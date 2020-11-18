import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *
import argparse
import json
import tqdm
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
import torch.nn as nn
import torch
from torch.optim import Adam, SGD
from sklearn.metrics import roc_auc_score, accuracy_score
from Predictor import Predictor
from torch.utils.data import DataLoader, TensorDataset, Dataset
from sklearn.metrics import plot_precision_recall_curve
from TransArch import TransformerModel


from RNN import parser, acc_thr, base_lr, EncountersDataset, MatchDataset, get_data_loaders, init_best_scores_dict, get_lr_by_epoch, \
    evaluate, train_one_epoch

# def train_one_epoch(encounters_dataset_loader, model, opt, step_mode='each'):
#     model.train()
#
#     ### New VERSION FROM HERE
#     for data, target, team_name, match in encounters_dataset_loader:
#         assert data.shape[0] == 1
#         assert target.shape[0] == 1
#         # print(data.shape)
#         # print(target.shape)
#         data = data.squeeze()
#         target = target.squeeze()
#
#         opt.zero_grad()
#         # predictions = model(data, target).squeeze()
#         predictions = model(data[:,:,:]).squeeze()
#
#         mask = target != -1
#         loss = criterion(predictions[mask], target[mask])
#
#         # predictions_masked = predictions[mask]
#         # target_masked = target[mask]
#         # target_masked_tensor = torch.zeros(target_masked.size(0), 2)
#         # target_masked_tensor[target_masked == 0, 0] = 1
#         # target_masked_tensor[target_masked == 1, 1] = 1
#         # loss = criterion(predictions[mask], target_masked_tensor)
#
#         loss.backward()
#         opt.step()


if __name__ == '__main__':
    args = parser.parse_args()  # TODO: uncomment

    # Fixed hyperparams
    input_size = len(columns_order)

    # Scores
    best_scores = defaultdict(dict)

    groups = itertools.product(args.hidden_size_list, args.lstm_layers_list,
                               args.linear_layers_list)  # , args.step_mode_list)

    ### New data loading
    datasets = ['train', 'test']
    if args.add_val:
        datasets = ['train', 'val', 'test']

    data_loaders_dict = get_data_loaders(datasets, args)

    # Experiments
    for group in groups:
        print(group)
        # hidden_size, n_lstm_layers, linear_layers, step_mode = group
        hidden_size, n_lstm_layers, linear_layers = group
        best_scores4exp = init_best_scores_dict(scorers_dict, datasets)
        n_epochs_with_no_improvement = 0

        # Model
        # model = nn.Transformer(d_model=input_size, nhead=1)
        model = TransformerModel(input_size, 8, 512, 1, dropout=0.5)
        print(f'model={model}')

        opt = Adam(model.parameters(), lr=base_lr)
        # opt = SGD(model.parameters(), lr=1e-5)

        for epoch in range(args.epochs):
            best_epoch = False
            lr = get_lr_by_epoch(epoch, base_lr=base_lr, warmup=args.warmup)
            for param_group in opt.param_groups:
                param_group['lr'] = lr
            train_one_epoch(data_loaders_dict['train'], model, opt)
            # data_loaders_list = [encounters_data_loader_train, encounters_data_loader_val, encounters_data_loader_test]
            scores4epoch_dict = evaluate(data_loaders_dict, model, scorers_dict, args, datasets, alg_name='Transformer')

            early_stopping_dataset = 'val' if args.add_val else 'test'
            if (best_scores4exp['auc'][early_stopping_dataset] is None) or (
                    best_scores4exp['auc'][early_stopping_dataset] < scores4epoch_dict['auc'][early_stopping_dataset]):
                best_epoch = True
                n_epochs_with_no_improvement = 0
            else:
                n_epochs_with_no_improvement += 1

            if n_epochs_with_no_improvement >= args.patience:
                print(f'Early stopping on epoch {epoch}')
                break

            if best_epoch:  # Update scores
                print(f'Epoch {epoch} is currently the best, scores:')

                for scorer_name in scorers_dict:
                    for dataset in datasets:
                        if dataset in scores4epoch_dict[scorer_name]:
                            current_score = np.mean(scores4epoch_dict[scorer_name][dataset])
                            best_scores4exp[scorer_name][dataset] = current_score

                best_scores4exp_rounded = best_scores4exp.copy()
                for scorer_name in scorers_dict:
                    for dataset in datasets:
                        if (dataset in best_scores4exp_rounded[scorer_name]) and (
                                best_scores4exp_rounded[scorer_name][dataset] is not None):
                            best_scores4exp_rounded[scorer_name][dataset] = round(
                                best_scores4exp_rounded[scorer_name][dataset], 3)

                print(dict(best_scores4exp))

        group_key = ','.join([str(x) for x in group])
        best_scores[group_key] = best_scores4exp

    with open(os.path.join(args.output_path, f'transformer_results_{args.output_suffix}.json'), 'w') as f:
        json.dump(best_scores, f)











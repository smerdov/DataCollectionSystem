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


parser = argparse.ArgumentParser()
parser.add_argument('--epochs', default=100, type=int)
parser.add_argument('--hidden-size-list', nargs='+', default=(8,), type=int)
parser.add_argument('--lstm-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--linear-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--output-suffix', default='last', type=str, help='Suffix to append to results')
parser.add_argument('--output-path', type=str, help='Output directory')
parser.add_argument('--data-suffix', default='last', type=str, help='Suffix for input data')
parser.add_argument('--patience', default=3, type=int, help='Patience for early stopping')
parser.add_argument('--step-mode-list', nargs='+', default=('each',), type=str, help='Step modes for training',
                    choices=['each', 'player', 'epoch'])

acc_thr = 0.5


def evaluate(data_dict, model, scorers_dict, datasets=('train', 'test')):
    # scores4epoch_dict = init_scores4epoch_dict(scorers_dict, modes)
    if hasattr(model, 'eval'):
        model.eval()

    scores = {}

    for dataset in datasets:
        data_dict_values = data_dict[dataset]
        keys = list(data_dict_values.keys())
        np.random.shuffle(keys)

        scores4dataset = {}

        for key in keys:  # key --- unique player
            scores4key = {
                'loss': [],
            }
            key = tuple(key)
            data_target = data_dict_values[key]
            data, target = data_target['data'], data_target['target']
            target = target.float()

            if hasattr(model, 'reset_hidden'):
                model.reset_hidden()

            predicts = []
            targets_with_encounter = []

            # for n_row in range(len(data)):
            for data_row, target_row in zip(data, target):
                if hasattr(model, 'predict_proba'):
                    predict = model.predict_proba(data_row.reshape(1, -1))[:, 1]
                    predict = torch.Tensor([predict])
                else:
                    predict = model(data_row.reshape(1, 1, -1))


                if target_row == -1:  # No encounter
                    # with torch.no_grad():
                    continue

                loss = criterion(predict, target_row.reshape(-1, 1))
                loss = loss.detach()
                # losses4epoch[dataset].append(loss.item())
                scores4key['loss'].append(loss.item())
                predicts.append(predict.item())
                targets_with_encounter.append(int(target_row))

            for scorer_name, scorer in scorers_dict.items():
                if scorer_name == 'loss':
                    # scores4epoch_dict[scorer_name][dataset] = np.mean(scores4epoch_dict[scorer_name][dataset])
                    scores4key[scorer_name] = np.mean(scores4key[scorer_name])
                    continue

                if len(np.unique(targets_with_encounter)) > 1:
                    if scorer_name == 'auc':
                        score = scorer(targets_with_encounter, predicts)
                    elif scorer_name == 'acc':
                        predicts_binary = (np.array(predicts) > acc_thr) * 1
                        score = scorer(targets_with_encounter, predicts_binary)
                    else:
                        raise ValueError(f'Unknown scorer name {scorer_name}')

                    # scores4epoch_dict[scorer_name][dataset] = score
                    scores4key[scorer_name] = score
                # else:
                #     print(f'Not enough data for key {key}')
                #     # raise ValueError(f'Not enough data for key {key}')

            scores4dataset[key] = scores4key

        # print(f'scores4dataset={scores4dataset}')
        scores[dataset]= {scorer_name: np.mean([scores4dataset[key][scorer_name] for key in keys if scorer_name in scores4dataset[key]])
            for scorer_name in scorers_dict}

    scores_reverted = defaultdict(dict)
    for scorer_name in scorers_dict:
        for dataset in datasets:
            scores_reverted[scorer_name][dataset] = scores[dataset][scorer_name]

    return scores_reverted
    # return scores4epoch_dict

def train_one_epoch(data_dict, model, opt, step_mode='each'):
    model.train()
    if step_mode == 'epoch':
        epoch_loss = 0
    opt.zero_grad()

    data_dict_values = data_dict['train']

    keys = list(data_dict_values.keys())
    np.random.shuffle(keys)

    for key in keys:  # key --- unique player
        if step_mode == 'player':
            player_loss = 0

        key = tuple(key)
        data_target = data_dict_values[key]
        data, target = data_target['data'], data_target['target']
        target = target.float()

        model.reset_hidden()

        for data_row, target_row in zip(data, target):
            predict = model(data_row.reshape(1, 1, -1))
            if target_row == -1:  # No encounter
                continue

            loss = criterion(predict, target_row.reshape(-1, 1))
            if step_mode == 'epoch':
                epoch_loss += loss
            elif step_mode == 'player':
                player_loss += loss
            elif step_mode == 'each':
                loss.backward()
                opt.step()

        if step_mode == 'player':
            player_loss.backward()
            opt.step()

    if step_mode == 'epoch':
        epoch_loss.backward()
        opt.step()

def init_best_scores_dict(scorers_dict, datasets=('train', 'test')):
    best_scores = defaultdict(dict)
    for scorer_name in scorers_dict:
        for dataset in datasets:
            best_scores[scorer_name][dataset] = None

    return best_scores

def init_scores4epoch_dict(scorers_dict, datasets=('train', 'test')):
    best_scores = {}
    for scorer_name in scorers_dict:
        best_scores4scorer = defaultdict(list)
        best_scores[scorer_name] = best_scores4scorer
        # for dataset in datasets:
        #     best_scores4scorer[scorer_name][dataset] = None

    return best_scores


if __name__ == '__main__':
    # args = parser.parse_args([])  # TODO: comment
    args = parser.parse_args()  # TODO: uncomment

    # Fixed hyperparams
    input_size = len(columns_order)

    # Scorers
    best_scores = defaultdict(dict)

    groups = itertools.product(args.hidden_size_list, args.lstm_layers_list, args.linear_layers_list, args.step_mode_list)

    # Data
    path2_data_dict = os.path.join(data_folder, f'data_dict_{args.data_suffix}')
    print(f'Loading data from {path2_data_dict} ...')
    data_dict = joblib.load(path2_data_dict)
    datasets = list(data_dict.keys())

    # Experiments
    for group in groups:
        print(group)
        hidden_size, n_lstm_layers, linear_layers, step_mode = group
        best_scores4exp = init_best_scores_dict(scorers_dict, datasets)
        n_epochs_with_no_improvement = 0

        # Model
        model = Predictor(hidden_size=hidden_size, n_lstm_layers=n_lstm_layers, n_linear_layers=linear_layers)
        print(f'model={model}')
        opt = Adam(model.parameters())
        # opt = SGD(model.parameters(), lr=1e-5)

        for epoch in range(args.epochs):
            best_epoch = False
            train_one_epoch(data_dict, model, opt, step_mode=step_mode)
            # print(list(model.parameters())[0])
            # print(list(model.parameters())[-1])
            scores4epoch_dict = evaluate(data_dict, model, scorers_dict)

            if (best_scores4exp['auc']['test'] is None) or (best_scores4exp['auc']['test'] < scores4epoch_dict['auc']['test']):
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
                        current_score = np.mean(scores4epoch_dict[scorer_name][dataset])
                        best_scores4exp[scorer_name][dataset] = current_score

                best_scores4exp_rounded = best_scores4exp.copy()
                for scorer_name in scorers_dict:
                    for dataset in datasets:
                        best_scores4exp_rounded[scorer_name][dataset] = round(best_scores4exp_rounded[scorer_name][dataset], 2)

                print(dict(best_scores4exp))


        group_key = ','.join([str(x) for x in group])
        best_scores[group_key] = best_scores4exp


    # with open(os.path.join(data_folder, f'nn_results_{args.output_suffix}.json'), 'w') as f:
    with open(os.path.join(args.output_path, f'nn_results_{args.output_suffix}.json'), 'w') as f:
        json.dump(best_scores, f)







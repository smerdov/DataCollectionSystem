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


parser = argparse.ArgumentParser()
parser.add_argument('--epochs', default=100, type=int)
parser.add_argument('--hidden-size-list', nargs='+', default=(8,), type=int)
parser.add_argument('--lstm-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--linear-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--arch', default='gru', type=str)
parser.add_argument('--output-suffix', default='last', type=str, help='Suffix to append to results')
parser.add_argument('--output-path', default='../Data/', type=str, help='Output directory')
parser.add_argument('--data-suffix', default='last', type=str, help='Suffix for input data')
parser.add_argument('--path2datasets', default=None, type=str, help='Suffix for input data', required=True)
parser.add_argument('--patience', default=3, type=int, help='Patience for early stopping')
parser.add_argument('--warmup', default=0, type=int, help='Patience for early stopping')
parser.add_argument('--key-mode', default='all', type=str, help='Averaging type', choices=['player_team', 'player_team_match', 'match', 'all'])
parser.add_argument('--add-val', default=0, type=int, choices=[0, 1], help='Whether to add validation dataset')
parser.add_argument('--acc-thr', default=0.45, type=float, help='Threshold for classification')

acc_thr = 0.5
base_lr = 1e-3


class EncountersDataset(Dataset):

    def __init__(self, path2dataset):
        super().__init__()

        self.path2dataset = path2dataset
        self._parse_data()

    def _parse_data(self):
        matches = os.listdir(self.path2dataset)
        matches = [match for match in matches if match.startswith('match')]

        match_data_list = []
        match_target_list = []
        match_teams = []
        match_names = []

        for match in matches:
            data_list = []
            target_list = []
            for player_id in player_ids:
                path2player_folder = os.path.join(self.path2dataset, match, f'player_{player_id}')
                data = pd.read_csv(os.path.join(path2player_folder, 'data.csv'), header=None).values
                target = pd.read_csv(os.path.join(path2player_folder, 'target.csv'), header=None).values
                with open(os.path.join(path2player_folder, 'meta_info.json')) as f:
                    meta_info = json.load(f)

                data_list.append(data)
                target_list.append(target)

            match_data = torch.FloatTensor(np.array(data_list))
            match_target = torch.FloatTensor(np.array(target_list))

            match_data_list.append(match_data)
            match_target_list.append(match_target)
            match_teams.append(meta_info['team'])
            match_names.append(match)


        self.match_data_list = match_data_list
        self.match_target_list = match_target_list
        self.match_teams = match_teams
        self.match_names = match_names

    def __getitem__(self, item):
        return self.match_data_list[item], self.match_target_list[item], self.match_teams[item], self.match_names[item]

    def __len__(self):
        return len(self.match_data_list)

class MatchDataset(Dataset):

    def __init__(self, data, target, name=None):
        self.data = data
        self.target = target

        assert self.data.shape[0] == self.target.shape[0]
        assert self.data.shape[0] == 5
        assert self.data.shape[1] == self.target.shape[1]

        if name is None:
            name = 'no name'

        self.name = name

    def __len__(self):
        return self.data.shape[1]

    def __getitem__(self, item):
        return self.data[:, item, :], self.target[:, item, :]

    def __repr__(self):
        return f'{self.name}, data shape {self.data.shape}, target shape {self.target.shape}'


def get_lr_by_epoch(epoch, base_lr=0.001, warmup=1, decay=1):
    if epoch < warmup:
        return base_lr * (epoch + 1) / warmup * decay ** epoch
    else:
        return base_lr * decay ** epoch


def get_scores(predictions, targets, scorers_dict, acc_thr):
    scores = {}
    predictions = torch.Tensor(predictions)
    targets = torch.Tensor(targets)

    mask = targets != -1

    predictions_masked = predictions[mask]
    targets_masked = targets[mask]

    if len(np.unique(targets_masked)) == 1:
        print('Only one class is present')
        return None

    if mask.sum() == 0:
        print('There is no encounters')
        return None

    for scorer_name, scorer in scorers_dict.items():
        # pos_label = 0 if scorer_name.endswith('neg') else 1

        # if scorer_name == 'loss':
        if scorer_name == 'log_loss':
            # score = criterion(predictions_masked, targets_masked).item()
            score = scorer(targets_masked, predictions_masked)
        elif scorer_name in ['auc', 'ap', 'ap_neg']:
            if len(targets_masked.unique()) > 1:
                if scorer_name == 'auc':
                    score = scorer(targets_masked, predictions_masked)
                elif scorer_name.endswith('neg'):
                    score = scorer(1 - targets_masked, 1 - predictions_masked)
                else:
                    score = scorer(targets_masked, predictions_masked)
                    # score = scorer(targets_masked, predictions_masked, pos_label=pos_label)
                    # if scorer_name != 'ap_neg':
                    #     score = scorer(targets_masked, predictions_masked)
                    # else:
                    #     score = scorer(1 - targets_masked, 1 - predictions_masked)
            else:
                continue
        elif scorer_name in ['acc', 'precision', 'recall', 'precision_neg', 'recall_neg']:
            predicts_binary = (np.array(predictions_masked) >= acc_thr) * 1
            # predicts_binary = (np.array(predictions_masked) >= acc_thr) * 1
            # predicts_binary = (np.array(predictions_masked) < acc_thr) * 1
            if (len(np.unique(predicts_binary)) < 2) and (scorer_name.startswith('recall') or scorer_name.startswith('precision')):
                continue

            if scorer_name == 'acc':
                score = scorer(targets_masked, predicts_binary)
            elif scorer_name.endswith('neg'):
                score = scorer(1 - targets_masked, 1 - predicts_binary)
            else:
                score = scorer(targets_masked, predicts_binary)
                # score = scorer(targets_masked, predicts_binary, pos_label=pos_label)
                # score = scorer(targets_masked, predicts_binary)
            # if scorer_name.endswith('neg'):
            #     score = scorer(1 - targets_masked, 1 - predicts_binary)
            # else:
            #     score = scorer(targets_masked, predicts_binary)
        else:
            raise ValueError(f'Unknown scorer name {scorer_name}')

        scores[scorer_name] = score

    return scores

def get_evaluation_key(player_id, team_name, match, mode='player_team'):
    if mode == 'player_team':
        return (player_id, team_name)
    elif mode == 'player_team_match':
        return (player_id, team_name, match)
    elif mode == 'match':
        return (match,)
    elif mode == 'all':
        return 'all'
    else:
        raise ValueError(f'Unknown mode {mode}')


def average_scores(predictions_dict, target_dict, scorers_dict, thrs_dict):
    assert set(predictions_dict.keys()) == set(target_dict.keys())

    scores4dataset = defaultdict(list)

    for key in predictions_dict.keys():
        # thr = thrs_dict.get(key, 0.5)
        thr = thrs_dict[key]
        scores = get_scores(predictions_dict[key], target_dict[key], scorers_dict, thr)
        if scores is not None:
            for score_name, score in scores.items():
                scores4dataset[score_name].append(score)

    for score_name in scores4dataset:
        scores4dataset[score_name] = np.mean(scores4dataset[score_name])

    return scores4dataset


def evaluate(data_loaders_dict, model, scorers_dict, args, datasets, alg_name='alg'):
    if hasattr(model, 'eval'):
        model.eval()

    scores = defaultdict(dict)
    thrs_dict = {}
    # predictions4datasets = {}

    with torch.no_grad():
        # for data_loader, dataset in zip(data_loaders, datasets):
        for dataset in datasets:
            data_loader = data_loaders_dict[dataset]
            predictions_list = []

            predictions_dict = defaultdict(list)
            target_dict = defaultdict(list)

            for data, target, team_name, match in data_loader:
                data = data.squeeze()
                target = target.squeeze()

                if hasattr(model, 'reset_hidden'):
                    model.reset_hidden()
                if hasattr(model, 'predict_proba'):  # or (alg_name == 'alg'):
                    predictions = model.predict_proba(data.reshape(-1, data.shape[2]).numpy())[:, 1]
                    predictions = predictions.reshape(5, -1)
                    predictions = torch.Tensor(predictions)
                    # raise NotImplementedError
                else:
                    predictions = model(data[:, :, :])
                    # if predictions.size(2) == 2:
                    #     predictions = predictions[:, :, 0]
                    predictions = predictions.squeeze()

                # mask = target != -1
                # targets_with_encounter = target[mask]
                # predicts = predictions[mask]
                #
                # loss = criterion(predicts, targets_with_encounter).item()

                for player_id in player_ids:
                    # scores4player_match = {}
                    predictions4player_team_match = predictions[player_id, :]
                    targets4player_team_match = target[player_id, :]

                    key = get_evaluation_key(player_id, team_name, match, mode=args.key_mode)
                    predictions_dict[key] = predictions_dict[key] + list(predictions4player_team_match.numpy())
                    target_dict[key] = target_dict[key] + list(targets4player_team_match.numpy())



                # predictions_list.append(predictions_list.numpy())
            # predictions4datasets[dataset] = predictions_list

            for key in predictions_dict.keys():
                if len(np.unique(target_dict[key])) == 1:  # One class instead of two
                    del target_dict[key]
                    del predictions_dict[key]

            # TODO: here I'm setting a thr for precision/recall
            if dataset == 'train':
                for key in predictions_dict.keys():
                    predictions = np.array(predictions_dict[key])
                    targets = np.array(target_dict[key])

                    # print(targets)
                    # print(predictions)

                    mask = targets != -1
                    # print(f'mask.sum() = {mask.sum()}')
                    predictions_masked = predictions[mask]
                    targets_masked = targets[mask]

                    # print(targets_masked)
                    # print(predictions_masked)

                    # precision, recall, thrs = precision_recall_curve(targets_masked, predictions_masked)
                    precision, recall, thrs = precision_recall_curve(1 - targets_masked, 1 - predictions_masked)
                    # precision, recall, thrs = precision_recall_curve(targets_masked, predictions_masked, pos_label=1)

                    recall_needed = 0.4

                    # print(precision)
                    # print(recall)
                    # print(thrs)

                    # index_thr = np.min(np.nonzero(recall < recall_needed)[0]) - 1
                    index_thr = np.max(np.nonzero(recall > recall_needed)[0])
                    # print(f'len(thrs) = {len(thrs)}')
                    # print(index_thr)
                    thr4key = 1 - thrs[index_thr]
                    thrs_dict[key] = thr4key
            else:
                for key in predictions_dict.keys():
                    predictions = np.array(predictions_dict[key])
                    targets = np.array(target_dict[key])
                    mask = targets != -1
                    # print(f'mask.sum() = {mask.sum()}')
                    predictions_masked = predictions[mask]
                    targets_masked = targets[mask]

                    # precision, recall, thrs = precision_recall_curve(1 - targets_masked, 1 - predictions_masked)
                    # precision, recall, thrs = precision_recall_curve(targets_masked, 1 - predictions_masked, pos_label=0)
                    plot_pr_curve = False
                    if plot_pr_curve:
                        precision, recall, thrs = precision_recall_curve(1 - targets_masked, 1 - predictions_masked)
                        fig, ax = plt.subplots(figsize=(8, 4.5))
                        fontsize = 12
                        ax.step(recall, precision, c='darkred')
                        ax.set_xlabel('Recall', fontsize=fontsize)
                        ax.set_ylabel('Precision', fontsize=fontsize)
                        ax.set_title(alg_name, fontsize=fontsize+3)
                        axes_margin = 0.03
                        ax.set_xlim(-axes_margin, 1 + axes_margin)
                        ax.set_ylim(-axes_margin, 1 + axes_margin)
                        fig.tight_layout()
                        fig.savefig(pic_folder + 'precision_recall_' + alg_name + '_' +  str(key) + '.pdf')
                        plt.close()

                # print(thrs_dict)

            # if dataset == 'test':
            #     for key in predictions_dict:
            #         targets4key = np.array(target_dict[key])
            #         predictions4key = np.array(predictions_dict[key])
            #         mask = targets4key != -1
            #         targets_masked = targets4key[mask]
            #         predictions_masked = predictions4key[mask]
            #         print(targets_masked.mean())
            #         # thrs_dict[key] = 0.5
            #
            #         precision, recall, thrs = precision_recall_curve(1 - targets_masked, 1 - predictions_masked, pos_label=1)
            #         plt.step(recall, precision)
            #         plt.title('pos_label = 0')
            #         plt.show()
            #
            #         precision, recall, thrs = precision_recall_curve(targets_masked, predictions_masked, pos_label=1)
            #         plt.step(recall, precision)
            #         plt.title('pos_label = 1')
            #         plt.show()
            #
            #         # # mask_recall = recall[:-1] <= 1 - 0.1
            #         # mask_recall = recall[1:] <= 1 - 0.3
            #         # # acc_thr = thrs[mask_recall].max()  # TODO: this should be calculated on train
            #         # acc_thr = thrs[mask_recall].min()  # TODO: this should be calculated on train
            #         # # print(acc_thr)
            #         # thrs_dict[key] = acc_thr
            #
            #         # # #### TMP BLOCK
            #         # predictions_binary = (predictions_masked < acc_thr) * 1
            #         # tmp_0 = recall_score(targets_masked, predictions_binary, pos_label=0)
            #         # tmp_1 = recall_score(targets_masked, predictions_binary, pos_label=1)
            #         # print(1)
            #         # # # tmp = get_scores(predictions4key, targets4key, scorers_dict, acc_thr)
            #         # # #### TMP BLOCK

            # print(thrs_dict)
            scores4dataset = average_scores(predictions_dict, target_dict, scorers_dict, thrs_dict)
            for score_name in scores4dataset:
                scores[score_name][dataset] = scores4dataset[score_name]

    # return scores, predictions4datasets
    return scores

def train_one_epoch(encounters_dataset_loader, model, opt, step_mode='each', ablation_index=None):
    model.train()

    ### New VERSION FROM HERE
    for data, target, team_name, match in encounters_dataset_loader:
        assert data.shape[0] == 1
        assert target.shape[0] == 1
        data = data.squeeze()
        target = target.squeeze()

        opt.zero_grad()
        predictions = model(data).squeeze()

        mask = target != -1
        loss = criterion(predictions[mask], target[mask])

        # predictions_masked = predictions[mask]
        # target_masked = target[mask]
        # target_masked_tensor = torch.zeros(target_masked.size(0), 2)
        # target_masked_tensor[target_masked == 0, 0] = 1
        # target_masked_tensor[target_masked == 1, 1] = 1
        # loss = criterion(predictions[mask], target_masked_tensor)

        loss.backward()
        opt.step()


def init_best_scores_dict(scorers_dict, datasets):
    best_scores = defaultdict(dict)
    for scorer_name in scorers_dict:
        for dataset in datasets:
            best_scores[scorer_name][dataset] = None

    return best_scores

def get_data_loaders(datasets, args, batch_size=1):
    path2dataset_dict = {}

    for dataset in datasets:
        path2dataset_dict[dataset] = os.path.normpath(os.path.join(os.getcwd(), args.path2datasets, dataset))

    data_loaders_dict = {dataset: DataLoader(EncountersDataset(path2dataset_dict[dataset]), batch_size=batch_size, shuffle=True)
                         for dataset in datasets}

    return data_loaders_dict

if __name__ == '__main__':
    # args = parser.parse_args([])  # TODO: comment
    args = parser.parse_args()  # TODO: uncomment

    # Fixed hyperparams
    input_size = len(columns_order)

    # Scores
    best_scores = defaultdict(dict)

    groups = itertools.product(args.hidden_size_list, args.lstm_layers_list, args.linear_layers_list)#, args.step_mode_list)

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
        model = Predictor(hidden_size=hidden_size, n_lstm_layers=n_lstm_layers, n_linear_layers=linear_layers, last_sigmoid=True, model=args.arch)
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
            scores4epoch_dict = evaluate(data_loaders_dict, model, scorers_dict, args, datasets, alg_name='GRU')

            early_stopping_dataset = 'val' if args.add_val else 'test'
            if (best_scores4exp['auc'][early_stopping_dataset] is None) or (best_scores4exp['auc'][early_stopping_dataset] < scores4epoch_dict['auc'][early_stopping_dataset]):
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
                        if (dataset in best_scores4exp_rounded[scorer_name]) and (best_scores4exp_rounded[scorer_name][dataset] is not None):
                            best_scores4exp_rounded[scorer_name][dataset] = round(best_scores4exp_rounded[scorer_name][dataset], 3)

                print(dict(best_scores4exp))


        group_key = ','.join([str(x) for x in group])
        best_scores[group_key] = best_scores4exp


    with open(os.path.join(args.output_path, f'nn_results_{args.output_suffix}.json'), 'w') as f:
        json.dump(best_scores, f)







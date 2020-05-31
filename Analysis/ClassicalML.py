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
from RNN import evaluate, get_data_loaders
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score, accuracy_score
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

parser = argparse.ArgumentParser()
parser.add_argument('--data-suffix', default='last', type=str, help='Suffix for input data')
parser.add_argument('--output-suffix', default='last', type=str, help='Suffix to append to results')
parser.add_argument('--output-path', default='../Data/', type=str, help='Output directory')
parser.add_argument('--path2datasets', default=None, type=str, help='Suffix for input data', required=True)
parser.add_argument('--key-mode', default='all', type=str, help='Patience for early stopping', choices=['player_team', 'player_team_match', 'match', 'all'])
parser.add_argument('--acc-thr', default=0.45, type=float, help='Threshold for classification')


if __name__ == '__main__':
    args = parser.parse_args()
    # args = parser.parse_args('--path2datasets ../Dataset/encounters_dataset'.split())

    datasets = ['train', 'test']
    data_loaders_dict = get_data_loaders(datasets, args, batch_size=1)

    prepared_data = defaultdict(dict)

    for dataset in datasets:
        data_all = []
        target_all = []

        for data, target, _, _ in data_loaders_dict[dataset]:
            data_all.append(data.reshape(-1, data.shape[3]))
            target_all.append(target.reshape(-1, 1))

        data_all = torch.cat(data_all)
        target_all = torch.cat(target_all)

        mask = target_all[:, 0] != -1
        prepared_data[dataset]['data'] = data_all[mask, :].numpy()
        prepared_data[dataset]['target'] = target_all[mask, :].numpy()

    # # path2_data_dict = os.path.join(data_folder, f'data_dict_{args.data_suffix}')
    # # print(f'Loading data from {path2_data_dict} ...')
    # # data_dict = joblib.load(path2_data_dict)
    #
    # x_train_all = torch.cat([value['data'] for key, value in data_dict['train'].items()])
    # y_train_all = torch.cat([value['target'] for key, value in data_dict['train'].items()])
    # x_test_all = torch.cat([value['data'] for key, value in data_dict['test'].items()])
    # y_test_all = torch.cat([value['target'] for key, value in data_dict['test'].items()])
    #
    # mask_train = y_train_all != -1
    # x_train, y_train = x_train_all[mask_train, :], y_train_all[mask_train]
    # mask_test = y_test_all != -1
    # x_test, y_test = x_test_all[mask_test, :], y_test_all[mask_test]

    alg_dict = {
        'lr': LogisticRegression(),
        'svm': SVC(probability=True),
        'knn_96': KNeighborsClassifier(n_neighbors=96),
        # 'knn_64': KNeighborsClassifier(n_neighbors=64),
        # 'rf_16': RandomForestClassifier(n_estimators=16),
        'rf_24': RandomForestClassifier(n_estimators=32, max_depth=5),
    }

    # # Comment from here
    # lr = LogisticRegression()
    # svm = SVC(probability=True)
    # knn = KNeighborsClassifier(n_neighbors=64)
    # rf = RandomForestClassifier(n_estimators=10)
    #
    # alg_list = [lr, svm, knn, rf]
    # # Comment to here
    results = {}


    # for alg in alg_list:
    for alg_name, alg in alg_dict.items():
        alg.fit(prepared_data['train']['data'], prepared_data['train']['target'])
        # alg_name = alg.__class__.__name__  # Comment

        alg_score = evaluate(data_loaders_dict, alg, scorers_dict, args, datasets)
        results[alg_name] = alg_score


    # with open(os.path.join(data_folder, f'cml_results_{args.output_suffix}.json'), 'w') as f:
    with open(os.path.join(args.output_path, f'cml_results_{args.output_suffix}.json'), 'w') as f:
        json.dump(results, f)


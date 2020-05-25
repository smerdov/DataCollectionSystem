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
from RNN import evaluate
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score, accuracy_score
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

parser = argparse.ArgumentParser()
parser.add_argument('--data-suffix', default='last', type=str, help='Suffix for input data')
parser.add_argument('--output-suffix', default='last', type=str, help='Suffix to append to results')
parser.add_argument('--output-path', type=str, help='Output directory')

if __name__ == '__main__':
    args = parser.parse_args()

    path2_data_dict = os.path.join(data_folder, f'data_dict_{args.data_suffix}')
    print(f'Loading data from {path2_data_dict} ...')
    data_dict = joblib.load(path2_data_dict)


    x_train_all = torch.cat([value['data'] for key, value in data_dict['train'].items()])
    y_train_all = torch.cat([value['target'] for key, value in data_dict['train'].items()])
    x_test_all = torch.cat([value['data'] for key, value in data_dict['test'].items()])
    y_test_all = torch.cat([value['target'] for key, value in data_dict['test'].items()])

    mask_train = y_train_all != -1
    x_train, y_train = x_train_all[mask_train, :], y_train_all[mask_train]
    mask_test = y_test_all != -1
    x_test, y_test = x_test_all[mask_test, :], y_test_all[mask_test]

    lr = LogisticRegression()
    svm = SVC(probability=True)
    knn = KNeighborsClassifier(n_neighbors=64)
    rf = RandomForestClassifier(n_estimators=10)

    alg_list = [lr, svm, knn, rf]
    results = {}

    for alg in alg_list:
        alg.fit(x_train, y_train)
        alg_name = alg.__class__.__name__

        alg_score = evaluate(data_dict, alg, scorers_dict)
        results[alg_name] = alg_score


    # with open(os.path.join(data_folder, f'cml_results_{args.output_suffix}.json'), 'w') as f:
    with open(os.path.join(args.output_path, f'cml_results_{args.output_suffix}.json'), 'w') as f:
        json.dump(results, f)


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


epochs = 100
# input_size = data_dict['train'][(0, 'amateurs', 'match_17')]['data'].shape[1]
input_size = 33

class Predictor(nn.Module):

    def __init__(self, hidden_size=16, lstm_layers=2, batch_size=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=lstm_layers)
        self.linear_0 = nn.Linear(hidden_size, 1)
        self.batch_size = batch_size
        self.hidden_size = hidden_size
        self.lstm_layers = lstm_layers


    def forward(self, x):
        # x, (self.hidden, self.cell) = self.lstm(x, (self.hidden, self.cell))
        lstm_output, (self.hidden, self.cell) = self.lstm(x, (self.hidden, self.cell))
        self.hidden = self.hidden.detach()
        self.hidden = self.cell.detach()
        # output = self.linear_0(self.hidden)
        output = self.linear_0(lstm_output.detach())
        output = torch.sigmoid(output)

        return output

    def reset_hidden(self):
        self.hidden = torch.zeros((self.lstm_layers, self.batch_size, self.hidden_size))
        self.cell = torch.zeros((self.lstm_layers, self.batch_size, self.hidden_size))

criterion = nn.BCELoss()
scorer = roc_auc_score
acc_scorer = accuracy_score

# resampling_list = [5, 15, 30, 60, 180]
# hidden_size_list = [4, 16, 64]
# lstm_layers_list = [1, 2, 3]

# resampling_list = [5, 10, 20]
resampling_list = [5, 10]
hidden_size_list = [32, 64]
lstm_layers_list = [1]

best_scores = defaultdict(dict)

for (resampling, hidden_size, lstm_layers) in itertools.product(resampling_list, hidden_size_list, lstm_layers_list):
    best_losses4exp = {
        'train': 100,
        'test': 100,
    }
    best_scores4exp = {
        'train': 0,
        'test': 0,
    }
    best_acc4exp = {
        'train': 0,
        'test': 0,
    }

    os.system(f'python -Wonce TensorsCreation.py --resample-string {resampling}s')
    data_dict = joblib.load(os.path.join(data_folder, 'data_dict'))

    print(f'resampling={resampling}, hidden_size={hidden_size}, lstm_layers={lstm_layers}')
    model = Predictor(hidden_size=hidden_size, lstm_layers=lstm_layers)
    opt = Adam(model.parameters())
    # opt = SGD(model.parameters(), lr=1e-5)
    for epoch in range(epochs):
        losses4epoch = defaultdict(list)
        scores4epoch = defaultdict(list)
        acc4epoch = defaultdict(list)
        for mode in ['train', 'test']:
            data_dict_values = data_dict[mode]

            keys = list(data_dict_values.keys())
            np.random.shuffle(keys)

            # for key in tqdm.tqdm(keys):
            for key in keys:  # key --- unique playe
                predicts = []
                targets_filtered = []
                key = tuple(key)
                data_target = data_dict_values[key]
                model.reset_hidden()
                data, target = data_target['data'], data_target['target']
                target = target.float()

                # for n_row in range(len(data)):
                for data_row, target_row in zip(data, target):
                    predict = model(data_row.reshape(1, 1, -1))
                    if target_row == -1:
                        # with torch.no_grad():
                        continue
                    # else:
                    #     predict = model(data_row.reshape(1, 1, -1))

                    # loss = criterion(predict, target_row.reshape(-1, 1))
                    # print(predict, target_row)
                    loss = criterion(predict, target_row.reshape(-1, 1))
                    if mode == 'train':
                        loss.backward()
                        # loss.backward(retain_graph=True)
                        opt.step()
                        opt.zero_grad()

                    losses4epoch[mode].append(loss.item())
                    predicts.append(predict.item())
                    targets_filtered.append(int(target_row))

                if len(np.unique(targets_filtered)) > 1:
                    scores4epoch[mode].append(scorer(targets_filtered, predicts))

                if len(np.unique(targets_filtered)) > 1:
                    acc4epoch[mode].append(acc_scorer(targets_filtered, 1 * (np.array(predicts) > 0.5)))

        # for mode in ['train', 'test']:
        #     print(f'Mean loss on {mode} is {round(np.mean(losses4epoch[mode]), 3)}')

        for mode in ['train', 'test']:
            current_loss = np.mean(losses4epoch[mode])
            if current_loss < best_losses4exp[mode]:
                best_losses4exp[mode] = current_loss

            current_score = np.mean(scores4epoch[mode])
            if current_score > best_scores4exp[mode]:
                best_scores4exp[mode] = current_score

            current_acc = np.mean(acc4epoch[mode])
            if current_acc > best_acc4exp[mode]:
                best_acc4exp[mode] = current_acc

    best_scores[','.join([str(resampling), str(hidden_size), str(lstm_layers)])]['loss'] = best_losses4exp
    best_scores[','.join([str(resampling), str(hidden_size), str(lstm_layers)])]['score'] = best_scores4exp
    best_scores[','.join([str(resampling), str(hidden_size), str(lstm_layers)])]['acc'] = best_acc4exp
    print(best_scores[','.join([str(resampling), str(hidden_size), str(lstm_layers)])])

with open(os.path.join(data_folder, 'results_last_5.json'), 'w') as f:
    json.dump(best_scores, f)







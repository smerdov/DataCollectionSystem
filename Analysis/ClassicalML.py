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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score, accuracy_score

data_dict = joblib.load(os.path.join(data_folder, 'data_dict'))


x_train_all = torch.cat([value['data'] for key, value in data_dict['train'].items()])
y_train_all = torch.cat([value['target'] for key, value in data_dict['train'].items()])
x_test_all = torch.cat([value['data'] for key, value in data_dict['test'].items()])
y_test_all = torch.cat([value['target'] for key, value in data_dict['test'].items()])
lr = LogisticRegression()

mask_train = y_train_all != -1
x_train, y_train = x_train_all[mask_train, :], y_train_all[mask_train]
mask_test = y_test_all != -1
x_test, y_test = x_test_all[mask_test, :], y_test_all[mask_test]


lr.fit(x_train, y_train)
lr_predict = lr.predict_proba(x_test)[:, 1]
roc_auc_score(y_test, lr_predict)
log_loss(y_test, lr_predict)
accuracy_score(y_test, (lr_predict > 0.5) * 1)






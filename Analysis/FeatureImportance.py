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

suffix = 'lr_coef_new_1'
lr_coef = joblib.load(data_folder + suffix)
suffix2fig = suffix.split('_')[-1]
lr_coef = lr_coef.ravel()
features = columns_order

lr_coef = pd.Series(lr_coef, index=features)
# lr_coef['mouse_pressed'] = lr_coef['mouse_pressed'] + 0.1
lr_coef = lr_coef.sort_values()
lr_coef_part_1 = lr_coef.iloc[:30]
lr_coef_part_2 = lr_coef.iloc[-25:]
lr_coef = pd.concat([lr_coef_part_1, lr_coef_part_2])

from matplotlib.patches import Rectangle, Circle, Ellipse
from collections import OrderedDict

colors = OrderedDict({
    'EEG': 'cornflowerblue',
    'IMU': 'goldenrod',
    'Input': 'lightseagreen',  # 'teal',
    # 'Input': 'darkcyan', # 'teal',
    # 'Environment': 'palevioletred',
    'Environment': 'palevioletred',
    # 'Phys': 'darkred',
    'EMG': 'plum',
    'HR': 'darkgreen',
    'Eyetracker': 'indigo',
    'Thermal': 'darkorange',
    'GSR': 'darkred',
    'spo2': 'forestgreen',
})

margin = 0.05
fontsize = 16
vspace = 3
width = 0.8
color = 'darkgreen'
plt.close()
fig, ax = plt.subplots(figsize=(16, 14))
xlim_min = lr_coef_part_1.min() - margin
xlim_max = lr_coef_part_2.max() + margin
ax.set_xlim(xlim_min, xlim_max)
ax.set_ylim(-1, len(lr_coef_part_1) + len(lr_coef_part_2) + vspace + 1)
n_row = 0

ticklabels = list(lr_coef_part_1.index) + list(lr_coef_part_2.index)
indexes_part_1_start = 0
indexes_part_1_end = len(lr_coef_part_1)
indexes_part_2_start = len(lr_coef_part_1) + vspace
indexes_part_2_end = len(lr_coef_part_1) + vspace + len(lr_coef_part_2)

tick_indexes = list(0.5 + np.arange(indexes_part_1_start, indexes_part_1_end)) + list(
    0.5 + np.arange(indexes_part_2_start, indexes_part_2_end))


def process_coef(coef, feature_name, ax, n_row):
    print(coef, feature_name)
    group = feature2group(feature_name, groups)
    color = colors[group]
    if coef < 0:
        rect = Rectangle((coef, n_row + 0.5 * (1 - width)), -coef, width, color=color)
        ax.hlines(n_row + 0.5, xmin=xlim_min, xmax=coef, linestyle='--', color='grey', alpha=0.5)
    else:
        rect = Rectangle((0, n_row + 0.5 * (1 - width)), coef, width, color=color)
        ax.hlines(n_row + 0.5, xmin=xlim_min, xmax=0, linestyle='--', color='grey', alpha=0.5)
    ax.add_patch(rect)

    return n_row + 1


for (feature_name, coef) in lr_coef_part_1.items():
    assert coef < 0
    n_row = process_coef(coef, feature_name, ax, n_row)

for i in range(vspace):
    ax.plot((0), (n_row + i + 0.5), 'o', color='black', ms=3.4)
    ax.plot((xlim_min - margin * 2), (n_row + i + 0.5), 'o', color='black', clip_on=False, ms=3.4)

n_row += vspace
# circle = Ellipse((-1, n_row), width=0.8, height=1)
# ax.add_patch(circle)


for (feature_name, coef) in lr_coef_part_2.items():
    assert coef > 0
    n_row = process_coef(coef, feature_name, ax, n_row)

ax.set_yticks(tick_indexes)
ax.set_yticklabels(ticklabels, fontsize=fontsize)

for ticklabel in plt.gca().get_yticklabels():
    # group = groups[ticklabel._text]
    group = feature2group(ticklabel._text, groups)
    color = colors[group]
    ticklabel.set_color(color)

ax.tick_params(axis='x', labelsize=fontsize + 2)

rename_dict = {
    'Thermal': 'Facial skin temperature',
    'Phys': 'Physical indicators',
    'IMU': 'IMU activity',
    'Input': 'Input activity',
    'Eyetracker': 'Eye tracker',
    'HR': 'Heart rate',
    'spo2': 'SpO2',
}

for label, color in colors.items():
    label_renamed = rename_dict.get(label, label)
    ax.fill([], [], color=color, label=label_renamed)

ax.legend(loc='lower right', fontsize=24)

# # ax.barh(np.arange(len(lr_coef)), lr_coef, color='darkgreen')
# ax.set_yticks(np.arange(len(lr_coef)))
# ax.set_yticklabels(lr_coef.index, fontsize=fontsize)
ax.set_title('Feature Importances as Coefficients in Logistic Regression', fontsize=fontsize + 8)
ax.set_xlabel('Coefficient', fontsize=fontsize + 4)
# for ticklabel in plt.gca().get_yticklabels():
#     # group = groups[ticklabel._text]
#     group = feature2group(ticklabel._text, groups)
#     color = colors[group]
#     ticklabel.set_color(color)
fig.tight_layout()
fig.savefig(pic_folder + f'feature_importance_custom_{suffix2fig}.pdf')

#
# fontsize = 16
# plt.close()
# fig, ax = plt.subplots(figsize=(16, 13))
# ax.barh(np.arange(len(lr_coef)), lr_coef, color='darkgreen')
# ax.set_yticks(np.arange(len(lr_coef)))
# ax.set_yticklabels(lr_coef.index, fontsize=fontsize)
# ax.set_title('Feature Importances as Coefficients in Logistic Regression', fontsize=fontsize+6)
# ax.set_xlabel('Coefficient', fontsize=fontsize+3)
# for ticklabel in plt.gca().get_yticklabels():
#     # group = groups[ticklabel._text]
#     group = feature2group(ticklabel._text, groups)
#     color = colors[group]
#     ticklabel.set_color(color)
# fig.tight_layout()
# fig.savefig(pic_folder + 'feature_importance_6.pdf')
#

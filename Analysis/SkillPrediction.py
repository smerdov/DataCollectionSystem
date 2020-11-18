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
import torch
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import scipy.stats
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score, f1_score
from sklearn.decomposition import PCA

matches_dict = joblib.load(data_folder + 'matches_dict')
meta_info_dict = joblib.load(data_folder + 'meta_info_dict')
series_list = joblib.load(data_folder + 'series_list')

df = pd.DataFrame(series_list)
columns = df.columns
columns = [column for column in columns if not column.startswith('quaternion')]
columns = [column for column in columns if not column.startswith('euler')]
columns = [column for column in columns if not column.startswith('gravity')]

columns_abs = [column for column in columns if (column.startswith('linaccel') or column.startswith('gyro'))]

df = df.loc[:, columns]
df.loc[:, columns_abs] = df.loc[:, columns_abs].abs()

# mask = (df['communication'] == 1) & (df['opponents'] == 0)
# mask = (df['opponents'] == 0)
# df = df.loc[mask, :]

target, communication, opponents, daynum = df['player_id_team'], df['communication'], df['opponents'], df['day_num']
df.drop(columns=['player_id_team', 'communication', 'opponents', 'day_num'], inplace=True)


df.fillna(df.median(), inplace=True)



ss = StandardScaler()
df = ss.fit_transform(df)

tsne = TSNE()
# pca = PCA(n_components=2)
df_ld = tsne.fit_transform(df)
# df_ld = pca.fit_transform(df)

colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

classes = target.unique()
amateurs_plotted = False
pros_plotted = False

plt.close()
fig_skill, ax_skill = plt.subplots(figsize=(9,6))
fig_player, ax_player = plt.subplots(figsize=(9,6))


for i, (player_team, color) in enumerate(zip(classes, colors)):
    mask = target == player_team
    player_team_str = player_team[1].capitalize() + f', player {player_team[0]}'
    color_num = 1 if player_team[1] == 'amateurs' else 0
    label = None
    if (not amateurs_plotted) and (player_team[1] == 'amateurs'):
        label = player_team[1].capitalize()
        amateurs_plotted = True

    if (not pros_plotted) and (player_team[1] == 'pros'):
        label = player_team[1].capitalize()
        pros_plotted = True

    # color_num = i
    # plt.scatter(df_ld[mask, 0], df_ld[mask, 1], c=color, label=player_team[1])
    ax_skill.scatter(df_ld[mask, 0], df_ld[mask, 1], c=colors[color_num], label=label)
    ax_player.scatter(df_ld[mask, 0], df_ld[mask, 1], c=colors[i], label=player_team_str)

ax_skill.legend(loc='upper left')
ax_player.legend(loc='upper left')
ax_skill.set_title('Sensor data representation in low-dimensional space')
ax_player.set_title('Sensor data representation in low-dimensional space')

fig_skill.show()
fig_player.show()

fig_skill.savefig(pic_folder + 'tsne_skill.pdf')
fig_player.savefig(pic_folder + 'tsne_reid.pdf')



team2id = {
    'amateurs': 0,
    'pros': 1,
}
targets_dict = {}
targets_dict['skill'] = target.apply(lambda x: team2id[x[1]]).values
# target_person = target.apply(lambda x: '_'.join([str(y) for y in x[::-1]])).values
targets_dict['person'] = target.apply(lambda x: x[0] + (0 if x[1] == 'amateurs' else 5)).values




mask_test = daynum.values == 2
y_train = {}
y_test = {}

x_train, x_test = df[mask_test, :], df[~mask_test, :]
y_train['skill'], y_test['skill'] = targets_dict['skill'][mask_test], targets_dict['skill'][~mask_test]
y_train['person'], y_test['person'] = targets_dict['person'][mask_test], targets_dict['person'][~mask_test]

metrics = {
    'accuracy': accuracy_score,
    'log_loss': log_loss,
    'AUC': roc_auc_score,
    # 'f1_score': f1_score,
}

from sklearn.naive_bayes import GaussianNB
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

algs_dict = {
    'lr': LogisticRegression(),
    # 'knn_0': KNeighborsClassifier(n_neighbors=2),
    # 'knn_1': KNeighborsClassifier(n_neighbors=4),
    # 'knn_2': KNeighborsClassifier(n_neighbors=8),
    'knn_3': KNeighborsClassifier(n_neighbors=16),
    # 'knn_4': KNeighborsClassifier(n_neighbors=32),
    'svm': SVC(probability=True),
    # 'rf_0': RandomForestClassifier(n_estimators=100, max_depth=2),
    'rf_1': RandomForestClassifier(n_estimators=100, max_depth=4),
    # 'rf_2': RandomForestClassifier(n_estimators=100, max_depth=8),
    # 'rf_3': RandomForestClassifier(n_estimators=100, max_depth=16),
    # 'rf_4': RandomForestClassifier(n_estimators=100, max_depth=32),
    'naive_bayes': GaussianNB(),
    'gaussian_process': GaussianProcessClassifier(),
    # 'QDA': QuadraticDiscriminantAnalysis(),
}

scores = defaultdict(lambda: defaultdict(dict))

for alg_name, alg in algs_dict.items():
    for target_type in y_train:
        alg.fit(x_train, y_train[target_type])
        predictions = alg.predict(x_test)
        predictions_proba = alg.predict_proba(x_test)
        if predictions_proba.shape[1] <= 2:
            predictions_proba = predictions_proba[:, 1]

        for metric_name, scorer in metrics.items():
            if metric_name in ['accuracy']:
                score = scorer(y_test[target_type], predictions)
            elif (metric_name in ['AUC']):
                score = scorer(y_test[target_type], predictions_proba, multi_class='ovr')
            else:
                score = scorer(y_test[target_type], predictions_proba)

            scores[target_type][alg_name][metric_name] = score

scores
pd.DataFrame(scores)











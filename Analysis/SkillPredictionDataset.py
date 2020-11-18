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

matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
output_dataset_folder = os.path.join(dataset_folder, 'encounters_dataset')
matches = [match for match in os.listdir(matches_processed_folder) if match.startswith('match')]
# time_step = f'{args.timestep}s'

data_sources2use = [
    'gsr',
    'emg',
    'heart_rate',
    'imu_left_hand',
    'imu_right_hand',
    'imu_chair_seat',
    'imu_chair_back',
    'imu_head',
    'keyboard',
    'mouse',
    'eye_tracker',
    'face_temperature',
    # 'eeg_band_power',
    # 'eeg_metrics',
    # 'environment',
]


def split_wrt_time(df, window_size=3, n_parts_max=5):
    timedelta = pd.Timedelta(minutes=window_size)
    stepsize = timedelta // df4player.index[1]
    # window = pd.Timedelta(minutes=window_size)
    n_parts = df.index.max() // timedelta
    # print(n_parts)
    n_parts = min(n_parts, n_parts_max)
    index_starts = [len(df) * i // n_parts for i in range(n_parts)]
    index_ends = [index + stepsize for index in index_starts]

    df_list = []

    for index_start, index_end in zip(index_starts, index_ends):
        df_list.append(df.iloc[index_start:index_end, :])

    return df_list


# GSR correlation
# Amateurs:
# Bots: 0.35
# Real Opponents: 0.42
# Pros:
# Bots: 0.30
# Real Opponents: 0.27

# GSR correlation
# Amateurs:
# No communication: 0.34
# Communication: 0.44
# Pros:
# No communication: 0.30
# Communication: 0.27


meta_info_dict = {}
matches_dict = defaultdict(dict)

series_list = []

# match = 'match_3'
for match in matches:
    path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
    with open(path2meta_info) as f:
        meta_info_json = json.load(f)
        meta_info_dict[match] = meta_info_json

    team = meta_info_json['team']
    match_duration = meta_info_json['match_duration']
    last_index = pd.Timedelta(seconds=match_duration)# .floor(args.time_step)
    # player_id = 0
    for player_id in player_ids:
        df4player = pd.DataFrame()
        path2encounters = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'encounters.json')

        with open(path2encounters) as f:
            encounters_json = json.load(f)


        player_id_team = (player_id, team)

        # df_encounters = pd.DataFrame.from_records(encounters_json).set_index('time').rename(columns={'outcome':'encounter_outcome'})

        # data_source = 'gsr'
        # data_source = 'keyboard'
        # data_source = 'heart_rate'
        for data_source in data_sources2use:
            if data_source == 'environment':
                path2data_source = os.path.join(matches_processed_folder, match, f'{data_source}.csv')
            else:
                path2data_source = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'{data_source}.csv')

            if not os.path.exists(path2data_source):
                # print(f'{path2data_source} doesn\'t exist')
                continue

            df4data_source = pd.read_csv(path2data_source, index_col='time')
            df4data_source.index = pd.TimedeltaIndex(df4data_source.index, unit='s')
            if data_source.startswith('imu'):
                imu_suffix = data_source.split('imu')[1]
                df4data_source.columns = [column + imu_suffix for column in df4data_source.columns]

                columns_abs = [column for column in df4data_source.columns if (column.startswith('linaccel') or column.startswith('gyro'))]
                df4data_source.loc[:, columns_abs] = df4data_source.loc[:, columns_abs].abs()

            df4player = df4player.join(df4data_source, how='outer')
            # print(data_source)
            # print(len(df4player))

        if last_index not in df4player.index:
            df4player.loc[last_index, :] = None

        df4player = df4player.interpolate('linear', limit_area='inside')
        df4player.fillna(df4player.median(), inplace=True)

        # df4player_resampled = df4player.resample(args.time_step).mean()
        df_parts_list = split_wrt_time(df4player)

        for df_part in df_parts_list:
            df4player_resampled = df_part.mean()
            df4player_resampled['player_id_team'] = player_id_team
            df4player_resampled['opponents'] = meta_info_json['real_opponents']
            df4player_resampled['communication'] = meta_info_json['communication']
            df4player_resampled['communication'] = meta_info_json['communication']
            df4player_resampled['day_num'] = meta_info_json['day_num']

            series_list.append(df4player_resampled)

        matches_dict[match][player_id_team] = df4player

joblib.dump(matches_dict, data_folder + 'matches_dict')
joblib.dump(meta_info_dict, data_folder + 'meta_info_dict')
joblib.dump(series_list, data_folder + 'series_list')
#
#
# ####### END OF DATASET CREATION PART
#
#
# df = pd.DataFrame(series_list)
# columns = df.columns
# columns = [column for column in columns if not column.startswith('quaternion')]
# columns = [column for column in columns if not column.startswith('euler')]
# columns = [column for column in columns if not column.startswith('gravity')]
#
# columns_abs = [column for column in columns if (column.startswith('linaccel') or column.startswith('gyro'))]
#
# df = df.loc[:, columns]
# df.loc[:, columns_abs] = df.loc[:, columns_abs].abs()
#
# # mask = (df['communication'] == 1) & (df['opponents'] == 0)
# # mask = (df['opponents'] == 0)
# # df = df.loc[mask, :]
#
# target, communication, opponents, daynum = df['player_id_team'], df['communication'], df['opponents'], df['day_num']
# df.drop(columns=['player_id_team', 'communication', 'opponents', 'day_num'], inplace=True)
#
#
# df.fillna(df.median(), inplace=True)
#
# from sklearn.decomposition import PCA
#
# ss = StandardScaler()
# df = ss.fit_transform(df)
#
# tsne = TSNE()
# pca = PCA(n_components=2)
# df_ld = tsne.fit_transform(df)
# # df_ld = pca.fit_transform(df)
#
# colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
#
# classes = target.unique()
# amateurs_plotted = False
# pros_plotted = False
#
# plt.close()
# fig_skill, ax_skill = plt.subplots(figsize=(9,6))
# fig_player, ax_player = plt.subplots(figsize=(9,6))
#
#
# for i, (player_team, color) in enumerate(zip(classes, colors)):
#     mask = target == player_team
#     player_team_str = player_team[1].capitalize() + f', player {player_team[0]}'
#     color_num = 1 if player_team[1] == 'amateurs' else 0
#     label = None
#     if (not amateurs_plotted) and (player_team[1] == 'amateurs'):
#         label = player_team[1].capitalize()
#         amateurs_plotted = True
#
#     if (not pros_plotted) and (player_team[1] == 'pros'):
#         label = player_team[1].capitalize()
#         pros_plotted = True
#
#     # color_num = i
#     # plt.scatter(df_ld[mask, 0], df_ld[mask, 1], c=color, label=player_team[1])
#     ax_skill.scatter(df_ld[mask, 0], df_ld[mask, 1], c=colors[color_num], label=label)
#     ax_player.scatter(df_ld[mask, 0], df_ld[mask, 1], c=colors[i], label=player_team_str)
#
# ax_skill.legend()
# ax_player.legend()
# ax_skill.set_title('Sensor data representation in low-dimensional space')
# ax_player.set_title('Sensor data representation in low-dimensional space')
#
# fig_skill.show()
# fig_player.show()
#
# fig_skill.savefig(pic_folder + 'fig_skill.pdf')
# fig_player.savefig(pic_folder + 'fig_player.pdf')
#
# #
# # # Correlations
# # corr_columns = ['gsr', 'heart_rate', 'emg_right_hand', 'pupil_diameter', 'mouse_pressed', 'mouse_movement', 'button_pressed', 'gaze_movement']
# # match_corr = {}
# # entries = []
# # # corr_column = 'gsr' #  'heart_rate'
# #
# # for match, match_dict in matches_dict.items():
# #
# #     meta_info = meta_info_dict[match]
# #     values4match = defaultdict(list)
# #     values4match_lens = defaultdict(list)
# #     entry = {
# #         'team': meta_info['team'],
# #         'communication': meta_info['communication'],
# #         'real_opponents': meta_info['real_opponents'],
# #     }
# #     # hr4match = []
# #     # hr_lens = []
# #     for corr_column in corr_columns:
# #         corr_columns_values = []
# #         corr_columns_lens = []
# #
# #         for player_team, player_id_team in match_dict.items():
# #             # player_id_team[]
# #             if corr_column in player_id_team:
# #                 corr_columns_values.append(player_id_team[corr_column].values)
# #                 corr_columns_lens.append(len(player_id_team[corr_column]))
# #
# #         len_mode = scipy.stats.mode(corr_columns_lens).mode
# #
# #         keys2del = []
# #         for key in range(len(corr_columns_values)):
# #             if len(corr_columns_values[key]) != len_mode:
# #                 keys2del.append(key)
# #
# #         for key in keys2del:
# #             del corr_columns_values[key]
# #
# #         corrs = np.corrcoef(corr_columns_values)
# #
# #         corrs = np.triu(corrs, 1).ravel()
# #         corrs = corrs[corrs > 0]
# #         corr_ = corrs.mean()
# #         # match_corr[match] = hr_corr
# #         entry[f'corr_{corr_column}'] = corr_
# #
# #     entries.append(entry)
# #
# # df_corr = pd.DataFrame(entries)
# # df_corr_mean = df_corr.groupby(['team', 'communication', 'real_opponents']).mean()
# # df_corr_mean.loc[('pros', 1, 0)] - df_corr_mean.loc[('pros', 0, 0)]
# #
# # df_corr_mean.loc[('amateurs', 1, 0)] - df_corr_mean.loc[('amateurs', 0, 0)]
# #
# #
# # df_corr.groupby('team').mean()
# # df_corr.groupby('communication').mean()
# # df_corr.groupby(['team', 'communication']).mean()
# # df_corr.groupby(['team', 'real_opponents']).mean()
# # df_corr.groupby(['communication', 'real_opponents']).mean()
# # df_corr.groupby('real_opponents').mean()
# #
# #
# #
# #
# # (match_dict[(4, 'amateurs')], match_dict[(3, 'amateurs')])
# #
# #
# # match_dict[(4, 'amateurs')]['heart_rate'].corr()
# #
# # np.corrcoef(match_dict[(1, 'amateurs')], match_dict[(4, 'amateurs')])
# #
# #
# #
# # # Player ReID
# # # Skill prediction
# # # Team cooperation
# #









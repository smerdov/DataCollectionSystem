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
from collections import OrderedDict


matches_dict = joblib.load(data_folder + 'matches_dict')
meta_info_dict = joblib.load(data_folder + 'meta_info_dict')
entries = []
corr_columns = [
    'gsr',
    'heart_rate',
    'emg_right_hand',
    'emg_left_hand',
    'pupil_diameter',
    'mouse_pressed',
    'mouse_movement',
    'button_pressed',
    'gaze_movement',
    'thermal_data',
    'linaccel_x_right_hand',
    'linaccel_y_right_hand',
    'linaccel_z_right_hand',
    'linaccel_x_chair_seat',
    'linaccel_y_chair_seat',
    'linaccel_z_chair_seat',
    'linaccel_x_chair_back',
    'linaccel_y_chair_back',
    'linaccel_z_chair_back',
    'gyro_x_chair_back',
    'gyro_y_chair_back',
    'gyro_z_chair_back',
    'gyro_x_chair_seat',
    'gyro_y_chair_seat',
    'gyro_z_chair_seat',
]

for match, match_dict in matches_dict.items():

    meta_info = meta_info_dict[match]
    values4match = defaultdict(list)
    values4match_lens = defaultdict(list)
    entry = {
        'team': meta_info['team'],
        'communication': meta_info['communication'],
        'real_opponents': meta_info['real_opponents'],
    }
    # hr4match = []
    # hr_lens = []
    for corr_column in corr_columns:
        corr_columns_values = []
        corr_columns_lens = []

        for player_team, player_id_team in match_dict.items():
            # player_id_team[]
            if corr_column in player_id_team:
                corr_columns_values.append(player_id_team[corr_column].values)
                corr_columns_lens.append(len(player_id_team[corr_column]))

        len_mode = scipy.stats.mode(corr_columns_lens).mode

        keys2del = []
        for key in range(len(corr_columns_values)):
            if len(corr_columns_values[key]) != len_mode:
                keys2del.append(key)

        for key in keys2del:
            del corr_columns_values[key]

        if len(corr_columns_values) > 1:
            corrs = np.corrcoef(corr_columns_values)

            corrs = np.triu(corrs, 1).ravel()
            corrs = corrs[corrs > 0]
            corr_ = corrs.mean()
            # match_corr[match] = hr_corr
        else:
            corr_ = 0

        entry[f'corr_{corr_column}'] = corr_

    entries.append(entry)


df_corr = pd.DataFrame(entries)
df_corr.groupby('team').mean()
df_corr.groupby('communication').mean()
df_corr.groupby(['team', 'communication']).mean()
df_corr.groupby(['team', 'real_opponents']).mean()
df_corr.groupby(['communication', 'real_opponents']).mean()
df_corr.groupby(['team', 'communication', 'real_opponents']).mean()
df_corr.groupby('real_opponents').mean()


mask_team = df_corr['team'] == 'amateurs'
mask_communication = df_corr['communication'] == 1
mask_real_opponents = df_corr['real_opponents'] == 1

df_corr.loc[mask_team, :].mean() - df_corr.loc[~mask_team, :].mean()
df_corr.loc[mask_communication, :].mean() - df_corr.loc[~mask_communication, :].mean()
df_corr.loc[mask_real_opponents, :].mean() - df_corr.loc[~mask_real_opponents, :].mean()

corr_dict = {}
corr_dict['amateurs'] = df_corr.loc[mask_team, :].mean()
corr_dict['pros'] = df_corr.loc[~mask_team, :].mean()

diff_dict = defaultdict(dict)
diff_dict['amateurs']['comm'] = df_corr.loc[mask_team & mask_communication, :].mean() - \
    df_corr.loc[mask_team & ~mask_communication, :].mean()
diff_dict['pros']['comm'] = df_corr.loc[~mask_team & mask_communication, :].mean() - \
    df_corr.loc[~mask_team & ~mask_communication, :].mean()
diff_dict['amateurs']['real_opp'] = df_corr.loc[mask_team & mask_real_opponents, :].mean() - \
    df_corr.loc[mask_team & ~mask_real_opponents, :].mean()
diff_dict['pros']['real_opp'] = df_corr.loc[~mask_team & mask_real_opponents, :].mean() - \
    df_corr.loc[~mask_team & ~mask_real_opponents, :].mean()

diff_dict['all']['comm'] = df_corr.loc[mask_communication, :].mean() - \
    df_corr.loc[~mask_communication, :].mean()
diff_dict['all']['real_opp'] = df_corr.loc[mask_real_opponents, :].mean() - \
    df_corr.loc[~mask_real_opponents, :].mean()


# columns = ['corr_gsr', 'corr_heart_rate',
#        'corr_emg_right_hand', 'corr_pupil_diameter', 'corr_mouse_pressed',
#        'corr_mouse_movement', 'corr_button_pressed', 'corr_gaze_movement',
#        'corr_thermal_data'
#            ]
#     # , 'corr_linaccel_x_right_hand',
#     #    'corr_linaccel_y_right_hand', 'corr_linaccel_z_right_hand']

columns_rename_dict = {
    'corr_gsr': 'gsr',
    'corr_heart_rate': 'hr',
    'corr_emg_right_hand': 'emg',
    # 'corr_emg_left_hand': 'emgl',
    'corr_pupil_diameter': 'pd',
    'corr_mouse_pressed': 'mc',
    # 'corr_mouse_movement': 'mm',
    'corr_button_pressed': 'bp',
    'corr_gaze_movement': 'gm',
    'corr_thermal_data': 'ft',
    'corr_linaccel_x_right_hand': 'hm',
    # 'corr_linaccel_y_right_hand': 'hy',
    # 'corr_linaccel_z_right_hand': 'hz',
    'corr_linaccel_x_chair_seat': 'cm',
    # 'corr_linaccel_y_chair_seat': 'cy',
    # 'corr_linaccel_z_chair_seat': 'cz',
    # 'corr_linaccel_x_chair_back': 'cbx',
    # 'corr_linaccel_y_chair_back': 'cby',
    # 'corr_linaccel_z_chair_back': 'cbz',
    # 'corr_gyro_x_chair_back': 'cbgx',
    # 'corr_gyro_y_chair_back': 'cbgy',
    # 'corr_gyro_z_chair_back': 'cbgz',
    # 'corr_gyro_x_chair_seat': 'gx',
    # 'corr_gyro_y_chair_seat': 'gy',
    'corr_gyro_z_chair_seat': 'cr',
}
columns_rename_dict = OrderedDict(columns_rename_dict)

# columns_short = [columns_rename_dict[column] for column in columns if column in columns_rename_dict]
columns = list(columns_rename_dict.keys())
columns_short = list(columns_rename_dict.values())

# fig.colorbar(ax)


def create_plot_0(series_list, columns, columns_short, figname='plot_0', headers=(), add_sign=True):
    """
    Plot 0:
    For both teams two 1d plot on how corr changes
    """
    size = len(columns_short)
    x_start, x_end = -0.5, len(columns_short) - 0.5
    y_start, y_end = 0, 1
    jump_x = (x_end - x_start) / (2.0 * size)
    x_positions = np.linspace(start=x_start, stop=x_end, num=size, endpoint=False)
    extent = [x_start, x_end, y_start, y_end]
    n_columns = len(headers)

    len_short = len(columns_short)

    plt.close()
    fig, ax_array = plt.subplots(1 + 2, 1 + n_columns, figsize=(0.9 + n_columns * len_short, 4.2), gridspec_kw={'width_ratios': [0.9] + [len_short] * n_columns, 'height_ratios': [0.2, 1, 1]})
    for n_plot, series in enumerate(series_list):
        n_row = 1 + n_plot // n_columns
        n_col = 1 + n_plot % n_columns
        ax = ax_array[n_row, n_col]
        ax.imshow(series[columns].values.reshape(1, -1), cmap='coolwarm', vmax=0.2, vmin=-0.2, extent=extent)
        ax.axes.get_yaxis().set_visible(False)
        ax.xaxis.tick_top()
        ax.set_xticks(np.arange(len_short))
        ax.set_xticklabels(labels=columns_short, fontsize=20)
        y = 0.5
        for x_index, x in enumerate(x_positions):
            # label = round(series[columns[x_index]], 2)
            label = '{:.2f}'.format(series[columns[x_index]])
            if add_sign and (float(label) > 0):
                label = '+' + str(label)

            text_x = x + jump_x
            text_y = y
            ax.text(text_x, text_y, label, color='black', ha='center', va='center', fontsize=16)

    for n_row in range(ax_array.shape[0]):
        for n_col in range(ax_array.shape[1]):
            ax = ax_array[n_row, n_col]
            if (n_row == 0) or (n_col == 0):
                ax.axis('off')

            if n_col == 0:
                if n_row == 1:  # amateurs
                    ax.text(0.9, 0.5, 'Amateurs', color='black', va='center', fontsize=24, ha='right')
                elif n_row == 2:  # pros
                    ax.text(0.9, 0.5, 'Pros', color='black', va='center', fontsize=24, ha='right')

            if n_row == 0:
                for n_col_ in range(1, 1 + n_columns):
                    if n_col == n_col_:
                        ax.text(0.5, 0.5, headers[n_col - 1], color='black', ha='center', va='center', fontsize=24)
                    # elif n_col == n_col_:
                    #     ax.text(0.5, 0.5, 'Real Opponents', color='black', ha='center', va='center', fontsize=24)

    fig.tight_layout()
    fig.savefig(pic_folder + f'{figname}.pdf')

series_list = []
series_list_comm = []
series_list_opp = []
series_list_corr = []
# for team in diff_dict:
for team in ['amateurs', 'pros']:
    series_list_corr.append(corr_dict[team])
    series_list_comm.append(diff_dict[team]['comm'])
    series_list_opp.append(diff_dict[team]['real_opp'])
    for mode in ['comm', 'real_opp']:
        series_list.append(diff_dict[team][mode])

        # label = team + '_' + mode
        # create_plot_0(diff_dict[team][mode], columns, columns_short, label)


# create_plot_0(series_list, columns, columns_short, 'team_dynamics_comm_and_opp', headers=('Communication Added', 'Real Opponents'))

create_plot_0(series_list_comm, columns, columns_short, 'team_dynamics_comm', headers=('Communication Added',))
create_plot_0(series_list_opp, columns, columns_short, 'team_dynamics_opp', headers=('Real Opponents Instead of Bots',))

create_plot_0(series_list_corr, columns, columns_short, 'correlations', headers=('Pairwise Correlations',), add_sign=False)




# Plot 0:
# For both teams two 1d plot on how corr changes
# Table 0:
# Compare two teams in one "realistic" scenario
# You're done

# mask_case = mask_communication & mask_real_opponents
df_case = df_corr.loc[mask_team, :].mean() - df_corr.loc[~mask_team, :].mean()
df_case.drop(['communication', 'real_opponents'], inplace=True)
score_0 = df_case.abs().mean()
score_1 = df_case.mean()
print(score_0, score_1)







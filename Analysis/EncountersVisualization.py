import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from config import *
import argparse
from collections import defaultdict
import json


columns2plot_dict = defaultdict(set)

def get_plot_params(data_source_columns_dict, n_rows=None, n_cols=None, n_players=1):
    n_plots =  sum([len(value) for value in data_source_columns_dict.values()]) * n_players
    if (n_rows is None) and (n_cols is None):
        n_cols = np.ceil(np.sqrt(n_plots)).astype(int)
        n_rows = (n_plots - 1) // n_cols + 1
    elif n_rows is None:
        n_rows = (n_plots - 1) // n_cols + 1
    elif n_cols is None:
        n_cols = (n_plots - 1) // n_rows + 1

    data_source_column2number_dict = {}
    number = 0
    for data_source, columns in data_source_columns_dict.items():
        columns_sorted = sorted(columns)
        for column in columns_sorted:
            data_source_column2number_dict[(data_source, column)] = number
            number += 1

    return n_plots, n_cols, n_rows, data_source_column2number_dict


if __name__ == '__main__':
    matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
    matches = [match for match in os.listdir(matches_processed_folder) if match.startswith('match')]

    match = 'match_10'
    for match in matches:
        player_id = 3
        for player_id in player_ids:
            path2player_folder = os.path.join(matches_processed_folder, match, f'player_{player_id}')

            data_source = 'imu_head'
            for data_source in data_sources:
                path2data_source = os.path.join(path2player_folder, f'{data_source}.csv')
                if not os.path.exists(path2data_source):
                    continue

                df4data_source = pd.read_csv(path2data_source, index_col='time', nrows=1)
                if data_source.startswith('imu'):
                    imu_suffix = data_source.split('imu')[1]
                    df4data_source.columns = [column + imu_suffix for column in df4data_source.columns]

                for column in df4data_source.columns:
                    columns2plot_dict[data_source].add(column)
                # plt.plot(df4data_source.index, )

    # n_plots = sum(len(columns2plot_dict[data_source]) for data_source in data_sources)

    targets = []

    match = 'match_10'
    for match in matches:
        path2meta_info = os.path.join(matches_processed_folder, match, 'meta_info.json')
        with open(path2meta_info) as f:
            meta_info = json.load(f)

        if not meta_info['real_opponents']:
            continue

        player_id = 3
        for player_id in player_ids:
            path2player_folder = os.path.join(matches_processed_folder, match, f'player_{player_id}')
            path2encounters = os.path.join(path2player_folder, 'encounters.json')
            with open(path2encounters) as f:
                player_encounters = json.load(f)

            targets4player = [player_encounter['outcome'] for player_encounter in player_encounters]
            targets = targets + targets4player

            # n_plots, n_cols, n_rows, data_source_column2number_dict = get_plot_params(
            #     data_source_columns_dict=columns2plot_dict)
            # plt.close()
            # fig, ax = plt.subplots(n_rows, n_cols, figsize=(32, 18))
            #
            # data_source = 'imu_head'
            # for data_source in data_sources:
            #     path2data_source = os.path.join(path2player_folder, f'{data_source}.csv')
            #     if not os.path.exists(path2data_source):
            #         continue
            #
            #     df4data_source = pd.read_csv(path2data_source, index_col='time')
            #     if data_source.startswith('imu'):
            #         imu_suffix = data_source.split('imu')[1]
            #         df4data_source.columns = [column + imu_suffix for column in df4data_source.columns]
            #
            #     # columns2plot4data_source = sorted(columns2plot_dict[data_source])
            #
            #     for column in columns2plot_dict[data_source]:
            #         n_plot = data_source_column2number_dict[(data_source, column)]
            #         n_row = n_plot // n_cols
            #         n_col = n_plot % n_cols
            #         ax[n_row, n_col].plot(df4data_source[column], label=column)
            #         ax[n_row, n_col].set_title(column, fontsize=10)
            #         # ax[n_row, n_col].axis('off')
            #         # ax[n_row, n_col].tick_params(axis='both', which='both', labelsize=7)
            #         ax[n_row, n_col].xaxis.set_major_locator(plt.NullLocator())
            #         ax[n_row, n_col].yaxis.set_major_locator(plt.NullLocator())
            #
            #         for player_encounter in player_encounters:
            #             if player_encounter['outcome'] == 0:
            #                 encounter_color = 'red'
            #             elif player_encounter['outcome'] == 1:
            #                 encounter_color = 'green'
            #             else:
            #                 raise ValueError(f'Unknown encounter outcome {player_encounter["outcome"]}')
            #
            #             ax[n_row, n_col].axvline(player_encounter['time'], c=encounter_color, linestyle=(0, (5, 7)), alpha=0.5)
            #
            #
            #         # ax[n_row, n_col].set_yticks([], [])
            #
            # for n_plot in range(n_plots, n_rows * n_cols):
            #     n_row = n_plot // n_cols
            #     n_col = n_plot % n_cols
            #     ax[n_row, n_col].remove()
            #
            # fig.tight_layout()
            # path2save = os.path.join(pic_folder, 'data_visualization', f'{match}_player_{player_id}_v0.png')
            # fig.savefig(path2save)











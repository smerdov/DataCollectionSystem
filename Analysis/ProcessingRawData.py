import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *
import argparse

# date = '2019-11-22'

parser = argparse.ArgumentParser()
parser.add_argument('--date', default='', type=str)
args = parser.parse_args()
date = args.date

eye_tracker_shift_hours = 1  # IMPORTANT: IT SHOULD BE 2 FOR CEST!!!
thermal_data_shape = (64, 48)

def concat_files4data_source(filenames, path, index_col, sep=','):
    df_result = pd.DataFrame()
    for filename in filenames:
        df_addition = pd.read_csv(path + filename, sep=sep)
        df_addition.set_index(index_col, inplace=True)
        df_result = pd.concat([df_result, df_addition])

    return df_result

def split_data_by_games(df_data_source, data_path_processed, games_start_end_times):
    for n_row, row in games_start_end_times.iterrows():
        game_num = row['game_num']
        game_start_time = datetime.strptime(row['game_start'], '%Y-%m-%d-%H:%M:%S').timestamp()
        game_end_time = datetime.strptime(row['game_end'], '%Y-%m-%d-%H:%M:%S').timestamp()
        game_dir = f'{data_path_processed}game_{game_num}/'

        mask4game = (game_start_time <= df_data_source.index) & (df_data_source.index <= game_end_time)
        df4game = df_data_source.loc[mask4game]
        df4game.index = df4game.index - game_start_time

        yield game_dir, df4game


# data_dict = {}

data_sources = [
    'arduino_0',
    'arduino_1',
    'arduino_2',
    'polar_heart_rate',
    'face_temperature',
    'eye_tracker',
    'mouse',
    'keyboard',
    'EEG',
]

data_path = f'{dataset_folder}{date}/'
data_path_processed = f'{dataset_folder}{date}_processed/'

games_start_end_times = pd.read_csv(data_path + 'labels/games_start_end_times.csv')

game_ids = list(games_start_end_times['game_num'])
player_ids = ['0', '1', '2', '3', '4']

for game_id in game_ids:
    game_dir = f'{data_path_processed}game_{game_id}/'
    if not os.path.exists(game_dir):
        os.mkdir(game_dir)

    for player_id in player_ids:
        player_game_dir = f'{game_dir}player_{player_id}/'
        if not os.path.exists(player_game_dir):
            os.mkdir(player_game_dir)

        # for data_source in data_sources:
        #     data_source_player_game_dir = f'{game_dir}player_{player_id}/{data_source}'
        #     if not os.path.exists(data_source_player_game_dir):
        #         os.mkdir(data_source_player_game_dir)


for data_source in ['environment']:
    sep = ','
    index_col = 'Timestamp'
    path2data_source = data_path + f'{data_source}/'
    filenames = sorted(os.listdir(path2data_source))
    filenames_filtered = [filename for filename in filenames if not (filename.startswith('game') or filename.startswith('.'))]
    df_data_source = concat_files4data_source(filenames_filtered, path2data_source, index_col=index_col, sep=sep)
    df_data_source.index = [datetime.strptime(x, '%Y-%m-%d-%H:%M:%S.%f').timestamp() for x in df_data_source.index]
    df_data_source.index.name = 'Timestamp'
    df_data_source.sort_index(inplace=True)

    for game_dir, df4game in split_data_by_games(df_data_source, data_path_processed, games_start_end_times):
        path = f'{game_dir}{data_source}.csv'
        df4game.to_csv(path)

# for data_source in ['face_temperature']:
#     sep = ','
#     index_col = 'Timestamp'
#     path2data_source = data_path + 'environment/'
#     filenames = sorted(os.listdir(path2data_source))
#     filenames_filtered = [filename for filename in filenames if not (filename.startswith('game') or filename.startswith('.'))]
#     df_data_source = concat_files4data_source(filenames_filtered, path2data_source, index_col=index_col, sep=sep)
#     df_data_source.index.name = 'Timestamp'
#     df_data_source.sort_index(inplace=True)
#
#     for game_dir, df4game in split_data_by_games(df_data_source, data_path_processed, games_start_end_times):
#         path = f'{game_dir}{data_source}.csv'
#         df4game.to_csv(path)



for player_id in player_ids:
    # player_data_dict = {}
    data_path4player = data_path + f'player_{player_id}/'
    data_sources_available = os.listdir(data_path4player)

    for data_source in data_sources:
        if data_source not in data_sources_available:
            continue

        if data_source in ['mouse', 'keyboard', 'EEG', 'face_temperature']:
            sep = ';'
        else:
            sep = ','

        if data_source in ['mouse', 'keyboard', 'EEG']:
            index_col = 'time'
        elif data_source == 'eye_tracker':
            index_col = '#timestamp'
        else:
            index_col = 'Timestamp'

        if data_source in ['arduino_0', 'arduino_1', 'arduino_2', 'keyboard', 'mouse', 'EEG']:
            time_format = '%Y-%m-%d-%H:%M:%S.%f'
        elif data_source in ['polar_heart_rate']:
            time_format = '%Y-%m-%d-%H:%M:%S'
        else:
            time_format = '%Y-%m-%d-%H:%M:%S.%f'


        path2data_source = data_path4player + data_source + '/'
        filenames = sorted(os.listdir(path2data_source))
        filenames_filtered = [filename for filename in filenames if not (filename.startswith('game') or filename.startswith('.'))]
        filenames_filtered = sorted(filenames_filtered)
        if data_source == 'eye_tracker':
            filenames_filtered = [filename for filename in filenames_filtered if filename.startswith('tobii_pro_gaze')]

        if len(filenames_filtered) == 0:
            continue

        if data_source == 'face_temperature':
            df_data_source = pd.DataFrame()

            for filename in filenames_filtered:
                thermal_data = pd.read_csv(path2data_source + filename, sep=sep, header=None).values
                # thermal_data = thermal_data.reshape(64, 48)
                # plt.imshow(thermal_data)
                # plt.interactive(True)
                thermal_data = list(thermal_data.reshape(-1, 1).ravel())
                datetime4filename = filename[-23:-4]
                datetime4filename = datetime.strptime(datetime4filename, '%Y-%m-%d-%H-%M-%S')
                timestamp4filename = datetime4filename.timestamp()
                row2add = pd.Series(data=[thermal_data], name=timestamp4filename, index=['thermal_data'])

                df_data_source = df_data_source.append(row2add)

            df_data_source.index.name = 'Timestamp'
        else:
            df_data_source = concat_files4data_source(filenames_filtered, path2data_source, index_col=index_col, sep=sep)

        # if data_source in ['arduino_0', 'arduino_1', 'arduino_2', 'keyboard', 'mouse', 'EEG']:
        #     df_data_source.index = [datetime.strptime(x, '%Y-%m-%d-%H:%M:%S.%f').timestamp() for x in df_data_source.index]

        if data_source not in ['eye_tracker', 'face_temperature']:
            df_data_source.index = [datetime.strptime(x, time_format).timestamp() for x in df_data_source.index]

        # if data_source in ['polar_heart_rate']:
        #     df_data_source.index = [datetime.strptime(x, '%Y-%m-%d-%H:%M:%S').timestamp() for x in df_data_source.index]

        if data_source == 'eye_tracker':
            df_data_source.index = df_data_source.index / 1000 + 3600 * eye_tracker_shift_hours

        df_data_source.index.name = 'Timestamp'
        df_data_source.sort_index(inplace=True)


        for game_dir, df4game in split_data_by_games(df_data_source, data_path_processed, games_start_end_times):
            if len(df4game) > 0:
                # earliest_time = df4game.index[0]

                path = f'{game_dir}player_{player_id}/{data_source}.csv'
                df4game.to_csv(path)


        # for n_row, row in games_start_end_times.iterrows():
        #     game_num = row['game_num']
        #     game_start_time = row['game_start']
        #     game_end_time = row['game_end']
        #     game_dir = f'{data_path_processed}game_{game_num}/'
        #
        #     mask4game = (game_start_time < df_data_source.index) & (df_data_source.index < game_end_time)
        #     df4game = df_data_source.loc[mask4game]
        #     if len(df4game) > 0:
        #         # earliest_time = df4game.index[0]
        #
        #         path = f'{game_dir}player_{player_id}/{data_source}.csv'
        #         df4game.to_csv(path)

















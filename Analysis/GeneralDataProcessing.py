import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *

day_name = '2019-11-15'
# player_id = 0
# arduino_id = 0
# if arduino_id == 0:
#     arduino_name = 'body'
# elif arduino_id == 1:
#     arduino_name = 'chair'
# elif arduino_id == 2:
#     arduino_name = 'heart_rate'
# else:
#     arduino_name = 'some_arduino'


eye_tracker_shift_hours = 4

def concat_files4data_source(filenames, path, index_col, sep=','):
    df_result = pd.DataFrame()
    for filename in filenames:
        df_addition = pd.read_csv(path + filename, sep=sep)
        df_addition.set_index(index_col, inplace=True)
        df_result = pd.concat([df_result, df_addition])

    return df_result

data_dict = {}

data_sources = [
    # 'arduino_0',
    # 'arduino_1',
    # 'arduino_2',
    'polar_heart_rate',
    # 'face_temperature',
    'eye_tracker',
    'mouse',
    'keyboard',
    'EEG',
]

data_path = f'{dataset_folder}{day_name}/'

games_start_end_times = pd.read_csv(data_path + 'games_start_end_times.csv')

for player_id in player_ids:
    player_data_dict = {}

    # data_path = f'{dataset_folder}day_{day_name}/player_{player_id}/'
    data_path4player = data_path + f'player_{player_id}/'

    data_sources_available = os.listdir(data_path4player)

    # for arduino_id in [0, 1, 2]:
    for data_source in data_sources:
        sep = ','
        # df4arduino = pd.DataFrame()
        # filename_prefix = f'arduino_{arduino_id}'
        # data_source = f'arduino_{arduino_id}'
        if data_source not in data_sources_available:
            os.mkdir(data_path4player + data_source)
            for game_num in range(1, 5):  # if there are 4 games
                path4game_folder = data_path4player + data_source + '/' + f'game_{game_num}'
                if not os.path.exists(path4game_folder):
                    os.mkdir(path4game_folder)

            continue

        path2data_source = data_path4player + data_source + '/'
        filenames = sorted(os.listdir(path2data_source))
        filenames_filtered = [filename for filename in filenames if not (filename.startswith('game') or filename.startswith('.'))]
        if data_source == 'eye_tracker':
            filenames_filtered = [filename for filename in filenames_filtered if filename.startswith('tobii_pro_gaze')]
            index_col = '#timestamp'
        elif data_source in ['mouse', 'keyboard', 'EEG']:
            index_col = 'time'
            sep = ';'
        else:
            index_col = 'Timestamp'

        # pd.read_csv(path2data_source + filenames_filtered[0], sep=';')
        df_data_source = concat_files4data_source(filenames_filtered, path2data_source, index_col=index_col, sep=sep)
        df_data_source.index.name = 'Timestamp'

        if data_source == 'eye_tracker':
            # break
            df_data_source.index = pd.to_datetime(df_data_source.index + 3600 * 4 * 1000, unit='ms')
            df_data_source.index = df_data_source.index.astype(str)
            df_data_source.index = [index.replace(' ', '-') for index in df_data_source.index]
            # df_data_source.index = df_data_source.index.apply(lambda x: x.timestamp())

        # df_data_source.rename(columns={'#timestamp': 'Timestamp'}, inplace=True)
        # df_data_source.set_index(['Timestamp'], inplace=True)
        # df_data_source.index = pd.to_datetime(df_data_source.index)
        # df_data_source.index = df_data_source.index.apply(lambda x: x.timestamp())
        df_data_source.sort_index(inplace=True)


        for n_row, row in games_start_end_times.iterrows():
            game_num = row['game_num']
            game_start_time = row['game_start']
            game_end_time = row['game_end']
            path4game_folder = data_path4player + data_source + '/' + f'game_{game_num}'
            if not os.path.exists(path4game_folder):
                os.mkdir(path4game_folder)

            # break
            mask4game = (game_start_time < df_data_source.index) & (df_data_source.index < game_end_time)
            df_data_source.loc[mask4game].to_csv(data_path4player + data_source + '/' + f'game_{game_num}/' + data_source + '.csv')

        # df_data_source = df_data_source.resample('1s').mean()
        # for filename in filenames_with_prefix:
        #     df_addition = pd.read_csv(data_path4player + filename)
        #     df_addition.set_index('Timestamp', inplace=True)
        #     df4arduino = pd.concat([df4arduino, df_addition])

        # player_data_dict[data_source] = df_data_source

    # ### Eye tracker
    # # filenames_with_prefix = [filename for filename in filenames if filename.startswith('tobii')]
    # df_eyetracker = concat_files4data_source(filenames_with_prefix, index_col='#timestamp')
    # df_eyetracker.index = pd.to_datetime(df_eyetracker.index + 3600 * 4 * 1000, unit='ms')
    # df_eyetracker.index = df_eyetracker.index.apply(lambda x: x.timestamp())
    # df_eyetracker.sort_index(inplace=True)
    # df_eyetracker = df_eyetracker.resample('1s').mean()
    # player_data_dict['eye_tracker'] = df_eyetracker
    #
    # data_dict[player_id] = player_data_dict


# pd.to_datetime(data_dict[1]['eye_tracker'].index + 3600 * 4 * 1000, unit='ms')  # It's a bullshit!  # Now not so much


# joblib.dump(data_dict, data_folder + 'data_dict')
































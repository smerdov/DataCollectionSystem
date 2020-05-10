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

# dates = ['2019-11-15', '2019-11-22']
dates = ['2019-11-22']
player_ids = ['player_0', 'player_1', 'player_2', 'player_3', 'player_4']

data_sources = [
    'arduino_0',
    'arduino_1',
    'arduino_2',
    'polar_heart_rate',
    # 'face_temperature',
    'eye_tracker',
    # 'mouse',
    'keyboard',
    # 'EEG',
]

data_sources_columns = { # If None, then plot all columns
    'arduino_0': ['gsr', 'emg_0', 'emg_1',
                  'linaccel_x_0', 'linaccel_y_0', 'linaccel_z_0',
                  'linaccel_x_1', 'linaccel_y_1', 'linaccel_z_1'],
    'arduino_1': ['linaccel_x_0', 'linaccel_y_0', 'linaccel_z_0',
                  'linaccel_x_1', 'linaccel_y_1', 'linaccel_z_1',
                  'gyro_x_0', 'gyro_y_0', 'gyro_z_0',
                  'gyro_x_1', 'gyro_y_1', 'gyro_z_1',
                  ],
    'arduino_2': ['irValue', 'redValue'],
    'eye_tracker': ['gaze_x', 'gaze_y', 'pupil_diameter'],
    'polar_heart_rate': ['heart_rate'],
    'face_temperature': None,
    # 'mouse': None,
    'keyboard': None,
    # 'EEG':
}


data_dict = {}

# date = dates[0]
for date in dates:
    date_dict = {}
    # data_path = f'{dataset_folder}{date}/'
    data_path_processed = f'{dataset_folder}{date}_processed/'

    game_names = sorted(os.listdir(data_path_processed))
    game_names = [game_name for game_name in game_names if game_name.startswith('game')]

    for game_name in game_names:
        game_path = data_path_processed + game_name + '/'
        game_dict = {}
        files4game_name = os.listdir(game_path)

        if 'replay.json' in files4game_name:
            game_dict['events'] = json.load(open(game_path + 'replay.json'))
        else:
            print(f'No replay in {game_path}')

        if 'environment.csv' in files4game_name:
            game_dict['environment'] = pd.read_csv(game_path + 'environment.csv')
            game_dict['environment'].set_index(['Timestamp'], inplace=True)
        else:
            print(f'No environment data in {game_path}')

        for player_id in player_ids:
            if not (f'{player_id}' in files4game_name):
                print(f'No data about {player_id}')
                continue

            player_path = game_path + player_id + '/'
            player_dict = {}
            files4player = os.listdir(player_path)

            for data_source in data_sources:
                if (data_source + '.csv') not in files4player:
                    print(f'No {data_source} for {player_id}')
                    continue

                if data_source not in data_sources_columns:
                    selected_columns = None
                else:
                    selected_columns = data_sources_columns[data_source]
                    # if data_sources_columns[data_source] is None:

                df_data_source = pd.read_csv(player_path + data_source + '.csv')
                df_data_source.set_index(['Timestamp'], inplace=True)

                if selected_columns is not None:
                    df_data_source = df_data_source.loc[:, selected_columns]

                player_dict[data_source] = df_data_source


            game_dict[player_id] = player_dict

        date_dict[game_name] = game_dict

    data_dict[date] = date_dict

joblib.dump(data_dict, '../Data/data_dict')










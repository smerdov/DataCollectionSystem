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

parser = argparse.ArgumentParser()
parser.add_argument('--time-step', default='5s', type=str)
parser.add_argument('--forecasting-horizon', default=10, type=float, help='Forecasting horizon in seconds')
parser.add_argument('--suffix', default='last', type=str, help='Suffix to append to files')
# args = parser.parse_args([])  # TODO: comment
args = parser.parse_args()  # TODO: uncomment
teams = ['amateurs', 'pros']

matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
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
    'keyboard',
    'mouse',
    'eye_tracker',
]



# test_matches = ['match_10', 'match_11']

matches_dict = defaultdict(dict)

# match = 'match_0'
for match in matches:
    path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
    with open(path2meta_info) as f:
        meta_info_json = json.load(f)

    team = meta_info_json['team']
    # player_id = 0
    for player_id in player_ids:
        df4player = pd.DataFrame()
        path2encounters = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'encounters.json')

        with open(path2encounters) as f:
            encounters_json = json.load(f)


        player_id_team = (player_id, team)

        df_encounters = pd.DataFrame.from_records(encounters_json).set_index('time').rename(columns={'outcome':'encounter_outcome'})
        df_encounters.index = df_encounters.index - args.forecasting_horizon
        df_encounters = df_encounters.loc[df_encounters.index > 0, :]
        df_encounters.index = pd.TimedeltaIndex(df_encounters.index, unit='s')
        df_encounters.index = df_encounters.index.floor(args.time_step)
        # For the case when args.time_step in this script
        df_encounters = (df_encounters.groupby(by='time').mean() > 0.5) * 1

        # data_source = 'gsr'
        # data_source = 'keyboard'
        for data_source in data_sources2use:
            path2data_source = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'{data_source}.csv')

            if not os.path.exists(path2data_source):
                # print(f'{path2data_source} doesn\'t exist')
                continue

            df4data_source = pd.read_csv(path2data_source, index_col='time')
            df4data_source.index = pd.TimedeltaIndex(df4data_source.index, unit='s')
            if data_source.startswith('imu'):
                imu_suffix = data_source.split('imu')[1]
                df4data_source.columns = [column + imu_suffix for column in df4data_source.columns]

            df4player = df4player.join(df4data_source, how='outer')
            # print(data_source)
            # print(len(df4player))

        df4player = df4player.interpolate('linear', limit_area='inside')
        df4player.fillna(df4player.median(), inplace=True)

        df4player_resampled = df4player.resample(args.time_step).mean()

        df_encounters = df4player_resampled.join(df_encounters, how='outer')['encounter_outcome']  # Trick
        df_encounters = df_encounters.fillna(-1).astype(int)
        assert len(df_encounters) == len(df4player_resampled)

        matches_dict[match][player_id_team] = {
            'data': df4player_resampled,
            'target': df_encounters,
        }


def get_match_type(day_num, real_opponents):
    if real_opponents:
        if day_num > 1:
            return 'test'
        else:
            return 'train'
    else:
        return 'ignore'

ss_dict = {}
# train_dict = {}
# test_dict = {}
data_dict = {
    'train': {},
    'test': {},
}


# team = 'amateurs'
for team in teams:
    # player_id = 3
    for player_id in player_ids:
        player_id_team = (player_id, team)
        player_train_list = []
        ss = StandardScaler()

        # match = 'match_1'
        ### Collecting all train data to one df to fit standard scaler
        for match in matches:
            path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
            with open(path2meta_info) as f:
                meta_info_json = json.load(f)

            if meta_info_json['team'] != team:
                continue

            match_type = get_match_type(meta_info_json['day_num'], meta_info_json['real_opponents'])
            if match_type == 'train':
                # print(match)
                df2append = matches_dict[match][player_id_team]['data']
                player_train_list.append(df2append)

        all_train_df = pd.concat(player_train_list, axis=0).loc[:, columns_order]
        ss.fit(all_train_df.values)
        # tmp.tail(100)

        for match in matches:
            player_id_team_match = (player_id, team, match)
            path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
            with open(path2meta_info) as f:
                meta_info_json = json.load(f)

            if meta_info_json['team'] != team:
                continue

            match_type = get_match_type(meta_info_json['day_num'], meta_info_json['real_opponents'])
            if match_type == 'ignore':
                continue

            df4player_match = matches_dict[match][player_id_team]['data']
            target4player_match = matches_dict[match][player_id_team]['target']
            for column in columns_order:
                if column not in df4player_match.columns:
                    df4player_match[column] = None

            df4player_match_copy = df4player_match.fillna(df4player_match.median()).loc[:, columns_order].copy()

            last_index = np.nonzero(target4player_match.values != -1)[-1][-1] + 1  # We are not interested in duplicating -1 in the end
            df4player_match_copy = df4player_match_copy.iloc[:last_index, :]
            target4player_match = target4player_match.iloc[:last_index]

            df4player_match_copy.loc[:, :] = ss.transform(df4player_match_copy.values)
            df4player_match_copy.fillna(0, inplace=True)

            # data_dict[match_type][player_id_team] = {
            data_dict[match_type][player_id_team_match] = {
                'data': torch.Tensor(df4player_match_copy.values),
                'target': torch.IntTensor(target4player_match.values),
            }

            # if match_type == 'train':
            #     print(match)
            #     df2append = matches_dict[match][player_id_team]['data']
            #     player_train_list.append(df2append)

joblib.dump(data_dict, os.path.join(data_folder, f'data_dict_{args.suffix}'))

# data_dict.keys()
# data_dict['train']
# len(data_dict['train'])
# data_dict['test']
# len(data_dict['test'])
















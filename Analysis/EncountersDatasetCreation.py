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
parser.add_argument('--add-val', default=0, type=int, choices=[0, 1], help='Whether to add validation dataset')
# args = parser.parse_args([])  # TODO: comment
args = parser.parse_args()  # TODO: uncomment
teams = ['amateurs', 'pros']

matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
encounters_dataset_folder = os.path.join(dataset_folder, 'encounters_dataset')
matches = [match for match in os.listdir(matches_processed_folder) if match.startswith('match')]
# time_step = f'{args.timestep}s'

data_sources2use = [
    'gsr',
    'emg',
    'spo2',
    'heart_rate',
    'imu_left_hand',
    'imu_right_hand',
    'imu_chair_seat',
    'imu_chair_back',
    'imu_head',
    'keyboard',
    'mouse',
    'eye_tracker',
    'facial_skin_temperature',
    'eeg_band_power',
    'eeg_metrics',
    'environment',
]



# test_matches = ['match_10', 'match_11']

matches_dict = defaultdict(dict)

# match = 'match_3'
for match in matches:
    path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
    with open(path2meta_info) as f:
        meta_info_json = json.load(f)

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

        df_encounters = pd.DataFrame.from_records(encounters_json).set_index('time').rename(columns={'outcome':'encounter_outcome'})
        df_encounters.index = df_encounters.index - args.forecasting_horizon
        df_encounters = df_encounters.loc[df_encounters.index > 0, :]
        df_encounters.index = pd.TimedeltaIndex(df_encounters.index, unit='s')
        df_encounters.index = df_encounters.index.floor(args.time_step)
        # For the case when args.time_step in this script
        df_encounters = (df_encounters.groupby(by='time').mean() > 0.5) * 1

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

                # # Keeping only linaccel and gyro columns, converting to absolute values
                # columns2keep = [column for column in df4data_source.columns if ((column.find('linaccel') != -1) or (column.find('gyro') != -1) or (column.find('rot') != -1))]
                # df4data_source = df4data_source.loc[:, columns2keep]
                # df4data_source = df4data_source.abs()

            df4player = df4player.join(df4data_source, how='outer')
            # print(data_source)
            # print(len(df4player))

        if last_index not in df4player.index:
            df4player.loc[last_index, :] = None

        df4player = df4player.interpolate('linear', limit_area='inside')
        df4player.fillna(df4player.median(), inplace=True)

        # # mask_null = df4player.isnull()
        # median = df4player.median()
        # noise = median.copy()
        # noise.loc[:] = np.random.randn(df4player.shape[1])
        # df4player = df4player.fillna(median, inplace=False) * 0.2 + df4player.fillna(noise, inplace=False) * 0.8
        # # df4player = (df4player.fillna(median, inplace=False) + df4player.fillna(noise, inplace=False) + \
        # #     df4player.fillna(0, inplace=False)) / 3
        # # df4player.loc[mask_null] = df4player.loc[mask_null] + (np.random.randn(df4player.shape[0], df4player.shape[1]) * 0.1)[mask_null]

        df4player_resampled = df4player.resample(args.time_step).mean()
        print(df4player_resampled.shape)

        df_encounters = df4player_resampled.join(df_encounters, how='outer')['encounter_outcome']  # Trick
        df_encounters = df_encounters.fillna(-1).astype(int)
        assert len(df_encounters) == len(df4player_resampled)

        matches_dict[match][player_id_team] = {
            'data': df4player_resampled,
            'target': df_encounters,
        }


def get_match_type(day_num, real_opponents, day_match_num, args):
    if real_opponents:
        if day_num == 0:
            return 'train'
        elif day_num == 1:
            # return 'test'  # Unfair
            if args.add_val: # Fair
                if day_match_num < 2:
                    return 'train'
                else:
                    return 'val'
            else:
                return 'train'
        elif day_num == 2:
            # return 'train'  # Unfair
            return 'test'  # Fair
        else:
            raise ValueError(f'Unknown day_num {day_num}')
    else:
        return 'ignore'

ss_dict = {}
# # train_dict = {}
# # test_dict = {}
# data_dict = {
#     'val': {},
#     'train': {},
#     'test': {},
# }


# team = 'pros'
for team in teams:
    # player_id = 1
    for player_id in player_ids:
        player_id_team = (player_id, team)
        player_train_list = []
        ss = StandardScaler()

        # match = 'match_10'
        ### Collecting all train data to one df to fit standard scaler
        for match in matches:
            path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
            with open(path2meta_info) as f:
                meta_info_json = json.load(f)

            if meta_info_json['team'] != team:
                continue

            match_type = get_match_type(meta_info_json['day_num'], meta_info_json['real_opponents'], meta_info_json['day_match_num'], args)
            if match_type == 'train':
                # print(match)
                df2append = matches_dict[match][player_id_team]['data']
                player_train_list.append(df2append)



        all_train_df = pd.concat(player_train_list, axis=0)
        for column in columns_order:
            if column not in all_train_df:
                all_train_df[column] = None

        all_train_df = all_train_df.loc[:, columns_order]
        ss.fit(all_train_df.values)
        # tmp.tail(100)

        # match = 'match_10'
        for match in matches:
            player_id_team_match = (player_id, team, match)
            path2meta_info = os.path.join(matches_processed_folder, match, f'meta_info.json')
            with open(path2meta_info) as f:
                meta_info_json = json.load(f)

            if meta_info_json['team'] != team:
                continue

            match_type = get_match_type(meta_info_json['day_num'], meta_info_json['real_opponents'], meta_info_json['day_match_num'], args)
            if match_type == 'ignore':
                continue

            df4player_match = matches_dict[match][player_id_team]['data']
            target4player_match = matches_dict[match][player_id_team]['target']
            for column in columns_order:
                if column not in df4player_match.columns:
                    df4player_match[column] = None

            df4player_match_copy = df4player_match.fillna(df4player_match.median()).loc[:, columns_order].copy()

            # # Commented. We are more interested in the same sequence length for all players
            # last_index = np.nonzero(target4player_match.values != -1)[-1][-1] + 1  # We are not interested in duplicating -1 in the end
            # df4player_match_copy = df4player_match_copy.iloc[:last_index, :]
            # target4player_match = target4player_match.iloc[:last_index]

            df4player_match_copy.loc[:, :] = ss.transform(df4player_match_copy.values)
            df4player_match_copy.fillna(0, inplace=True)

            output_folder = os.path.join(encounters_dataset_folder, match_type, match, f'player_{player_id}')
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            df4player_match_copy.to_csv(os.path.join(output_folder, 'data.csv'), index=False, header=False)
            target4player_match.to_csv(os.path.join(output_folder, 'target.csv'), index=False, header=False)
            with open(os.path.join(output_folder, 'meta_info.json'), 'w') as f:
                json.dump(meta_info_json, f)

            # data_dict[match_type][player_id_team_match] = {
            #     'data': torch.Tensor(df4player_match_copy.values),
            #     'target': torch.IntTensor(target4player_match.values),
            # }

            # if match_type == 'train':
            #     print(match)
            #     df2append = matches_dict[match][player_id_team]['data']
            #     player_train_list.append(df2append)

# joblib.dump(data_dict, os.path.join(data_folder, f'data_dict_{args.suffix}'))

# data_dict.keys()
# data_dict['train']
# len(data_dict['train'])
# data_dict['test']
# len(data_dict['test'])
















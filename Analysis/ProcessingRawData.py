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
from utils import gsr_to_ohm
import tqdm

# date = '2019-11-22'

parser = argparse.ArgumentParser()
parser.add_argument('--dates', nargs='+', default='', type=str)
parser.add_argument('--only-metadata', action='store_true')
args = parser.parse_args()
if args.dates[0] == 'all_dates':
    args.dates = all_dates
# args = parser.parse_args(['--date', '2019-12-17'])
# args = parser.parse_args(['--date', '2019-12-11b'])
# args = parser.parse_args(['--only-metadata', '--dates', '2019-11-15'])

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

data_rename_dict = {
    'arduino_0': ['gsr', 'emg', 'imu_right_hand', 'imu_left_hand'],
    'arduino_1': ['imu_chair_seat', 'imu_chair_back'],
    'arduino_2': 'particle_sensor',
    'polar_heart_rate': 'heart_rate',
    'EEG': ['eeg_band_power', 'imu_head', 'eeg_device_info', 'eeg_metrics'],
}

def save2path(game_dir, player_id, filename, df):
    path = f'{game_dir}player_{player_id}/{filename}.csv'
    df.to_csv(path)

# date = list(args.dates)[0]
for date in tqdm.tqdm(args.dates, desc='date\'s progress...'):

    eye_tracker_shift_hours = 1  # IMPORTANT: IT SHOULD BE 2 FOR CEST!!!
    thermal_data_shape = (64, 48)

    def concat_files4data_source(filenames, path, index_col, sep=','):
        df_result = pd.DataFrame()
        for filename in filenames:
            try:
                df_addition = pd.read_csv(path + filename, sep=sep)
            except UnicodeDecodeError:
                df_addition = pd.read_csv(path + filename, sep=sep, encoding='latin')

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


    data_path = f'{dataset_folder}{date}/'
    data_path_processed = f'{dataset_folder}{date}_processed/'

    games_start_end_times = pd.read_csv(data_path + 'labels/games_start_end_times.csv')

    ### Game lengths calculation
    game_lenghts = pd.to_datetime(games_start_end_times['game_end']) - pd.to_datetime(games_start_end_times['game_start'])
    game_lenghts.index = games_start_end_times['game_num']
    game_lenghts = game_lenghts / pd.Timedelta(seconds=1)
    game_lenghts = game_lenghts.astype(int)
    ### End of game lengths calculation

    game_ids = list(games_start_end_times['game_num'])
    player_ids = ['0', '1', '2', '3', '4']

    for game_id in game_ids:
        game_dir = f'{data_path_processed}game_{game_id}/'
        if not os.path.exists(game_dir):
            # os.mkdir(game_dir)
            os.makedirs(game_dir)

        for player_id in player_ids:
            player_game_dir = f'{game_dir}player_{player_id}/'
            if not os.path.exists(player_game_dir):
                os.makedirs(player_game_dir)

            # for data_source in data_sources:
            #     data_source_player_game_dir = f'{game_dir}player_{player_id}/{data_source}'
            #     if not os.path.exists(data_source_player_game_dir):
            #         os.mkdir(data_source_player_game_dir)


    exp_dict = date2exp_dict[date]
    game_id_infos = {}

    for game_id in game_ids:
        game_day_instance = GameDay(exp_dict['day_num'], game_id, exp_dict['team'])
        game_id_infos[game_id] = game_day_instance.get_stats()
        game_id_infos[game_id].update(exp_dict)
        game_id_infos[game_id]['day_num'] = game_id_infos[game_id]['day_num'] - 1
        game_id_infos[game_id]['day_match_num'] = game_id - 1
        if (date == '2019-12-11a') and (game_id == 4):
            game_id_infos[game_id]['day_match_num'] = game_id_infos[game_id]['day_match_num'] - 1  # Because match #3 was skipped

        game_id_infos[game_id]['match_duration'] = int(game_lenghts[game_id])

        path2game_info = os.path.join(data_path_processed, f'game_{game_id}', 'meta_info.json')

        with open(path2game_info, 'w') as f:
            json.dump(game_id_infos[game_id], f)

    if args.only_metadata:
        continue

    for data_source in ['environment']:
        sep = ','
        index_col = 'Timestamp'
        path2data_source = data_path + f'{data_source}/'
        filenames = sorted(os.listdir(path2data_source))
        filenames_filtered = [filename for filename in filenames if not (filename.startswith('game') or filename.startswith('.'))]
        df_data_source = concat_files4data_source(filenames_filtered, path2data_source, index_col=index_col, sep=sep)
        df_data_source.index = [datetime.strptime(x, '%Y-%m-%d-%H:%M:%S.%f').timestamp() for x in df_data_source.index]
        # df_data_source.index.name = 'Timestamp'
        df_data_source.index.name = 'time'
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



    for player_id in tqdm.tqdm(player_ids, desc='player\'s progress...'):
        data_path4player = data_path + f'player_{player_id}/'
        data_sources_available = os.listdir(data_path4player)

        for data_source in tqdm.tqdm(data_sources, desc='data source progress...'):
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
                # df_data_source.index = df_data_source.index / 1000 + 3600 * eye_tracker_shift_hours
                # When using '+' it looks like the data is misaligned probably for about 2 hours
                df_data_source.index = df_data_source.index / 1000 - 3600 * eye_tracker_shift_hours

            df_data_source.index.name = 'Timestamp'
            df_data_source.sort_index(inplace=True)


            for game_dir, df4game in split_data_by_games(df_data_source, data_path_processed, games_start_end_times):
                if len(df4game) > 0:
                    # earliest_time = df4game.index[0]
                    # data_rename_dict
                    df4game.index.name = 'time'

                    if data_source in data_rename_dict:
                        if type(data_rename_dict[data_source]) == str:
                            filename = data_rename_dict[data_source]
                            if data_source == 'arduino_2':
                                df4game.rename(columns={
                                    'irValue': 'ir_value',
                                    'redValue': 'red_value',
                                }, inplace=True)
                            if data_source == 'polar_heart_rate':
                                df4game.loc[:, 'heart_rate'] = df4game.loc[:, 'heart_rate'].astype(int)
                            # path = f'{game_dir}player_{player_id}/{filename}.csv'
                            # df4game.to_csv(path)
                            save2path(game_dir, player_id, filename, df4game)
                        else:  # We need to split columns
                            if data_source == 'arduino_1':
                                columns_part_0 = [column for column in df4game.columns if column.endswith('0')]
                                columns_part_0_renamed = [column.replace('_0', '') for column in columns_part_0]
                                columns_part_1 = [column for column in df4game.columns if column.endswith('1')]
                                columns_part_1_renamed = [column.replace('_1', '') for column in columns_part_1]

                                df_imu_chair_seat = df4game.loc[:, columns_part_0]
                                df_imu_chair_seat.rename(columns=dict(zip(columns_part_0, columns_part_0_renamed)), inplace=True)
                                filename_0 = data_rename_dict[data_source][0]
                                save2path(game_dir, player_id, filename_0, df_imu_chair_seat)

                                df_imu_chair_back = df4game.loc[:, columns_part_1]
                                df_imu_chair_back.rename(columns=dict(zip(columns_part_1, columns_part_1_renamed)), inplace=True)
                                filename_1 = data_rename_dict[data_source][1]
                                save2path(game_dir, player_id, filename_1, df_imu_chair_back)
                            elif data_source =='arduino_0':
                                columns_part_0 = ['gsr']
                                columns_part_1 = ['emg_0', 'emg_1']
                                columns_part_1_renamed = ['emg_right_hand', 'emg_left_hand']
                                columns_part_2 = [column for column in df4game.columns if column not in (columns_part_0 + columns_part_1)]
                                columns_right_hand = [column for column in columns_part_2 if column.endswith('0')]
                                columns_left_hand = [column for column in columns_part_2 if column.endswith('1')]
                                columns_right_hand_renamed = [column.replace('_0', '') for column in columns_right_hand]
                                columns_left_hand_renamed = [column.replace('_1', '') for column in columns_left_hand]
                                # columns_part_0 = ['gsr']

                                df_gsr = df4game.loc[:, columns_part_0]
                                df_gsr['gsr'] = gsr_to_ohm(df_gsr['gsr'])
                                filename = data_rename_dict[data_source][0]
                                save2path(game_dir, player_id, filename, df_gsr)

                                df_emg = df4game.loc[:, columns_part_1]
                                df_emg.rename(columns=dict(zip(columns_part_1, columns_part_1_renamed)), inplace=True)
                                filename = data_rename_dict[data_source][1]
                                save2path(game_dir, player_id, filename, df_emg)

                                df_imu_right_hand = df4game.loc[:, columns_right_hand]
                                df_imu_right_hand.rename(columns=dict(zip(columns_right_hand, columns_right_hand_renamed)), inplace=True)
                                filename = data_rename_dict[data_source][2]
                                save2path(game_dir, player_id, filename, df_imu_right_hand)

                                df_imu_left_hand = df4game.loc[:, columns_left_hand]
                                df_imu_left_hand.rename(columns=dict(zip(columns_left_hand, columns_left_hand_renamed)), inplace=True)
                                filename = data_rename_dict[data_source][3]
                                save2path(game_dir, player_id, filename, df_imu_left_hand)

                            elif data_source == 'EEG':
                                ### 'EEG': ['eeg_band_power', 'imu_head', 'eeg_device_info', 'eeg_metrics'],
                                # mot_entries = []
                                # pow_entries = []
                                entries = {
                                    'mot': [],
                                    'pow': [],
                                    'dev': [],
                                    'met': [],
                                }

                                time_indexes = {
                                    'mot': [],
                                    'pow': [],
                                    'dev': [],
                                    'met': [],
                                }

                                for n_row, row in df4game.iterrows():
                                    # entry = json.loads(df4data_source.iloc[0, 0])
                                    entry = json.loads(row['content'])
                                    key = list(entry.keys())[0]
                                    if key in entries:
                                        entries[key].append(entry[key])
                                        # time_indexes[key].append(row.name / pd.Timedelta(seconds=1))
                                        time_indexes[key].append(row.name)
                                    else:
                                        print(f'Unknown entry {entry}')
                                        # raise ValueError(f'Unknown entry {entry}')

                                ### pow --- Band Power
                                df_pow = pd.DataFrame(np.array(entries['pow']))
                                df_pow.columns = [
                                    "AF3/theta", "AF3/alpha", "AF3/betaL", "AF3/betaH", "AF3/gamma",
                                    "T7/theta", "T7/alpha", "T7/betaL", "T7/betaH", "T7/gamma",
                                    "Pz/theta", "Pz/alpha", "Pz/betaL", "Pz/betaH", "Pz/gamma",
                                    "T8/theta", "T8/alpha", "T8/betaL", "T8/betaH", "T8/gamma",
                                    "AF4/theta", "AF4/alpha", "AF4/betaL", "AF4/betaH", "AF4/gamma"
                                ]
                                df_pow['time'] = np.array(time_indexes['pow'])
                                df_pow.set_index(['time'], inplace=True)
                                filename = data_rename_dict[data_source][0]
                                save2path(game_dir, player_id, filename, df_pow)

                                ### mot --- Head Motion (IMU)
                                df_mot = pd.DataFrame(np.array(entries['mot'])[:, 2:])
                                df_mot.columns = ['acc_x', 'acc_y', 'acc_z', 'mag_x', 'mag_y', 'mag_z', 'q0', 'q1',
                                                  'q2', 'q3']
                                # df_mot['mag_y'].mean()
                                # df_mot['mag_y'].max()
                                # df_mot['mag_y'].min()
                                # df_mot['acc_x'].mean()
                                # df_mot.set_index(time_indexes['mot'], inplace=True)
                                df_mot['time'] = np.array(time_indexes['mot'])
                                df_mot.set_index(['time'], inplace=True)
                                filename = data_rename_dict[data_source][1]
                                save2path(game_dir, player_id, filename, df_mot)

                                ### dev --- Device Info
                                df_dev = pd.DataFrame(np.array(entries['dev']))
                                # df_dev = df_dev.append(df_dev[2].apply(lambda x: pd.Series(x)))
                                df_dev = pd.concat([df_dev, df_dev[2].apply(lambda x: pd.Series(x))], axis=1)
                                df_dev.columns = ["Battery", "Signal", 'tmp', "AF3", "T7", "Pz", "T8", "AF4"]
                                df_dev.drop(columns='tmp', inplace=True)
                                # df_dev.set_index(time_indexes['dev'], inplace=True)
                                df_dev['time'] = np.array(time_indexes['dev'])
                                df_dev.set_index(['time'], inplace=True)
                                filename = data_rename_dict[data_source][2]
                                save2path(game_dir, player_id, filename, df_dev)

                                ### met --- EEG Metrics
                                df_met = pd.DataFrame(np.array(entries['met']))
                                df_met.columns = [
                                    "Engagement.isActive", "Engagement",
                                    "Excitement.isActive", "Excitement", "Long term excitement",
                                    "Stress.isActive", "Stress",
                                    "Relaxation.isActive", "Relaxation",
                                    "Interest.isActive", "Interest",
                                    "Focus.isActive", "Focus",
                                ]
                                # df_met.columns = [
                                #     "eng.isActive", "eng",
                                #     "exc.isActive", "exc", "lex",
                                #     "str.isActive", "str",
                                #     "rel.isActive", "rel",
                                #     "int.isActive", "int",
                                #     "foc.isActive", "foc"
                                # ]
                                # df_met.set_index(time_indexes['met'], inplace=True)
                                df_met['time'] = np.array(time_indexes['met'])
                                df_met.set_index(['time'], inplace=True)
                                filename = data_rename_dict[data_source][3]
                                save2path(game_dir, player_id, filename, df_met)
                    else:
                        filename = data_source
                        save2path(game_dir, player_id, filename, df4game)



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



















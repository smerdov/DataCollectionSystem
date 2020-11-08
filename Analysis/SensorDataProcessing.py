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
import shutil
from scipy.spatial.transform import Rotation as R
from hr_spo2_lib import calc_hr_and_spo2

parser = argparse.ArgumentParser()
parser.add_argument('--halflife', default=1, type=float, help='Smoothing parameter')
parser.add_argument('--resampling-string', default='500ms', type=str, help='Timestep for resampling')
parser.add_argument('--preresampling-string', default='100ms', type=str, help='Timestep for preresampling for mouse, '
                                                  'keyboard and eyetracker. These data sources have too many data.')
parser.add_argument('--plot', action='store_true')
parser.add_argument('--halflifes-in-window', default=5, type=float)

def get_spo2_df(df):
    ir_values = df['ir_value'].values
    red_values = df['red_value'].values
    timestamps = df.index.values
    entries = []

    step = 100
    for i in range(len(ir_values) // step):
        index_start = step * i
        index_end = step * (i + 1)
        timestamp = timestamps[index_end - 1]
        hr, hr_valid, spo2, spo2_valid = calc_hr_and_spo2(ir_values[index_start:index_end], red_values[index_start:index_end])
        if spo2_valid:
            entry = {
                'spo2': spo2,
                'time': timestamp,
            }
            entries.append(entry)

    df_spo2 = pd.DataFrame(entries)
    df_spo2.set_index('time', inplace=True)

    return df_spo2

def time_ewa(series, halflife, mode):
    time_diffs = series.index / pd.Timedelta(seconds=1)
    time_diffs = time_diffs.values
    time_diffs = time_diffs.max() - time_diffs
    # Folmula from https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
    alpha = 1 - np.exp(np.log(0.5) / halflife)
    weights = (1 - alpha) ** time_diffs
    if mode == 'mean':  # Normalizing all weights to zero
        weights = weights / weights.sum()
    elif mode == 'sum':
        # Keeping weights as is
        pass
    else:
        raise ValueError(f'Don\'t know mode {mode}')

    result = (series * weights).sum()

    return result

def smooth_df(df, halflife, mode='mean'):
    window_size = pd.Timedelta(seconds=halflife * args.halflifes_in_window)
    df_smoothed = df.rolling(window=window_size).apply(lambda x: time_ewa(x, halflife, mode))

    return df_smoothed

def plot_smoothed_values(df, halflives):
    plt.close()
    n_features = len(df.columns)
    fig, ax = plt.subplots(nrows=n_features, ncols=1, figsize=(12, 6 * n_features), sharex=True, squeeze=False)
    for halflife in tqdm.tqdm(halflives):
        if halflife == 0:
            df_smoothed = df
        else:
            df_smoothed = smooth_df(df, halflife)

        for n_row, column in enumerate(df_smoothed.columns):
            ax[n_row, 0].plot(df_smoothed.index / one_second_unit, df_smoothed[column].values, label=f'halflife={halflife}')

    for n_feature in range(n_features):
        ax[n_feature, 0].legend()

    plt.show()
    plt.close()

def extract_press_events(df):
    press_events_times = []
    pressed_buttons = set()

    for time_index, row in df.iterrows():
        button = row['button']
        event = row['event']

        if event == 'kp':
            if button not in pressed_buttons:
                pressed_buttons.add(button)
                # time_press = time_index
                press_events_times.append(time_index)
        elif event =='kr':
            if button in pressed_buttons:
                pressed_buttons.remove(button)
            else:
                print('Button released, but not pressed, looks strange.')

    df_key_pressed = pd.DataFrame.from_records(zip(press_events_times, np.ones_like(press_events_times)),
                                               columns=['time', 'buttons_pressed'])

    df_key_pressed = df_key_pressed.drop_duplicates()
    df_key_pressed.set_index(['time'], inplace=True)

    return df_key_pressed

def save_df(df, path2save):
    df.index = df.index / one_second_unit
    df.to_csv(path2save)

def resample_smooth_save_df(df, path2save, resampling_string, halflife, resampling_method='mean', smooth=True):
    df.index = df.index.floor(resampling_string)
    if resampling_method == 'mean':
        df = df.resample(resampling_string).mean()
    elif resampling_method == 'sum':
        df = df.resample(resampling_string).sum()

    # Some indexes can have NaN values. We need to fill it to proper smoothing
    if resampling_method == 'mean':
        df = df.interpolate('linear', limit_area='inside')

    if smooth:
        df_smoothed = smooth_df(df, halflife, mode=resampling_method)
    else:
        df_smoothed = df
    # df_smoothed.to_csv(path2save)
    save_df(df_smoothed, path2save)


if __name__ == '__main__':
    # args = parser.parse_args([])
    args = parser.parse_args()

    matches_folder = os.path.join(dataset_folder, 'matches')
    matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
    matches = [match for match in os.listdir(matches_folder) if match.startswith('match')]
    one_second_unit = pd.Timedelta(seconds=1)
    print(f'Resampling with {args.resampling_string}')

    # match = 'match_9'  # TODO: comment
    for match in tqdm.tqdm(matches, 'Processing matches...'):
        print(f'Processing match {match}')
        if not os.path.exists(os.path.join(matches_processed_folder, match)):
            os.makedirs(os.path.join(matches_processed_folder, match))

        # files2copy = ['meta_info.json', 'environment.csv', 'replay.json']
        files2copy = ['meta_info.json', 'replay.json']

        for file2copy in files2copy:
            shutil.copy(os.path.join(matches_folder, match, file2copy),
                        os.path.join(matches_processed_folder, match, file2copy))

        with open(os.path.join(matches_folder, match, 'meta_info.json')) as f:
            meta_info = json.load(f)

        match_duration = meta_info['match_duration']

        df_env = pd.read_csv(os.path.join(matches_folder, match, 'environment.csv'), index_col='time')
        df_env.rename(
            columns={
            'Temperature': 'env_temperature',
            'Humidity': 'env_humidity',
            'CO2': 'env_co2',
            'Pressure': 'env_pressure',
            'Altitude': 'altitude',
        }, inplace=True
        )
        df_env.index = pd.TimedeltaIndex(df_env.index, unit='s')
        resample_smooth_save_df(
            df_env,
            os.path.join(matches_processed_folder, match, 'environment.csv'),
            args.resampling_string,
            args.halflife,
            resampling_method=None,
            smooth=False)

        # player_id = 3  # TODO: comment
        for player_id in tqdm.tqdm(player_ids, 'Processing players...'):
            path2player_data_src = os.path.join(matches_folder, match, f'player_{player_id}')
            path2player_data_dst = os.path.join(matches_processed_folder, match, f'player_{player_id}')

            if not os.path.exists(path2player_data_dst):
                os.makedirs(path2player_data_dst)

            if os.path.exists(os.path.join(path2player_data_src, 'player_report.json')):
                shutil.copy(os.path.join(path2player_data_src, 'player_report.json'),
                            os.path.join(path2player_data_dst, 'player_report.json'))

            # data_source = 'gsr'  # TODO: comment
            # data_source = 'emg'  # TODO: comment
            # data_source = 'heart_rate'  # TODO: comment
            # data_source = 'imu_left_hand'  # TODO: comment
            # data_source = 'imu_head'  # TODO: comment
            # data_source = 'keyboard'  # TODO: comment
            # data_source = 'mouse'  # TODO: comment
            # data_source = 'eye_tracker'  # TODO: comment
            # data_source = 'eeg'  # TODO: comment
            # data_source = 'eeg_band_power'  # TODO: comment
            # data_source = 'eeg_metrics'  # TODO: comment
            # data_source = 'face_temperature'  # TODO: comment
            for data_source in tqdm.tqdm(data_sources, 'Processing data sources...'):
                print(f'data_source={data_source}')
                path2data_source = os.path.join(path2player_data_src, f'{data_source}.csv')
                path2save = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'{data_source}.csv')

                if not os.path.exists(path2data_source):
                    if data_source != 'environment':
                        print(f'{path2data_source} doesn\'t exist')

                    continue

                df4data_source = pd.read_csv(path2data_source, index_col='time')
                df4data_source.index = pd.TimedeltaIndex(df4data_source.index, unit='s')

                if data_source == 'gsr':
                    if args.plot:
                        halflives = [0, 1, 5, 30]
                        plot_smoothed_values(df4data_source, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife)

                if data_source == 'emg':
                    reference_levels = df4data_source.median()  # TODO: we use data from the future a little bit
                    df4data_source = df4data_source - reference_levels
                    df4data_source = df4data_source.abs()

                    if args.plot:
                        plt.close()
                        halflives = [5, 10]
                        plot_smoothed_values(df4data_source, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife)

                if data_source == 'heart_rate':
                    if args.plot:
                        halflives = [0, 1, 5, 30]
                        plot_smoothed_values(df4data_source, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife)

                if data_source.startswith('imu') and (data_source != 'imu_head'):
                    df4data_source_part = df4data_source[['linaccel_x', 'linaccel_y', 'linaccel_z',
                                                          'gyro_x', 'gyro_y', 'gyro_z']]

                    if args.plot:
                        halflives = [5, 10]
                        plot_smoothed_values(df4data_source_part, halflives)

                    df4data_source_part = df4data_source_part - df4data_source_part.median()
                    df4data_source_part = df4data_source_part.abs()

                    if args.plot:
                        halflives = [5, 10]
                        plot_smoothed_values(df4data_source_part, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife)

                if data_source == 'imu_head':
                    df_quat = df4data_source[['q0', 'q1', 'q2', 'q3']].diff()
                    mask = df_quat.sum(axis=1) != 0
                    df_quat = df_quat.loc[mask, :]

                    def get_rotvec(quat):
                        rotvec = R.from_quat(quat).as_rotvec()
                        return rotvec

                    rot_data = get_rotvec(df_quat)
                    df_rot = pd.DataFrame(data=rot_data, index=df_quat.index, columns=['rot_x', 'rot_y', 'rot_z'])
                    # df_rot.plot()
                    resample_smooth_save_df(df_rot, path2save, args.resampling_string, args.halflife,
                                            resampling_method='mean')


                if data_source == 'keyboard':
                    df_key_pressed = extract_press_events(df4data_source)

                    print(match, player_id)
                    df_key_pressed.loc[pd.Timedelta(seconds=0), 'buttons_pressed'] = 0
                    # df_key_pressed.loc[pd.Timedelta(seconds=match_duration - 1, milliseconds=999), 'button_pressed'] = 0
                    df_key_pressed.loc[pd.Timedelta(seconds=match_duration), 'buttons_pressed'] = 0
                    df_key_pressed.index = df_key_pressed.index.floor(args.preresampling_string)
                    df_key_pressed = df_key_pressed.resample(args.preresampling_string).sum()

                    if args.plot:
                        halflives = [5, 10]
                        plot_smoothed_values(df_key_pressed, halflives)

                    resample_smooth_save_df(df_key_pressed, path2save, args.resampling_string, args.halflife, resampling_method='sum')

                if data_source == 'mouse':
                    # df4data_source['event'].value_counts()
                    df4data_source['dx'] = [0] + list(np.diff(df4data_source['x']))
                    df4data_source['dy'] = [0] + list(np.diff(df4data_source['y']))
                    df4data_source['mouse_movement'] = (df4data_source['dx'] ** 2 + df4data_source['dy'] ** 2) ** 0.5

                    mask_pressed = df4data_source['event'].isin(['mp'])
                    df4data_source['mouse_clicks'] = 0
                    df4data_source.loc[mask_pressed, 'mouse_clicks'] = 1

                    mask_scroll = df4data_source['event'].isin(['ms'])
                    df4data_source['mouse_scroll'] = 0
                    df4data_source.loc[mask_scroll, 'mouse_scroll'] = 1  # I'm currently ommiting this feature

                    df4data_source = df4data_source[['mouse_movement', 'mouse_clicks']]
                    # TODO: I might be dropping important information here (when 2 events occur at the same time but in different rows)
                    df4data_source = df4data_source.reset_index().drop_duplicates(['time']).set_index(['time'])  # Dropping index duplicates
                    df4data_source.loc[pd.Timedelta(seconds=0), ['mouse_movement', 'mouse_clicks']] = (0, 0)
                    # df4data_source.loc[pd.Timedelta(seconds=match_duration - 1, milliseconds=999), ['mouse_movement', 'mouse_clicks']] = 0
                    df4data_source.loc[pd.Timedelta(seconds=match_duration - 1), ['mouse_movement', 'mouse_clicks']] = 0
                    df4data_source.index = df4data_source.index.floor(args.preresampling_string)
                    df4data_source = df4data_source.resample(args.preresampling_string).sum()

                    if args.plot:
                        # halflives = [0, 1, 5, 30]
                        halflives = [0, 1, 5, 10]
                        plot_smoothed_values(df4data_source, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife, resampling_method='sum')

                if data_source == 'eye_tracker':
                    mask_validity = (df4data_source['left_gaze_origin_validity'] == 1) & \
                                    (df4data_source['right_gaze_origin_validity'] == 1)
                    df4data_source = df4data_source.loc[mask_validity, ['gaze_x', 'gaze_y', 'pupil_diameter']]

                    df4data_source['gaze_dx'] = [0] + list(np.diff(df4data_source['gaze_x']))
                    df4data_source['gaze_dy'] = [0] + list(np.diff(df4data_source['gaze_y']))
                    df4data_source['gaze_movement'] = (df4data_source['gaze_dx'] ** 2 + df4data_source['gaze_dx'] ** 2) ** 0.5

                    df4data_source.index = df4data_source.index.floor(args.preresampling_string)
                    df4data_source = df4data_source.resample(args.preresampling_string).apply({
                        'gaze_movement': np.sum,
                        'pupil_diameter': np.mean,
                    })

                    if args.plot:
                        halflives = [0, 5, 10]
                        plot_smoothed_values(df4data_source, halflives)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife, resampling_method='mean')

                if data_source == 'EEG':
                    raise ValueError(f'data_source cannot be equal to {data_source}')

                if data_source == 'eeg_band_power':
                    values_min, values_max = np.percentile(df4data_source, [5, 95], axis=0)
                    df4data_source = df4data_source.clip(values_min, values_max, axis=1)
                    plt.close()

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife,
                                            resampling_method='mean')

                if data_source == 'eeg_metrics':
                    df4data_source = df4data_source[['Engagement', 'Excitement',# 'Long term excitement',
                                                     'Stress', 'Relaxation', 'Interest', 'Focus']]

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife,
                                            resampling_method='mean')

                if data_source == 'face_temperature':
                    df4data_source['thermal_data'] = df4data_source['thermal_data'].apply(lambda x: json.loads(x))
                    df4data_source['thermal_data'] = df4data_source['thermal_data'].apply(lambda x: np.percentile(x, 95))
                    path2save = os.path.join(os.path.dirname(path2save), 'facial_skin_temperature.csv')
                    df4data_source.rename(columns={'thermal_data': 'facial_skin_temperature'}, inplace=True)

                    resample_smooth_save_df(df4data_source, path2save, args.resampling_string, args.halflife, resampling_method='mean')

                if data_source == 'particle_sensor':
                    df_spo2 = get_spo2_df(df4data_source)
                    path2save = os.path.join(os.path.dirname(path2save), 'spo2.csv')

                    resample_smooth_save_df(df_spo2, path2save, args.resampling_string, args.halflife)


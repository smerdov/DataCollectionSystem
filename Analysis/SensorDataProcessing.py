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

parser = argparse.ArgumentParser()
# parser.add_argument('--smoothing-window', default=5, type=float)
parser.add_argument('--halflife', default=10, type=float)
# parser.add_argument('--resample-timestep', default=100, type=int, help='Timestep for resampling')
# parser.add_argument('--resample-timestep-units', default='ms', type=str, help='Units for resampling timestep')
parser.add_argument('--resample-string', default='100ms', type=str, help='Timestep for resampling')
parser.add_argument('--plot', action='store_true')
parser.add_argument('--halflifes-in-window', default=5, type=float)
# args = parser.parse_args(['--halflife', '10'])
# args = parser.parse_args([])
args = parser.parse_args()

matches_folder = os.path.join(dataset_folder, 'matches')
matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')
matches = [match for match in os.listdir(matches_folder) if match.startswith('match')]
one_second_unit = pd.Timedelta(seconds=1)
# resample_string = f'{args.resample_timestep}ms'
# resample_string = f'{args.resample_timestep}{args.resample_timestep_units}'
resample_string = args.resample_string
print(f'Resampling with {resample_string}')

def time_ewa(series, halflife):
    # print(series, halflife)
    # n_points = len(df)
    time_diffs = series.index / pd.Timedelta(seconds=1)
    time_diffs = time_diffs.values
    # time_diffs = (time_diffs - time_diffs.max())
    time_diffs = time_diffs.max() - time_diffs
    # time_diffs = time_diffs /
    # time_diffs = time_diffs.values
    # Folmula from https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
    alpha = 1 - np.exp(np.log(0.5) / halflife)
    weights = (1 - alpha) **  time_diffs
    weights = weights / weights.sum()
    # print(weights)
    result = (series * weights).sum()

    return result


def smooth_df(df, halflife):
    window_size = pd.Timedelta(seconds=halflife * args.halflifes_in_window)
    df_smoothed = df.rolling(window=window_size).apply(lambda x: time_ewa(x, halflife))

    return df_smoothed


def plot_smoothed_values(df, halflives):
    plt.close()
    n_features = len(df.columns)
    fig, ax = plt.subplots(nrows=n_features, ncols=1, figsize=(12, 6 * n_features), sharex=True, squeeze=False)
    # for halflife in [0, 1, 5, 30]:
    for halflife in tqdm.tqdm(halflives):
        if halflife == 0:
            df_smoothed = df
        else:
            # window_size = pd.Timedelta(seconds=halflife * args.halflifes_in_window)
            # df_smoothed = df.rolling(window=window_size).apply(
            #     lambda x: time_ewa(x, halflife))
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
    # df = df.copy()
    # df.index = df.index / one_second_unit

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
                                               columns=['time', 'button_pressed'])
    df_key_pressed.set_index(['time'], inplace=True)

    return df_key_pressed

def save_df(df, path2save):
    df.index = df.index / one_second_unit
    df.to_csv(path2save)

# data_sources = ['keyboard']
# data_sources = []

if __name__ == '__main__':
    # match = 'match_0'  # TODO: comment
    for match in tqdm.tqdm(matches, 'Processing matches...'):
        if not os.path.exists(os.path.join(matches_processed_folder, match)):
            os.makedirs(os.path.join(matches_processed_folder, match))

        shutil.copy(os.path.join(matches_folder, match, 'meta_info.json'),
                    os.path.join(matches_processed_folder, match, 'meta_info.json'))
        # player_id = 0  # TODO: comment
        for player_id in tqdm.tqdm(player_ids, 'Processing players...'):
            path2player_data_src = os.path.join(matches_folder, match, f'player_{player_id}')
            # path2player_data_dst = os.path.join(matches_processed_folder, match, f'player_{player_id}')

            # pd.TimedeltaIndex(pd.Timedelta(seconds=0), unit='s', freq=resample_string)

            # data_source = 'gsr'  # TODO: comment
            # data_source = 'emg'  # TODO: comment
            # data_source = 'heart_rate'  # TODO: comment
            # data_source = 'imu_left_hand'  # TODO: comment
            # data_source = 'keyboard'  # TODO: comment
            # data_source = 'mouse'  # TODO: comment
            # data_source = 'eye_tracker'  # TODO: comment
            for data_source in tqdm.tqdm(data_sources, 'Processing data sources...'):
                print(f'data_source={data_source}')
                path2data_source = os.path.join(path2player_data_src, f'{data_source}.csv')
                path2save = os.path.join(matches_processed_folder, match, f'player_{player_id}', f'{data_source}.csv')

                if not os.path.exists(path2data_source):
                    print(f'{path2data_source} doesn\'t exist')
                    continue

                df4data_source = pd.read_csv(path2data_source, index_col='time')
                df4data_source.index = pd.TimedeltaIndex(df4data_source.index, unit='s')

                if data_source == 'gsr':
                    if args.plot:
                        halflives = [0, 1, 5, 30]
                        plot_smoothed_values(df4data_source, halflives)

                    # halflife = 10
                    # new_index = pd.TimedeltaIndex([df4data_source.index[0].floor(resample_string)] + list(df4data_source.index[1:].values))
                    # df4data_source.index = new_index
                    df4data_source.index = df4data_source.index.floor(resample_string)
                    df4data_source = df4data_source.resample(resample_string).mean()
                    df_smoothed = smooth_df(df4data_source, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source == 'emg':

                    reference_levels = df4data_source.median()  # TODO: we use data from the future a little bit
                    df4data_source = df4data_source - reference_levels
                    df4data_source = df4data_source.abs()

                    if args.plot:
                        plt.close()
                        # df4data_source.ewm(span=100).mean().plot()
                        # halflives = [0, 1, 5, 30]
                        halflives = [5, 10]
                        plot_smoothed_values(df4data_source, halflives)

                    # halflife = 10
                    df4data_source.index = df4data_source.index.floor(resample_string)
                    df4data_source = df4data_source.resample(resample_string).mean()
                    df_smoothed = smooth_df(df4data_source, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source == 'heart_rate':
                    if args.plot:
                        halflives = [0, 1, 5, 30]
                        plot_smoothed_values(df4data_source, halflives)

                    # halflife = 5
                    df4data_source.index = df4data_source.index.floor(resample_string)
                    df4data_source = df4data_source.resample(resample_string).mean()
                    df_smoothed = smooth_df(df4data_source, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source.startswith('imu'):
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

                    # halflife = 10
                    df4data_source_part.index = df4data_source_part.index.floor(resample_string)
                    df4data_source_part = df4data_source_part.resample(resample_string).mean()
                    df_smoothed = smooth_df(df4data_source_part, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source == 'keyboard':
                    df4data_source['event'].value_counts()
                    # df4data_source.head(60)

                    df_key_pressed = extract_press_events(df4data_source)

                    ### Summarizing key presses
                    window_size = 10
                    df_key_pressed.index = df_key_pressed.index.floor(resample_string)
                    df_key_pressed = df_key_pressed.resample(resample_string).sum()
                    df_key_pressed_sum = df_key_pressed.rolling(f'{window_size}s').sum()

                    if args.plot:
                        halflives = [5, 10]
                        plot_smoothed_values(df_key_pressed_sum, halflives)

                    # halflife = 10
                    # df_key_pressed_sum = df_key_pressed_sum.resample(resample_string).mean()

                    df_smoothed = smooth_df(df_key_pressed_sum, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source == 'mouse':
                    df4data_source['event'].value_counts()

                    df4data_source['dx'] = [0] + list(np.diff(df4data_source['x']))
                    df4data_source['dy'] = [0] + list(np.diff(df4data_source['y']))
                    df4data_source['mouse_movement'] = (df4data_source['dx'] ** 2 + df4data_source['dy'] ** 2) ** 0.5

                    mask_pressed = df4data_source['event'].isin(['mp'])
                    df4data_source['mouse_pressed'] = 0
                    df4data_source.loc[mask_pressed, 'mouse_pressed'] = 1

                    mask_scroll = df4data_source['event'].isin(['ms'])
                    df4data_source['mouse_scroll'] = 0
                    df4data_source.loc[mask_scroll, 'mouse_scroll'] = 1  # I'm currently ommiting this feature

                    window_size = 10
                    # df_agg = df4data_source[['mouse_movement', 'mouse_pressed']].rolling(f'{window_size}s').sum()
                    df_agg = df4data_source[['mouse_movement', 'mouse_pressed']].resample(resample_string).sum()
                    df_agg = df_agg.rolling(f'{window_size}s').sum()

                    if args.plot:
                        # halflives = [0, 1, 5, 30]
                        halflives = [0, 1, 5, 10]
                        plot_smoothed_values(df_agg, halflives)

                    # halflife = 10
                    # new_index = pd.TimedeltaIndex([df_agg.index[0].floor(resample_string)] + list(df_agg.index[1:].values))
                    # df_agg.index = new_index
                    df_agg.index = df_agg.index.floor(resample_string)
                    df_smoothed = smooth_df(df_agg, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)

                if data_source == 'eye_tracker':
                    mask_validity = (df4data_source['left_gaze_origin_validity'] == 1) & \
                                    (df4data_source['right_gaze_origin_validity'] == 1)
                    df4data_source = df4data_source.loc[mask_validity, ['gaze_x', 'gaze_y', 'pupil_diameter']]

                    # df4data_source['left_gaze_origin_validity'].value_counts()
                    # df4data_source['left_pupil_validity'].value_counts()
                    # df4data_source['right_gaze_origin_validity'].value_counts()
                    # df4data_source['right_pupil_validity'].value_counts()

                    df4data_source['gaze_dx'] = [0] + list(np.diff(df4data_source['gaze_x']))
                    df4data_source['gaze_dy'] = [0] + list(np.diff(df4data_source['gaze_y']))
                    df4data_source['gaze_movement'] = (df4data_source['gaze_dx'] ** 2 + df4data_source['gaze_dx'] ** 2) ** 0.5

                    window_size = 10
                    df4data_source['gaze_movement'] = df4data_source['gaze_movement'].rolling(f'{window_size}s').sum()
                    df_agg = df4data_source[['gaze_movement', 'pupil_diameter']].resample(resample_string).mean()

                    if args.plot:
                        halflives = [0, 5, 10]
                        plot_smoothed_values(df_agg, halflives)

                    # halflife = 10
                    df_agg.index = df_agg.index.floor(resample_string)
                    df_smoothed = smooth_df(df_agg, args.halflife)
                    # df_smoothed.to_csv(path2save)
                    save_df(df_smoothed, path2save)








































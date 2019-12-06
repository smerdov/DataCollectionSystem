import joblib
# import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from config import *
from utils import get_intervals_from_moments, EventIntervals
import argparse

plt.interactive(False)

date = '2019-11-15'
# data_path = f'{dataset_folder}{date}/'
data_path_processed = f'{dataset_folder}{date}_processed/'

# parser = argparse.ArgumentParser()
# parser.add_argument('--date', default='', type=str)
# args = parser.parse_args()
# date = args.date

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


# data_dict = joblib.load(data_folder + 'data_dict')
# matches_dict = joblib.load(data_folder + 'matches_dict')
# replays_dict = joblib.load(data_folder + 'replays_dict')

# del data_dict[0]['eye_tracker']
# del data_dict[1]['eye_tracker']

interval_start = -1
interval_end = 1


def square_plot(df, columns2plot, timecol='Timestamp', suffix='last'):
    n_plots = len(columns2plot)
    square_size = int(np.ceil(n_plots ** 0.5))
    time_data = df[timecol]
    fig, ax = plt.subplots(square_size, square_size, sharex=False, sharey=False, figsize=(20, 20))
    fig.suptitle(suffix)

    for n_plot, (n_row, n_col) in enumerate(itertools.product(range(square_size), range(square_size))):
        if n_plot >= n_plots:
            continue

        colname = columns2plot[n_plot]
        ax[n_row, n_col].plot(time_data, df[colname])
        ax[n_row, n_col].set_title(colname)

    fig.tight_layout()
    fig.savefig(f'{pic_folder}square_plot_{suffix}.png')

# data_sources = [f'arduino_{i}' for i in range(3)] + ['eye_tracker']

data_sources_columns2plot = { # If None, then plot all columns
    'arduino_0': ['gsr', 'emg_0', 'emg_1', 'linaccel_x_0', 'linaccel_y_1', 'linaccel_z_0',
                  'linaccel_x_1', 'linaccel_y_1', 'linaccel_z_1'],
    'arduino_1': ['linaccel_x_0', 'linaccel_y_1', 'linaccel_z_0',
                  'linaccel_x_1', 'linaccel_y_1', 'linaccel_z_1',
                  'gyro_x_0', 'gyro_y_0', 'gyro_z_0',
                  'gyro_x_1', 'gyro_y_1', 'gyro_z_1',
                  ],
    'arduino_2': ['irValue', 'redValue'],
    'eye_tracker': ['gaze_x', 'gaze_y', 'pupil_diameter'],
    'polar_heart_rate': ['heart_rate'],
}

n_plots = sum([len(value) for value in data_sources_columns2plot.values()])

n_cols = np.ceil(np.sqrt(n_plots)).astype(int)
n_rows = (n_plots - 1) // n_cols + 1

game_names = sorted(os.listdir(data_path_processed))
game_names = [game_name for game_name in game_names if game_name.startswith('game')]
player_ids = ['0', '1', '2', '3', '4']















# Visualization of many sensors for each player

for game_name in game_names:
    # for match_id, match_dict in matches_dict.items():
    # for player_id, match_dict4player in match_dict.items():

    for player_id in player_ids:
        # match_dict4player = match_dict[player_id]

        fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(50, 25), squeeze=False, sharex=True)
        n_plot = 0

        for data_source in data_sources:
            df2plot = match_dict4player['sensors'][data_source]
            # # df = data_dict4player[data_source]
            # df2plot.index = pd.to_datetime(df2plot.index)
            # df2plot = df2plot.resample('1s').mean()

            if data_source in data_sources_columns2plot:
                columns2plot = data_sources_columns2plot[data_source]
            else:
                columns2plot = df2plot.columns

            for column in columns2plot:
                print(f'column {column} done')
                data2plot = df2plot.loc[:, column]
                data2plot.index = data2plot.index.total_seconds()

                n_row = n_plot // n_cols
                n_col = n_plot % n_cols
                ax[n_row, n_col].plot(data2plot, color='black', alpha=0.5)
                title = column
                if data_source == 'arduino_1':  # chair
                    title = 'chair ' + title
                ax[n_row, n_col].set_title(title)
                if n_row == n_rows - 1:
                    ax[n_row, n_col].set_xlabel('Time, s')

                n_plot += 1

                # intervals_dict = {}
                event_intervals_list = []
                events_colors_list = [('kill', 'green'), ('death', 'red'), ('assist', 'blue')]
                # for event_type in ['kill', 'death', 'assist']:
                for event_type, color in events_colors_list:
                    # intervals_dict[event_type] = get_intervals_from_moments(match_dict4player['events'][f'{event_type}_times'],
                    #                                                         interval_start=interval_start, interval_end=interval_end)
                    intervals_list = get_intervals_from_moments(match_dict4player['events'][f'{event_type}_times'],
                                                                            interval_start=interval_start, interval_end=interval_end)

                    event_intervals4event_type = EventIntervals(intervals_list=intervals_list, label=event_type, color=color)
                    event_intervals_list.append(event_intervals4event_type)

                for event_intervals in event_intervals_list:

                    # intervals_list = event_intervals.intervals_list
                    event_label = event_intervals.label
                    color = event_intervals.color
                    # mask_interval_list = get_mask_intervals(times, intervals_list=intervals_list)
                    mask_interval_list = event_intervals.get_mask_intervals(data2plot.index)

                    for mask_interval in mask_interval_list:
                        # times_with_mask = data2plot.index[mask_interval]
                        data2plot_with_mask = data2plot.loc[mask_interval]
                        ax[n_row, n_col].plot(
                            # times_with_mask,
                            data2plot_with_mask,
                            # label=event_label,
                            color=color,
                            alpha=0.8,
                            # linewidth=2,
                        )

                    ax[n_row, n_col].plot([], [], label=event_label, color=color)

                ax[n_row, n_col].legend(loc='upper right')

        fig.suptitle(f'Match {match_id}, Player {player_id}')
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        fig.savefig(f'{pic_folder}match_{match_id}_player_{player_id}.png')







# square_plot(df, columns2plot=df.columns[1:], suffix=arduino_name)









# df = pd.read_csv(data_path + filename, sep=',', skiprows=corrupted_rows_list)
#
# df['Timestamp'] = pd.to_datetime(df['Timestamp']).apply(lambda x: x.timestamp())
#
# df['Timestamp'] = df['Timestamp'] - df['Timestamp'][0]
# timediffs = np.diff(df['Timestamp'].values)
#
# plt.plot(df['Timestamp'])
# plt.title('Time after start')
# plt.savefig(pic_folder + 'time_after_start.png')
# plt.close()
#
# plt.plot(timediffs)
# timediff_mean = timediffs.mean()
# sampling_rate = 1 / timediff_mean
# plt.title(f'Time after previous record. Sampling rate = {round(sampling_rate, 2)} Hz')
# plt.plot(timediff_mean, label='mean')
# plt.savefig(pic_folder + 'time_diffs.png')
# plt.close()


# n = 81416 - 2
# for i in range(20):
#     print(len(df.iloc[n + i,0].split(',')))
#
#
# print(len(df.iloc[n,0].split(',')))
#
#
# df.iloc[n,0].split(',')
# str(df.columns[0]).split(',')
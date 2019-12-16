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
player_ids = ['player_0', 'player_1', 'player_2', 'player_3', 'player_4']
# data_path = f'{dataset_folder}{date}/'
# data_path_processed = f'{dataset_folder}{date}_processed/'
data_dict = joblib.load('../Data/data_dict')

plot_individual = False
plot_team = True
# parser = argparse.ArgumentParser()
# parser.add_argument('--date', default='', type=str)
# args = parser.parse_args()
# date = args.date

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

team_names_dict = {
    '2019-11-15': 'amateurs',
    '2019-11-22': 'pros',
}

events_colors_list = [('kill', 'green'), ('death', 'red'), ('assist', 'blue')]
# column2smooth = ['heart_rate', 'gsr', 'pupil_diameter']

smooth_dict = {
    'heart_rate': 200,
    'gsr': 5000,
    'pupil_diameter': 25000,
}



# data_dict = joblib.load(data_folder + 'data_dict')
# matches_dict = joblib.load(data_folder + 'matches_dict')
# replays_dict = joblib.load(data_folder + 'replays_dict')

# del data_dict[0]['eye_tracker']
# del data_dict[1]['eye_tracker']

interval_start = -2
interval_end = 2


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

data_sources_columns2plot_individual = { # If None, then plot all columns
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
}

data_sources_columns2plot_team = { # If None, then plot all columns
    'arduino_0': ['gsr', 'emg_0', 'linaccel_x_0'], #, 'linaccel_x_1'],
    'arduino_1': ['linaccel_y_0', 'gyro_z_0'],
    'eye_tracker': ['pupil_diameter'],
    'polar_heart_rate': ['heart_rate'],
}

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
        for column in columns:
            data_source_column2number_dict[(data_source, column)] = number
            number += 1

    return n_plots, n_cols, n_rows, data_source_column2number_dict



# n_plots_individual = sum([len(value) for value in data_sources_columns2plot_individual.values()])
n_plots_individual, n_cols_individual, n_rows_individual, data_source_column2number_dict_individual = get_plot_params(
    data_sources_columns2plot_individual,
)
n_plots_team, n_cols_team, n_rows_team, data_source_column2number_dict_team = get_plot_params(
    data_sources_columns2plot_team,
    n_rows=len(player_ids),
    n_players=len(player_ids),
)


def plot_content(fig, ax, data_sources_columns2plot, data_source_column2number_dict, n_cols, n_rows,
                 event_intervals_list, n_player=None, column2smooth=column2smooth):
    for data_source, columns2plot in data_sources_columns2plot.items():
        if data_source not in player_dict:
            continue

        df2plot = player_dict[data_source]

        if data_source in data_sources_columns2plot:
            columns2plot = data_sources_columns2plot[data_source]
        else:
            columns2plot = df2plot.columns

        for column in columns2plot:
            print(f'column {column} done')
            data2plot = df2plot.loc[:, column]

            data2plot.index = pd.TimedeltaIndex(data2plot.index, unit='s')
            if column in smooth_dict:
                # data2plot = data2plot.resample('30s').mean()
                # data2plot = data2plot.loc[data2plot.notnull().values]
                # print(data2plot)
                # data2plot = data2plot.resample('s') # .pad()
                # data2plot = data2plot.asfreq('1s')
                data2plot = data2plot.ewm(span=smooth_dict[column]).mean()
                # print(data2plot)
                # data2plot = data2plot.interpolate(method='cubic')
            data2plot.index = data2plot.index.total_seconds()

            n_plot = data_source_column2number_dict[(data_source, column)]

            n_row = n_plot // n_cols
            if n_player is not None:
                n_row += n_player  # For team plots
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
            # for event_type in ['kill', 'death', 'assist']:

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

            if n_row == 0:
                ax[n_row, n_col].legend(loc='upper right') # , fontsize=5)

def savefig(fig, suptitle, filename):
    fig.suptitle(suptitle)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(filename)



# Visualization of many sensors for each player

for date, date_dict in data_dict.items():
    team_name = team_names_dict[date]

    for game_name, game_dict in date_dict.items():
        environment = game_dict['environment']
        # events = game_dict['events']

        if plot_team:
            fig_team, ax_team = plt.subplots(nrows=n_rows_team, ncols=n_cols_team, figsize=(26, 13), squeeze=False, sharex=True)

            for player_id in player_ids:
                player_id_int = int(player_id[-1])
                ax_team[player_id_int, 0].set_ylabel(player_id)


        for player_id in player_ids:
            if player_id not in game_dict:
                continue

            player_dict = game_dict[player_id]
            player_id_int = int(player_id[-1])

            event_intervals_list = []

            for event_type, color in events_colors_list:
                # intervals_dict[event_type] = get_intervals_from_moments(match_dict4player['events'][f'{event_type}_times'],
                #                                                         interval_start=interval_start, interval_end=interval_end)
                events_dict4player = game_dict['events'][f'events_{player_id}']
                intervals_list = get_intervals_from_moments(events_dict4player[f'{event_type}_times'],
                                                            interval_start=interval_start, interval_end=interval_end)

                event_intervals4event_type = EventIntervals(intervals_list=intervals_list, label=event_type,
                                                            color=color)
                event_intervals_list.append(event_intervals4event_type)


            if plot_individual:
                fig_individual, ax_individual = plt.subplots(nrows=n_rows_individual, ncols=n_cols_individual, figsize=(50, 25), squeeze=False, sharex=True)
                # n_plot_individual = 0

                plot_content(
                    fig_individual,
                    ax_individual,
                    data_sources_columns2plot_individual,
                    data_source_column2number_dict_individual,
                    n_cols_individual,
                    n_rows_individual,
                    event_intervals_list,
                )

                savefig(
                    fig_individual,
                    suptitle=f'{team_name}, {date}, match {game_name}, player {player_id}',
                    filename=f'{pic_folder}{team_name}_{date}_match_{game_name}_player_{player_id}.png',
                )

            if plot_team:
                plot_content(
                    fig_team,
                    ax_team,
                    data_sources_columns2plot_team,
                    data_source_column2number_dict_team,
                    n_cols_team,
                    n_rows_team,
                    event_intervals_list,
                    n_player=player_id_int,
                )

        if plot_team:
            savefig(
                fig_team,
                suptitle = f'{team_name}, {date}, match {game_name}',
                filename = f'{pic_folder}{team_name}_{date}_match_{game_name}.png',
            )


                # for data_source, columns2plot in data_sources_columns2plot_individual.items():
                #     if data_source not in player_dict:
                #         continue
                #
                #     df2plot = player_dict[data_source]
                #
                #     if data_source in data_sources_columns2plot_individual:
                #         columns2plot = data_sources_columns2plot_individual[data_source]
                #     else:
                #         columns2plot = df2plot.columns
                #
                #     for column in columns2plot:
                #         print(f'column {column} done')
                #         data2plot = df2plot.loc[:, column]
                #         # data2plot.index = data2plot.index.total_seconds()
                #         n_plot_individual = data_source_column2number_dict_individual[(data_source, column)]
                #
                #         n_row = n_plot_individual // n_cols_individual
                #         n_col = n_plot_individual % n_cols_individual
                #         ax_individual[n_row, n_col].plot(data2plot, color='black', alpha=0.5)
                #         title = column
                #         if data_source == 'arduino_1':  # chair
                #             title = 'chair ' + title
                #         ax_individual[n_row, n_col].set_title(title)
                #         if n_row == n_rows_individual - 1:
                #             ax_individual[n_row, n_col].set_xlabel('Time, s')
                #
                #         n_plot_individual += 1
                #
                #         # intervals_dict = {}
                #         # for event_type in ['kill', 'death', 'assist']:
                #
                #         for event_intervals in event_intervals_list:
                #
                #             # intervals_list = event_intervals.intervals_list
                #             event_label = event_intervals.label
                #             color = event_intervals.color
                #             # mask_interval_list = get_mask_intervals(times, intervals_list=intervals_list)
                #             mask_interval_list = event_intervals.get_mask_intervals(data2plot.index)
                #
                #             for mask_interval in mask_interval_list:
                #                 # times_with_mask = data2plot.index[mask_interval]
                #                 data2plot_with_mask = data2plot.loc[mask_interval]
                #                 ax_individual[n_row, n_col].plot(
                #                     # times_with_mask,
                #                     data2plot_with_mask,
                #                     # label=event_label,
                #                     color=color,
                #                     alpha=0.8,
                #                     # linewidth=2,
                #                 )
                #
                #             ax_individual[n_row, n_col].plot([], [], label=event_label, color=color)
                #
                #         ax_individual[n_row, n_col].legend(loc='upper right')
                #
                # fig_individual.suptitle(f'{date} Match {game_name}, Player {player_id}')
                # fig_individual.tight_layout(rect=[0, 0, 1, 0.97])
                # fig_individual.savefig(f'{pic_folder}{date}_match_{game_name}_player_{player_id}.png')


            # if plot_team:
            #     for data_source, columns2plot in data_sources_columns2plot_team.items():
            #         if data_source not in player_dict:
            #             continue
            #
            #         df2plot = player_dict[data_source]
            #
            #         if data_source in data_sources_columns2plot_team:
            #             columns2plot = data_sources_columns2plot_team[data_source]
            #         else:
            #             columns2plot = df2plot.columns









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
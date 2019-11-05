import joblib
# import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from config import *


data_dict = joblib.load(data_folder + 'data_dict')


# del data_dict[0]['eye_tracker']
# del data_dict[1]['eye_tracker']


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

data_sources = [f'arduino_{i}' for i in range(3)] + ['eye_tracker']

data_sources_columns2plot = {
    'arduino_0': list(data_dict[0]['arduino_0'].columns),
    'arduino_1': list(data_dict[0]['arduino_1'].columns),
    'arduino_2': list(data_dict[0]['arduino_2'].columns),
    'eye_tracker': ['gaze_x', 'gaze_y', 'pupil_diameter'],
}

n_plots = sum([len(value) for value in data_sources_columns2plot.values()])

n_cols = np.ceil(np.sqrt(n_plots)).astype(int)
n_rows = (n_plots - 1) // n_cols + 1

for player_id, data_dict4player in data_dict.items():
    fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(50, 25), squeeze=False, sharex=True)
    n_plot = 0

    for data_source in data_sources:
        df2plot = data_dict4player[data_source]
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

            n_row = n_plot // n_cols
            n_col = n_plot % n_cols
            ax[n_row, n_col].plot(data2plot)

            ax[n_row, n_col].set_title(column)

            n_plot += 1

    fig.tight_layout()
    fig.savefig(f'{pic_folder}player_{player_id}')









square_plot(df, columns2plot=df.columns[1:], suffix=arduino_name)









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
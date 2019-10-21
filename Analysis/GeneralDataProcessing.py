import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime

plt.interactive(True)

pd.options.display.max_columns = 15
data_folder = '../Dataset/'
pic_folder = '../Pictures/'
day_num = 0
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



def concat_files4data_source(filenames, index_col):
    df_result = pd.DataFrame()
    for filename in filenames:
        df_addition = pd.read_csv(data_path + filename)
        df_addition.set_index(index_col, inplace=True)
        df_result = pd.concat([df_result, df_addition])

    return df_result

data_dict = {}

for player_id in [0, 1]:
    player_data_dict = {}

    data_path = f'{data_folder}day_{day_num}/player_{player_id}/'
    filenames = sorted(os.listdir(data_path))
    for arduino_id in [0, 1, 2]:
        # df4arduino = pd.DataFrame()
        filename_prefix = f'arduino_{arduino_id}'
        filenames_with_prefix = [filename for filename in filenames if filename.startswith(filename_prefix)]
        df_arduino = concat_files4data_source(filenames_with_prefix, index_col='Timestamp')
        # for filename in filenames_with_prefix:
        #     df_addition = pd.read_csv(data_path + filename)
        #     df_addition.set_index('Timestamp', inplace=True)
        #     df4arduino = pd.concat([df4arduino, df_addition])

        player_data_dict[f'arduino_{arduino_id}'] = df_arduino

    ### Eye tracker
    filenames_with_prefix = [filename for filename in filenames if filename.startswith('tobii')]
    df_eyetracker = concat_files4data_source(filenames_with_prefix, index_col='#timestamp')
    player_data_dict['eye_tracker'] = df_eyetracker

    data_dict[player_id] = player_data_dict

# pd.to_datetime(data_dict[1]['eye_tracker'].index / 1000, unit='s')  # It's a bullshit!

joblib.dump(data_dict, '../Data/data_dict')







# corrupted_rows_list = [81415, 118021, 127353, 138037, 297856, 301348]
# corrupted_rows_list = [14051, 70047, 117133] # , 138037, 297856, 301348]
# corrupted_rows_list = [10569, ]
corrupted_rows_list = []
df = pd.read_csv(data_path + filename, sep=',', skiprows=corrupted_rows_list)

df['Timestamp'] = pd.to_datetime(df['Timestamp']).apply(lambda x: x.timestamp())

df['Timestamp'] = df['Timestamp'] - df['Timestamp'][0]
timediffs = np.diff(df['Timestamp'].values)

plt.plot(df['Timestamp'])
plt.title('Time after start')
plt.savefig(pic_folder + 'time_after_start.png')
plt.close()

plt.plot(timediffs)
timediff_mean = timediffs.mean()
sampling_rate = 1 / timediff_mean
plt.title(f'Time after previous record. Sampling rate = {round(sampling_rate, 2)} Hz')
plt.plot(timediff_mean, label='mean')
plt.savefig(pic_folder + 'time_diffs.png')
plt.close()


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


square_plot(df, columns2plot=df.columns[1:], suffix=arduino_name)























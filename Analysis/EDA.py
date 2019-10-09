import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools

plt.interactive(True)


data_folder = '../Data/'
pic_folder = '../Pictures/'
player_id = 1
arduino_id = 0
if arduino_id == 0:
    arduino_name = 'body'
elif arduino_id == 1:
    arduino_name = 'chair'
else:
    arduino_name = 'some_arduino'


data_path = f'{data_folder}player_{player_id}/arduino_{arduino_id}_data/'

# file_datetime = '2019-10-07-14-27-10'
# filename = f'arduino_{arduino_id}_playerID_{player_id}_{file_datetime}.csv'
# filename = 'arduino_0_playerID_1_2019-10-07-14-27-10.csv'
filename = sorted(os.listdir(data_path))[-1]  # Last recording

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























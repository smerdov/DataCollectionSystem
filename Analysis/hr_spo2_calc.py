from config import *
from hr_spo2_lib import calc_hr_and_spo2
import numpy as np
import os


path2df = os.path.join(dataset_folder, '2019-12-17_processed', 'game_4', 'player_0', 'particle_sensor.csv')

df = pd.read_csv(path2df, index_col=['time'])

# plt.close()
# plt.plot(ir_values / ir_values.mean())
# plt.plot(red_values / red_values.mean())
# print(result)


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
                'timestamp': timestamp,
            }
            entries.append(entry)

    df_spo2 = pd.DataFrame(entries)
    df_spo2.set_index('timestamp', inplace=True)

    return df_spo2


df_spo2 = get_spo2_df(df)
plt.close()
plt.plot(df_spo2)


# plt.plot(df['ir_value'], df['red_value'])
# calc_hr_and_spo2(10**6**np.sin(np.arange(10)), np.cos(np.arange(10))*10**7)


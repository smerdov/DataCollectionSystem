import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *

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

    data_path = f'{dataset_folder}day_{day_num}/player_{player_id}/'
    filenames = sorted(os.listdir(data_path))
    for arduino_id in [0, 1, 2]:
        # df4arduino = pd.DataFrame()
        filename_prefix = f'arduino_{arduino_id}'
        filenames_with_prefix = [filename for filename in filenames if filename.startswith(filename_prefix)]
        df_arduino = concat_files4data_source(filenames_with_prefix, index_col='Timestamp')
        df_arduino.index = pd.to_datetime(df_arduino.index)
        df_arduino = df_arduino.resample('1s').mean()
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
































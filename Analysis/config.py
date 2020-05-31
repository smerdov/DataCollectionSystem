import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, accuracy_score, average_precision_score, precision_recall_curve, precision_score, recall_score, log_loss
import torch.nn as nn
import torch

dataset_folder = '../Dataset/'
data_folder = '../Data/'
pic_folder = '../Pictures/'
# API_KEY = 'RGAPI-3e4ae736-1151-4541-9c45-c33593d25987'
API_KEY = 'RGAPI-43efbdb5-43b8-4867-bac6-93180de95bf8'

plt.interactive(True)
pd.options.display.max_columns = 15

player_ids = list(range(5))

criterion = nn.BCELoss()
# criterion = nn.BCEWithLogitsLoss(pos_weight=torch.Tensor([1, 0.1]))
scorers_dict = {
    'auc': roc_auc_score,
    'ap': average_precision_score,
    'ap_neg': average_precision_score,
    'precision': precision_score,
    'recall': recall_score,
    'precision_neg': precision_score,
    'recall_neg': recall_score,
    'acc': accuracy_score,
    'log_loss': log_loss}

data_sources = [
    'emg',
    'eye_tracker',
    'gsr',
    'heart_rate',
    'imu_chair_back',
    'imu_chair_seat',
    'imu_left_hand',
    'imu_right_hand',
    'imu_head',
    'keyboard',
    'mouse',
    'particle_sensor',
    'face_temperature',
    # 'eeg',
    'eeg_band_power',
    # 'eeg_device_info',
    'eeg_metrics',
]

summoner_name2player_id_dicts = {
    'pros': {
        'Reiign': 0,
        'Biotom': 1,
        'TUK hi im ballat': 2,
        'Ebermann': 2,
        'TUK Psytolos': 3,
        'TUK Trannas': 4,
        },
    'amateurs': {
        'oi mori  ': 0,
        'TheSilverTusk': 1,
        'Fillps': 2,
        'ZdadrDeM': 3,
        'Supersaiyarunk3l': 4,
    }
}

date2exp_dict = {
    '2019-11-15': {
        'team': 'amateurs',
        'day_num': 1,
    },
    '2019-11-22': {
        'team': 'pros',
        'day_num': 1,
    },
    '2019-12-04': {
        'team': 'pros',
        'day_num': 2,
    },
    '2019-12-11a': {
        'team': 'amateurs',
        'day_num': 2,
    },
    '2019-12-11b': {
        'team': 'pros',
        'day_num': 3,
    },
    '2019-12-17': {
        'team': 'amateurs',
        'day_num': 3,
    },
}
all_dates = date2exp_dict.keys()

exp2date_dict = {
    ('amateurs', 1): '2019-11-15',
    ('pros', 1): '2019-11-22',
    ('pros', 2): '2019-12-04',
    ('amateurs', 2): '2019-12-11a',
    ('pros', 3): '2019-12-11b',
    ('amateurs', 3): '2019-12-17',
}


class GameDay:

    def __init__(self, day_num, game_id, team='pros'):
        if day_num == 1:  # 1, 2, 3, 4
            if game_id == 1:
                self.real_players = 0
                self.communication = 1
            elif game_id == 2:
                self.real_players = 1
                self.communication = 1
            elif game_id == 3:
                self.real_players = 0
                self.communication = 0
            elif game_id == 4:
                self.real_players = 1
                self.communication = 0
        elif day_num == 2:  # 4, 1, 2, 3
            if game_id == 1:
                self.real_players = 1
                self.communication = 0
            elif game_id == 2:
                self.real_players = 0
                self.communication = 1
            elif game_id == 3:
                self.real_players = 1
                self.communication = 1
            elif game_id == 4:
                if team == 'amateurs':
                    self.real_players = 1
                    self.communication = 1
                else:  # As usual
                    self.real_players = 0
                    self.communication = 0
        elif day_num == 3:  # 2, 1, 4, 3
            if game_id == 1:
                self.real_players = 1
                self.communication = 1
            elif game_id == 2:
                self.real_players = 0
                self.communication = 1
            elif game_id == 3:
                self.real_players = 1
                self.communication = 0
            elif game_id == 4:
                self.real_players = 0
                self.communication = 0

    def get_stats(self):
        return {
            'real_opponents': self.real_players,
            'communication': self.communication,
        }


columns_order = ['gsr', 'emg_right_hand', 'emg_left_hand', 'heart_rate',
       'linaccel_x_left_hand', 'linaccel_y_left_hand', 'linaccel_z_left_hand',
       'gyro_x_left_hand', 'gyro_y_left_hand', 'gyro_z_left_hand',
       'linaccel_x_right_hand', 'linaccel_y_right_hand',
       'linaccel_z_right_hand', 'gyro_x_right_hand', 'gyro_y_right_hand',
       'gyro_z_right_hand', 'linaccel_x_chair_seat', 'linaccel_y_chair_seat',
       'linaccel_z_chair_seat', 'gyro_x_chair_seat', 'gyro_y_chair_seat',
       'gyro_z_chair_seat', 'linaccel_x_chair_back', 'linaccel_y_chair_back',
       'linaccel_z_chair_back', 'gyro_x_chair_back', 'gyro_y_chair_back',
       'gyro_z_chair_back', 'button_pressed', 'mouse_movement',
       'mouse_pressed', 'gaze_movement', 'pupil_diameter']












# player_ids = list(summoner_name2player_id_dict.values())



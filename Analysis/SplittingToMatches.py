import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *

day_num = 0

data_dict = joblib.load(data_folder + 'data_dict')
replays_dict = joblib.load(data_folder + 'replays_dict')

matches_dict = {}

for match_id, replay_dict in replays_dict.items():
    match_dict = {}
    for key in replay_dict:
        if key.startswith('events_player_'):
            player_id = key[len('events_player_'):]
            match_dict[player_id] = {
                'events': replay_dict[key],
            }
        else:
            match_dict[key] = replay_dict[key]

    # match_dict.update(replay_dict)

    match_start_time = replay_dict['start_time']#.timestamp()
    match_end_time = replay_dict['end_time']#.timestamp()

    for player_id, player_data_dict in data_dict.items():
        match_player_dict = {}
        data_sources = list(player_data_dict.keys())

        for data_source in data_sources:
            df4data_source = player_data_dict[data_source]
            mask_match_start = (df4data_source.index - match_start_time) >= pd.Timedelta(0)
            mask_match_end = (df4data_source.index - match_end_time) <= pd.Timedelta(0)
            mask_match = mask_match_start & mask_match_end
            df4data_source4match = df4data_source.loc[mask_match, :]
            df4data_source4match.index -= match_start_time
            match_player_dict[data_source] = df4data_source4match

        match_dict[player_id]['sensors'] = match_player_dict

    matches_dict[match_id] = match_dict


joblib.dump(matches_dict, data_folder + 'matches_dict')







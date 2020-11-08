import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from config import *
import glob
import json
from collections import defaultdict
import numpy as np


matches_processed_folder = os.path.join(dataset_folder, 'matches')

missed_dict = defaultdict(list)
# data_source = 'eeg_metrics'
# data_source = 'eeg_band_power'
for data_source in data_sources:
    pattern = os.path.join(matches_processed_folder, '**', '**', f'{data_source}.csv')
    # pattern = os.path.join(matches_processed_folder, '**', f'{data_source}.csv')
    paths = glob.glob(pattern)
    # path = paths[0]
    portions_missed_list = []

    for path in paths:
        path2meta_info = os.path.join(os.path.dirname(path), '..', 'meta_info.json')
        meta_info = json.load(open(path2meta_info))
        df = pd.read_csv(path, usecols=['time'])
        match_duration = meta_info['match_duration']
        portion_collected = round(df['time'].max() / meta_info['match_duration'], 1)
        portion_missed = 1 - portion_collected
        portions_missed_list.append(portion_missed)

    portions_missed_list = portions_missed_list + [1] * (110 - len(portions_missed_list))
    total_missed = np.mean(portions_missed_list)
    missed_dict[data_source] = total_missed
    print(data_source, total_missed)








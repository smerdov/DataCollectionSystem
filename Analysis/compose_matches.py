import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *
import argparse
import json
from utils import gsr_to_ohm
import tqdm
import shutil

# date = '2019-11-22'

# import os, shutil
# def copytree(src, dst, symlinks=False, ignore=None):
#     for item in os.listdir(src):
#         s = os.path.join(src, item)
#         d = os.path.join(dst, item)
#         if os.path.isdir(s):
#             shutil.copytree(s, d, symlinks, ignore)
#         else:
#             shutil.copy2(s, d)

parser = argparse.ArgumentParser()
parser.add_argument('--dates', nargs='+', default='', type=str)
# parser.add_argument('--replay-only', action='store_true')
parser.add_argument('--separate-file', default=None, type=str, choices=['replay.json', 'meta_info.json'])
args = parser.parse_args()
if args.dates[0] == 'all_dates':
    args.dates = all_dates
# args = parser.parse_args(['--dates', '2019-12-17'])

game_ids = [1, 2, 3, 4]
match_id = 0

for date in tqdm.tqdm(args.dates, desc='date\'s progress...'):
    for game_id in game_ids:
        if (date == '2019-12-11a') and (game_id == 3):
            continue

        path_src = os.path.join(dataset_folder, f'{date}_processed', f'game_{game_id}')
        if not os.path.exists(path_src):
            print(f'{path_src} does not exist')
            continue

        path_dst = os.path.join(dataset_folder, 'matches', f'match_{match_id}')
        if not os.path.exists(path_dst):
            os.makedirs(path_dst)

        rm_func = shutil.rmtree
        copy_func = shutil.copytree

        # if len(args.separate_file):
        if args.separate_file is not None:
            path_src = os.path.join(path_src, args.separate_file)
            path_dst = os.path.join(path_dst, args.separate_file)
            rm_func = os.remove
            copy_func = shutil.copy2

        rm_func(path_dst)
        copy_func(path_src, path_dst)
        # copytree(path_src, path_dst)
        match_id += 1





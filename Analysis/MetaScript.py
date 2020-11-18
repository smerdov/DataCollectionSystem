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
import tqdm
from collections import defaultdict

parser = argparse.ArgumentParser()

# Encounters extraction params
parser.add_argument('--min-interval-list', default=(10,), nargs='+', type=float)
parser.add_argument('--margin-list', default=(0.15,), nargs='+', type=float)

# Sensor data params
parser.add_argument('--halflife-list', default=(10,), nargs='+', type=float)
parser.add_argument('--resampling-string-list', default=('1s',), nargs='+', type=str)
parser.add_argument('--preresampling-string-list', default=('500ms',), nargs='+', type=str)
parser.add_argument('--halflifes-in-window-list', default=(5,), nargs='+', type=float)

# Tensors creation params
parser.add_argument('--time-step-list', default=('5s',), nargs='+', type=str)
parser.add_argument('--forecasting-horizon-list', default=(10,), nargs='+', type=float)

# NN params
parser.add_argument('--epochs', default=100, type=int)
parser.add_argument('--hidden-size-list', nargs='+', default=(8,), type=int)
parser.add_argument('--lstm-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--linear-layers-list', nargs='+', default=(1,), type=int)
parser.add_argument('--archs-list', nargs='+', default=('gru',), type=str)
parser.add_argument('--key-modes-list', nargs='+', default='all', type=str, help='Averaging type', choices=['player_team', 'player_team_match', 'match', 'all'])
# parser.add_argument('--output-suffix', default='last', type=str, help='Suffix to append to results')
# parser.add_argument('--data-suffix', default='last', type=str, help='Suffix for input data')
parser.add_argument('--patience', default=3, type=int, help='Patience for early stopping')
# parser.add_argument('--step-mode-list', nargs='+', default=('each',), type=str, help='Step modes for training',
#                     choices=['each', 'player', 'epoch'])

# Experiment related
parser.add_argument('--skip-encounters', action='store_true')
parser.add_argument('--skip-sensor-data', action='store_true')
parser.add_argument('--skip-tensor-creation', action='store_true')
parser.add_argument('--skip-cml', action='store_true')
parser.add_argument('--skip-rnn', action='store_true')
parser.add_argument('--skip-transformer', action='store_true')

parser.add_argument('--exp-name', default=None, type=str)
# parser.add_argument('--key-mode', default='all', type=str, help='Averaging type', choices=['player_team', 'player_team_match', 'match', 'all'])
parser.add_argument('--path2datasets', default='../Dataset/encounters_dataset', type=str, help='Suffix for input data')



def exec_cmd(cmd):
    print(cmd)
    os.system(cmd)

def args_list2args_str(args_list):
    args_str = ' '.join([str(x) for x in args_list])

    return args_str



if __name__ == '__main__':
    args = parser.parse_args()

    if args.exp_name is None:
        exp_suffix = 0
        exp_name = f'exp_{exp_suffix}'
        while os.path.exists(os.path.join(data_folder, exp_name)):
            exp_suffix += 1
            exp_name = f'exp_{exp_suffix}'

        args.exp_name = exp_name

    path2exp = os.path.join(data_folder, args.exp_name)

    if os.path.exists(path2exp):
        raise ValueError(f'path2exp {path2exp} already exists')


    groups = list(itertools.product(
        args.min_interval_list,
        args.margin_list,
        args.halflife_list,
        args.resampling_string_list,
        args.preresampling_string_list,
        args.halflifes_in_window_list,
        args.time_step_list,
        args.forecasting_horizon_list,
        args.archs_list,
        args.key_modes_list,
    ))

    np.random.shuffle(groups)


    for group in tqdm.tqdm(groups, desc='Processing parameters combinations...'):
        output_suffix = '_'.join([str(x) for x in group])

        min_interval, margin, halflife, resampling_string, preresampling_string, halflifes_in_window, time_step, \
            forecasting_horizon, arch, key_mode = group
        print(f'time_step={time_step}')

        if not args.skip_encounters:
            # Extract encounters
            cmd = f'python EncountersProcessing.py --min-interval {min_interval} --margin {margin}'
            exec_cmd(cmd)

        if not args.skip_sensor_data:
            # Process Sensor Data
            cmd = f'python SensorDataProcessing.py --halflife {halflife} --resampling-string {resampling_string} ' \
                  f'--preresampling-string {preresampling_string} --halflifes-in-window {halflifes_in_window}'
            exec_cmd(cmd)

        if not args.skip_tensor_creation:
            # Aggregating data into tensors with training data
            cmd = f'python EncountersDatasetCreation.py --time-step {time_step} --forecasting-horizon {forecasting_horizon}'
            exec_cmd(cmd)

        # Creating a directory for experiment results
        if not os.path.exists(path2exp):
            os.mkdir(path2exp)

        if not args.skip_cml:
            # Run Classical ML
            cmd = f'python ClassicalML.py --output-path {path2exp} --output-suffix {output_suffix} --key-mode {key_mode} ' \
                  f'--path2datasets {args.path2datasets}'
            exec_cmd(cmd)

        if not args.skip_transformer:
            # Run Classical ML
            cmd = f'python Transformer.py --output-path {path2exp} --output-suffix {output_suffix} --key-mode {key_mode} ' \
                  f'--path2datasets {args.path2datasets}'
            exec_cmd(cmd)

        if not args.skip_rnn:
            # Run NN
            cmd = f'python RNN.py --hidden-size-list {args_list2args_str(args.hidden_size_list)} ' \
                  f'--lstm-layers-list {args_list2args_str(args.lstm_layers_list)} ' \
                  f'--linear-layers-list {args_list2args_str(args.linear_layers_list)} ' \
                  f'--patience {args.patience} ' \
                  f'--epochs {args.epochs} ' \
                  f'--key-mode {key_mode} ' \
                  f'--path2datasets {args.path2datasets} ' \
                  f'--output-path {path2exp} ' \
                  f'--output-suffix {output_suffix} ' \
                  f'--arch {arch}'
                  # f'--step-mode-list {args_list2args_str(args.step_mode_list)} ' \
            exec_cmd(cmd)




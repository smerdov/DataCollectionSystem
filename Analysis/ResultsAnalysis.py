import json
import os
import pandas as pd
from config import *
import json

exp_ids = [9]
exp_names = [f'exp_{exp_id}' for exp_id in exp_ids] + []  # For named experiments

results_list = []

for exp_name in exp_names:
    path2exp = os.path.join(data_folder, exp_name)
    filenames = os.listdir(path2exp)
    filenames = [filename for filename in filenames if not filename.startswith('.')]

    for filename in filenames:
        # entry_info = {}

        path2filename = os.path.join(path2exp, filename)
        with open(path2filename) as f:
            entry_json = json.load(f)

        suffix = filename.split('_results_')[1]
        suffix = suffix.replace('.json', '')
        suffix_parts = suffix.split('_')
        params = {
            'min_interval': float(suffix_parts[0]),
            'margin': float(suffix_parts[1]),
            'halflife': float(suffix_parts[2]),
            'resampling_str': suffix_parts[3],
            'preresampling_str': suffix_parts[4],
            'halflifes_in_window': float(suffix_parts[5]),
            'time_step': suffix_parts[6],
            'forecasting_horizon': float(suffix_parts[7]),
        }

        for alg_name, alg_scores in entry_json.items():
            alg_resuls = {
                'alg_name': alg_name,
            }

            for scorer_name, scores4datasets in alg_scores.items():
                for dataset, score4dataset in scores4datasets.items():
                    key = f'{scorer_name}_{dataset}'
                    alg_resuls[key] = score4dataset

            alg_resuls.update(params)
            results_list.append(alg_resuls)


df_results = pd.DataFrame(results_list)

def agg_results(df, columns, metric='auc_test'):
    return df.groupby(columns)[metric].mean()

agg_results(df_results, ['alg_name'])
agg_results(df_results, ['forecasting_horizon'])
agg_results(df_results, ['time_step'])
agg_results(df_results, ['margin'])
agg_results(df_results, ['min_interval'])

agg_results(df_results, ['alg_name', 'min_interval'])
agg_results(df_results, ['alg_name', 'forecasting_horizon'])
agg_results(df_results, ['alg_name', 'forecasting_horizon', 'time_step'])
agg_results(df_results, ['alg_name', 'time_step'])
agg_results(df_results, ['time_step', 'forecasting_horizon'])
agg_results(df_results, ['alg_name', 'margin'])
agg_results(df_results, ['min_interval', 'margin'])

# Sensor data related
agg_results(df_results, ['halflife', 'resampling_str'])
agg_results(df_results, ['halflife'])
agg_results(df_results, ['resampling_str'])


# df_results.groupby(['time_step', 'forecasting_horizon', 'margin'])['auc_test'].mean()
agg_results











path2results = os.path.join(data_folder, 'results_last_2.json')
with open(path2results) as f:
    results = json.load(f)

results.keys()
results['5,2,1'].keys()

selected_results = {key: value[key_1][key_2] for key, value in results.items()}

pd.DataFrame.from_records(selected_results)
# pd.DataFrame(selected_results)




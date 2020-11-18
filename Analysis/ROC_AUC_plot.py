import json
import os
import pandas as pd
from config import *
import json
import matplotlib

# exp_ids = [11, 12]
# exp_ids = [12, 13]
# exp_ids = [49, 50]
# exp_ids = [93, 94, 95]
# exp_ids = [99, 100, 102]
# exp_ids = [105, 106, 107, 108, 109]
exp_ids = [163, 164, 165, 166, 167]
exp_names = [f'exp_{exp_id}' for exp_id in exp_ids] + []  # For named experiments

# # exp_names = ['exp_mode_all', 'exp_mode_player_team', 'exp_mode_player_team_match']  # For named experiments
# exp_names = ['exp_59', 'exp_60']  # For named experiments

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

        prefix = filename.split('_results_')[0]
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
            'arch': suffix_parts[8],
            'key_mode': '_'.join(suffix_parts[9:]),
            'prefix': prefix,
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


forecasting_horizons_list = sorted(df_results['forecasting_horizon'].unique())



rename_dict = {
    '64,1,2': 'GRU',
    # '64,1,1': 'GRU_',
    '8,1,1': 'Transformer',
    'lr': 'Logistic Regression',
    'svm': 'SVM',
    'knn_96': 'KNN',
    'rf_24': 'Random Forest',
}


# for forecasting_horizons in forecasting_horizons_list:
plt.close()
fontsize = 24
matplotlib.rcParams.update({'font.size': 24})
lw = 5
alpha = 0.9

fig, ax = plt.subplots(figsize=(16, 9))
for alg_name in df_results['alg_name'].unique():
    # # if not alg_name[0].isdigit():
    # #     continue
    if alg_name.startswith('rf') or alg_name.startswith('svm'):
        continue

    mask = df_results['alg_name'] == alg_name

    df4plot = df_results.loc[mask, ['auc_test', 'forecasting_horizon']]
    df4plot.set_index('forecasting_horizon', inplace=True)
    df4plot = df4plot.groupby('forecasting_horizon').mean()
    df4plot.sort_index(inplace=True)
    ax.plot(df4plot.index, df4plot['auc_test'], label=rename_dict[alg_name], lw=lw, alpha=alpha)

ax.hlines(0.5, 0, 90, lw=lw, color='black', linestyles='--', label='Random Guess')
ax.set_xlim(0, 90)
# ax.set_ylim(0.49, 0.76)
ax.set_ylim(0.4985, 0.75)
# ax.set_title('Algorithms\' Scores w.r.t. Forecasting Horizon')
ax.set_xlabel('Forecasting Horizon $\\tau$, s')
ax.set_ylabel('ROC AUC')
ax.grid(alpha=1)
ax.legend()
ax.tick_params(which='major', size=fontsize//2)
fig.tight_layout()
fig.savefig('../Pictures/AUC/auc_last_14_.pdf')
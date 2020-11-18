import pandas as pd
from config import *
import glob
import os
import json
import matplotlib.pyplot as plt

pattern = os.path.join(dataset_folder, 'matches_processed', '**', '**', 'player_report.json')
reports = glob.glob(pattern)

reports_list = []
match_types = []
teams = []

for report in reports:
    with open(report) as f:
        new_report = json.load(f)
        reports_list.append(new_report)

    match_dir = os.path.dirname(os.path.dirname(report))
    path2match_info = os.path.join(match_dir, 'meta_info.json')
    with open(path2match_info) as f:
        match_info = json.load(f)
        match_types.append(match_info['real_opponents'])
        teams.append(match_info['team'])

df_reports = pd.DataFrame(reports_list)
df_reports['real_opponents'] = match_types
df_reports['team'] = teams

# Disturbance statistics
df_reports['sensing_system_disturbance'].value_counts() / len(df_reports)

fontsize = 28

plt.close()
fig, ax = plt.subplots(figsize=(16, 9))
ax.hist(
    [df_reports['performance_evaluation'], df_reports['performance_evaluation_teammates']],
    alpha=1.,
    bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
    # color=['sandybrown', 'yellowgreen'],
    color=['darkcyan', 'lightsalmon'],
    label=['Self-evaluation', 'Peer-evaluation'],
    density=True,
)
ax.tick_params(which='both', labelsize=fontsize, length=12)#, width=1.5)
ax.set_xlabel('Evaluation', fontsize=fontsize+4)
ax.set_ylabel('Proportion of responses', fontsize=fontsize+4)
ax.legend(loc='upper left', fontsize=fontsize)
fig.tight_layout()
fig.savefig(os.path.join(pic_folder, 'players_evaluations.pdf'))
# plt.hist(df_reports['performance_evaluation_teammates'], alpha=0.8)


mask_real_opponents = df_reports['real_opponents'] == 1
mask_amateurs = df_reports['team'] == 'amateurs'
df_reports.loc[mask_real_opponents, 'mental_load'].mean()
df_reports.loc[~mask_real_opponents, 'mental_load'].mean()


plt.close()
fig, ax = plt.subplots(figsize=(16,9))
ax.hist(
    [df_reports.loc[mask_real_opponents&mask_amateurs, 'mental_load'],
     df_reports.loc[mask_real_opponents&~mask_amateurs, 'mental_load']],
    alpha=1.,
    bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
    # color=['mediumseagreen', 'indianred'],
    # color=['brown', 'skyblue'],
    # color=['peru', 'skyblue'],
    color=['peru', 'skyblue'],
    label=['Amateurs', 'Professionals'],
    density=True,
)
ax.tick_params(which='both', labelsize=fontsize, length=12)#, width=1.5)
ax.set_xlabel('Mental load', fontsize=fontsize+4)
ax.set_ylabel('Proportion of responses', fontsize=fontsize+4)
ax.legend(loc='upper left', fontsize=fontsize)
fig.tight_layout()
fig.savefig(os.path.join(pic_folder, 'mental_load.pdf'))



df_players = pd.read_csv(dataset_folder + 'players_info.csv')
df_players




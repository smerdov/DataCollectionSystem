import pandas as pd
from config import *
import os
import json


df = pd.read_csv(os.path.join(dataset_folder, 'GoogleForms/After Match Survey.csv'), sep=';')
df['date'] = df.apply(lambda x: exp2date_dict[(x['team'], x['day_num'])], axis=1)
df.drop(columns=['time', 'day_num', 'team'], inplace=True)
df['role'] = df['role'].apply(lambda x: x.lower())
df['sensing_system_disturbance'] = df['sensing_system_disturbance'].apply(lambda x: x.lower())
sensing_system_disturbance_rename_dict = {
    'not at all': 'no',
    'yes, it did': 'yes',
    'a little bit': 'a little bit',
}
df['sensing_system_disturbance'] = df['sensing_system_disturbance'].apply(lambda x: sensing_system_disturbance_rename_dict[x])
# df.rename(columns={'sensing_system_disturbance': 'sensing_system_disturbed'}, inplace=True)
df = df.set_index(['date', 'game_num', 'player_id'])

for index, row in df.iterrows():
    # pass
    # row.to_dict()
    date, game_num, player_id = index
    row2dump = row.to_dict()
    path2dump = os.path.join(dataset_folder, f'{date}_processed', f'game_{game_num}', f'player_{player_id}', 'player_report.json')

    if os.path.exists(os.path.dirname(path2dump)):  # If the folder exists
        with open(path2dump, 'w') as f:
            json.dump(row2dump, f)







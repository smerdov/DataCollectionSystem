import pandas as pd
from config import *
import os


df = pd.read_csv(os.path.join(dataset_folder, 'GoogleForms/Player Survey.csv'), sep=';')
df.sort_values(['team', 'player_id'], inplace=True)
df = df.reset_index(drop=True)
df.rename(columns={
    'best_rank_ever': 'best_rank_achieved',
    'I am': 'dominant_hand',
    },
    inplace=True,
)
df.replace('I never had a rank', 'no_rank', inplace=True)
df.replace("I don't have a rank in Season 9", 'no_rank', inplace=True)
df.replace('Right-handed', 'right', inplace=True)
df.replace('Left-handed', 'left', inplace=True)
df['best_rank_achieved'] = df['best_rank_achieved'].apply(lambda x: x.lower())
df['rank_season_9'] = df['best_rank_achieved'].apply(lambda x: x.lower())


df.to_csv(os.path.join(dataset_folder, 'players_info.csv'), index=None)









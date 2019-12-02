import activityio as aio
import pandas as pd
import os
import json

TIME_FORMAT = "%Y-%m-%d-%H-%M-%S"
TIME_FORMAT_FIT = "%Y-%m-%dT%H:%M:%SZ"
players_list = json.load(open('players_credentials.json'))


for player_dict in players_list:
    player_id = player_dict['player_id']
    player_data_dir = f'fit_data/player_{player_id}/'
    player_fit_filenames = os.listdir(player_data_dir)

    df4player = pd.DataFrame()

    prefixes = [filename[:-4] for filename in player_fit_filenames if filename.endswith('.fit')]

    if len(prefixes) == 0:
        continue

    # for player_fit_filename in player_fit_filenames:
    for prefix in prefixes:
        filename_data = prefix + '.fit'
        filename_time_start = prefix + '_start_time.txt'

        with open(player_data_dir + filename_time_start) as f:
            start_time = f.readline()

        data2add = aio.read(player_data_dir + filename_data)
        if 'hr' not in data2add:
            continue

        df2add = pd.DataFrame(data2add)[['hr']]
        df2add.index = pd.to_datetime(start_time) + df2add.index
        df2add.rename(columns={'hr': 'heart_rate'}, inplace=True)
        df2add.index.name = 'Timestamp'

        df4player = pd.concat([df4player, df2add])

    if len(df4player):
        df4player = df4player.sort_index()
        suffix = df4player.index[0].strftime(TIME_FORMAT)

        df4player.to_csv(f'output/player_{player_id}/heart_rate_{suffix}.csv')
    else:
        print(f'No data for player {player_id}')
        # print(df4player)





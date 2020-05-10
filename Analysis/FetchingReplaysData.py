import json
import joblib
import os
import requests
import pandas as pd
from config import *
import argparse

# date = '2019-11-15'
# date = '2019-11-22'
# date = '2019-12-17'
# date = '2019-12-11a'
parser = argparse.ArgumentParser()
parser.add_argument('--dates', nargs='+', default='', type=str)
args = parser.parse_args()


for date in args.dates:
    replays_path = f'{dataset_folder}{date}/replays/'
    data_path_processed = f'{dataset_folder}{date}_processed/'

    # replay_filenames = os.listdir(replays_path)
    # replay_filenames = sorted(replay_filenames)
    match_ids_dict = {}

    # for replay_filename in replay_filenames:
    #     id_index_start = replay_filename.find('-')
    #     id_index_end = replay_filename.find('.rofl')
    #     if (id_index_start != -1) and (id_index_end != -1):
    #         match_ids.append(replay_filename[id_index_start+1:id_index_end])

    game_folders = os.listdir(replays_path)
    game_folders = [folder for folder in game_folders if folder.startswith('game')]
    game_folders = sorted(game_folders)

    for game_folder in game_folders:
        with open(replays_path + game_folder + '/' + 'match_id.md') as f:
            match_id = f.readline()
            match_ids_dict[game_folder] = match_id

    # match_id = '4232819529'
    prefix = 'https://euw1.api.riotgames.com/'
    headers = {
        "Origin": "https://developer.riotgames.com",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Riot-Token": API_KEY,
        "Accept-Language": "en-us",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15"
    }

    for match_name, match_id in match_ids_dict.items():
        replay_json = {}

        response_match_info = requests.get(prefix + f'lol/match/v4/matches/{match_id}', headers=headers)
        if response_match_info.status_code != 200:
            raise ValueError('There is a problem')
        response_match_info_json = json.loads(response_match_info.content)
        replay_json.update(response_match_info_json)

        response_timeline = requests.get(prefix + f'lol/match/v4/timelines/by-match/{match_id}', headers=headers)
        if response_timeline.status_code != 200:
            raise ValueError('There is a problem')
        response_timeline_json = json.loads(response_timeline.content)
        replay_json.update(response_timeline_json)


        # json.dump(replay_json, open(data_folder + 'replays_json/' + f'replay_{match_id}.json', 'w'))

        replay_json_folder = replays_path + match_name + '/' + 'replay_json/'
        if not os.path.exists(replay_json_folder):
            os.mkdir(replay_json_folder)

        json.dump(replay_json, open(replay_json_folder + f'replay.json', 'w'))



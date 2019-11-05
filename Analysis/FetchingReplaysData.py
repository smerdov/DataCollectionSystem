import json
import joblib
import os
import requests
import pandas as pd
from config import *

day_num = 0
replays_path = f'{dataset_folder}day_{day_num}/replays/'
replay_filenames = os.listdir(replays_path)
# replay_filenames = sorted(replay_filenames)
match_ids = []

for replay_filename in replay_filenames:
    id_index_start = replay_filename.find('-') + 1
    id_index_end = replay_filename.find('.rofl')
    match_ids.append(replay_filename[id_index_start:id_index_end])


# match_id = '4232819529'
prefix = 'https://euw1.api.riotgames.com/'
headers = {
    "Origin": "https://developer.riotgames.com",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Riot-Token": API_KEY,
    "Accept-Language": "en-us",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15"
}

for match_id in match_ids:
    response = requests.get(prefix + f'lol/match/v4/timelines/by-match/{match_id}', headers=headers)
    response_json = json.loads(response.content)
    json.dump(response_json, open(data_folder + f'replay_{match_id}.json', 'w'))



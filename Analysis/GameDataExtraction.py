import json
import joblib
import os
import pandas as pd
from datetime import datetime
from config import *
from collections import defaultdict
import argparse

# summoner_names = ['TUK Trannas', 'AE Iromator']

# date = '2019-11-15'
parser = argparse.ArgumentParser()
parser.add_argument('--dates', nargs='+', default='', type=str)
args = parser.parse_args()
# args = parser.parse_args(['--date', '2019-12-17', '2019-12-11b', '2019-12-11a'])
# args = parser.parse_args(['--date', '2019-12-04'])
# date = args.dates[0]

for date in args.dates:
    # date = args.date

    # date = '2019-12-17'
    # team_name = 'amateurs'
    team_name = date2exp_dict[date]['team']

    # team_name = 'pros'

    summoner_name2player_id_dict = summoner_name2player_id_dicts[team_name]
    summoner_name2player_id_dict.update({
        'opponent_0': 5,
        'opponent_1': 6,
        'opponent_2': 7,
        'opponent_3': 8,
        'opponent_4': 9,
    })
    summoner_names = list(summoner_name2player_id_dict.keys())


    replays_path = f'{dataset_folder}{date}/replays/'
    game_folders = os.listdir(replays_path)
    game_folders = [folder for folder in game_folders if folder.startswith('game')]
    game_folders = sorted(game_folders)
    data_path_processed = f'{dataset_folder}{date}_processed/'

    replays_jsons = {}

    for game_folder in game_folders:
        replay_json = json.load(open(f'{replays_path}{game_folder}/replay_json/replay.json'))
        replays_jsons[game_folder] = replay_json


    # def get_match_id_from_filename(filename):
    #     match_id_index_start = filename.find('_')
    #     match_id_index_end = filename.find('.json')
    #     if (match_id_index_start != -1) and (match_id_index_end != -1):
    #         return filename[match_id_index_start+1:match_id_index_end]
    #     else:
    #         return None
    #         # raise ValueError(f'can\'t extract match_id from filename {filename}')
    #
    # for replays_jsons_filename in replays_jsons_filenames:
    #     match_id = get_match_id_from_filename(replays_jsons_filename)
    #     if match_id is None:
    #         continue
    #     replay_json = json.load(open(replays_json_path + replays_jsons_filename))
    #     replays_jsons[match_id] = replay_json

    replays_processed = {}

    # replays_json = replays_jsons['4232819529']  # DEBUG

    # match_id, replay_json = list(replays_jsons.items())[0]

    participant_id2summoner_name_dict_restored = {
        '2019-11-15': {
            'game_1': {
                1: 'TheSilverTusk',
                2: 'Fillps',
                3: 'oi mori  ',
                4: 'Supersaiyarunk3l',
                5: 'ZdadrDeM',
            }
        },
        '2019-11-22': {
            # 'game_3': {
            #     0: 'Reiign',
            #     1: 'TUK hi im ballat',
            #     2: 'TUK Trannas',
            #     3: 'Biotom',
            #     4: 'TUK Psytolos',
            # },
            'game_3': {
                1: 'Reiign',
                2: 'TUK hi im ballat',
                3: 'TUK Trannas',
                4: 'Biotom',
                5: 'TUK Psytolos',
            }
        },
        '2019-12-04': {
            'game_2': {
                1: 'Reiign',
                2: 'TUK Psytolos',
                3: 'Biotom',
                4: 'Ebermann',
                5: 'TUK Trannas',
            }
        },
    }

    # match_id, replay_json = list(replays_jsons.items())[0]
    for match_id, replay_json in replays_jsons.items():
        print(f'Processing {match_id}')
        custom_game = False
        # players_dict4replay = {}
        participant_id2summoner_name_dict = {}

        if date in participant_id2summoner_name_dict_restored:  # This is a custom game
            if match_id in participant_id2summoner_name_dict_restored[date]:
                custom_game = True
                participant_id2summoner_name_dict = participant_id2summoner_name_dict_restored[date][match_id]

        if not custom_game:
            for participant in replay_json['participantIdentities']: # This is not a custom game
                if participant['player']['summonerName'] in summoner_names:
                    participant_id = participant['participantId']
                    participant_id2summoner_name_dict[participant_id] = participant['player']['summonerName']

        def get_player_id_from_participant_id(participant_id):
            summoner_name = participant_id2summoner_name_dict[participant_id]
            player_id = summoner_name2player_id_dict[summoner_name]

            return player_id

        ### TODO: do I need 2 lines below?
        # if len(participant_id2summoner_name_dict) == 0:
        #     raise ValueError(f'Game {match_id} is a custom game. I need to reindex players')

        # print(participant_id2summoner_name_dict)
        n_opponent_id = 0
        for _participant_id in range(1, 11):
            if _participant_id not in participant_id2summoner_name_dict:  # T
                opponent_name = f'opponent_{n_opponent_id}'
                print(f'Creating {opponent_name}')
                participant_id2summoner_name_dict[_participant_id] = opponent_name
                n_opponent_id += 1


        replay_processed = {}
        meta_info = {}
        # loading_screen_correction = 90
        # replay_processed['start_time'] = pd.to_datetime(replay_json['gameCreation'] / 1000 + 3600 * 2 + loading_screen_correction, unit='s')
        meta_info['game_duration'] = replay_json['gameDuration']
        meta_info['season_id'] = replay_json['seasonId']
        meta_info['game_version'] = replay_json['gameVersion']
        # replay_processed['game_mode'] = replay_json['gameMode']
        # replay_processed['game_type'] = replay_json['gameType']
        teams = replay_json['teams']
        teams_dict = {}
        if participant_id2summoner_name_dict[1] == 'opponent_0':  # players 5-9 are in team 100
            # teams[0]['teamName'] = 'opponents'
            # teams[1]['teamName'] = 'participants'
            teams[0]['players'] = list(range(5, 10))
            teams[1]['players'] = list(range(0, 5))
            teams_dict['opponents'] = teams[0]
            teams_dict['participants'] = teams[1]
        else:
            # teams[0]['teamName'] = 'participants'
            # teams[1]['teamName'] = 'opponents'
            teams[0]['players'] = list(range(0, 5))
            teams[1]['players'] = list(range(5, 10))
            teams_dict['participants'] = teams[0]
            teams_dict['opponents'] = teams[1]

        # replay_processed['teams'] = teams
        replay_processed['teams'] = teams_dict


        # for participant_id, summoner_name in participant_id2summoner_name_dict.items():
        for summoner_name, player_id in summoner_name2player_id_dict.items():
            replay_processed[f'player_{player_id}'] = {
                'deathTimes': [],
                'killTimes': [],
                'assistTimes': [],
            }


        for participant_info, participant_id in zip(replay_json['participants'], list(range(1, 11))):
            player_id = get_player_id_from_participant_id(participant_info['participantId'])
            if int(player_id) < 5:
                participant_info['teamName'] = 'participants'
            else:
                participant_info['teamName'] = 'opponents'

            del participant_info['participantId']
            del participant_info['timeline']['participantId']
            del participant_info['stats']['participantId']

            replay_processed[f'player_{player_id}'].update(participant_info)


        # replay_json['participantIdentities']
        # replay_json['frameInterval']
        # replay_json.keys()

        # replay_processed['end_time'] = replay_processed['start_time'] + pd.Timedelta(replay_processed['game_duration'], unit='s')




        for frames in replay_json['frames']:
            for event in frames['events']:
            # for event in replay_json['frames'][10]['events']:
                if event['type'] == 'CHAMPION_KILL':
                    # print(event)
                    if event['killerId'] in participant_id2summoner_name_dict:
                        timestamp = event['timestamp'] / 1000
                        # summoner_name = participant_id2summoner_name_dict[event['killerId']]
                        player_id = get_player_id_from_participant_id(event['killerId'])
                        replay_processed[f'player_{player_id}']['killTimes'].append(timestamp)
                    if event['victimId'] in participant_id2summoner_name_dict:
                        timestamp = event['timestamp'] / 1000
                        # summoner_name = participant_id2summoner_name_dict[event['victimId']]
                        player_id = get_player_id_from_participant_id(event['victimId'])
                        replay_processed[f'player_{player_id}']['deathTimes'].append(timestamp)
                    for assistant_participant_id in event['assistingParticipantIds']:
                        if assistant_participant_id in participant_id2summoner_name_dict:
                            timestamp = event['timestamp'] / 1000
                            # summoner_name = participant_id2summoner_name_dict[assistant_participant_id]
                            player_id = get_player_id_from_participant_id(assistant_participant_id)
                            replay_processed[f'player_{player_id}']['assistTimes'].append(timestamp)

        replays_processed[match_id] = replay_processed

        path2save = os.path.join(data_path_processed, match_id, f'replay.json')
        json.dump(replay_processed, open(path2save, 'w'))

        path2meta_info = os.path.join(data_path_processed, match_id, f'meta_info.json')
        with open(path2meta_info) as f:
            meta_info_prev = json.load(f)

        meta_info.update(meta_info_prev)

        with open(path2meta_info, 'w') as f:
            json.dump(meta_info, f)


# joblib.dump(replays_processed, data_folder + 'replays_dict')



# datetime.fromtimestamp(replays_json['gameCreation']/1000)
# replays_json['gameDuration']
# replays_json.keys()





















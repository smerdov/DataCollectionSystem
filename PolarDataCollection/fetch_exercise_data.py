import requests
import os
from datetime import datetime
import pandas as pd
import json
import argparse

# CONFIG_FILENAME = "config.yml"
# config = load_config(CONFIG_FILENAME)
# # user_id = config["user_id"]

parser = argparse.ArgumentParser()
parser.add_argument('--date', default='', type=str)
args = parser.parse_args()
date = args.date


def get_relevant_exercises(exercises_list, start_time_intervals_list, min_duration=0):
    relevant_exercises_list = []

    for exercise in exercises_list:
        exercise_start_time = exercise['start_time']

        for start_time_min, start_time_max in start_time_intervals_list:
            if start_time_min <= exercise_start_time <= start_time_max:
                exercise_dict = {}
                exercise_dict['id'] = exercise['id']
                exercise_dict['start_time'] = exercise_start_time

                relevant_exercises_list.append(exercise_dict)

    return relevant_exercises_list


players_list = json.load(open('players_credentials.json'))

def create_interval_for_date(date):
    date_start = f'{date}T00:00:00Z'
    date_end = f'{date}T23:59:59Z'

    return (date_start, date_end)



# start_time_intervals_list = [ # Start time intervals must don't intersect
#     ('2019-11-15T00:00:00Z', '2019-11-15T23:59:59Z'),
#     # ('2019-11-22T00:00:00Z', '2019-11-22T23:59:59Z'),
# ]

start_time_intervals_list = [
    create_interval_for_date(date)
]

for player_dict in players_list:
    player_id = player_dict['player_id']
    player_data_dir = f'fit_data/player_{player_id}/'
    player_fit_filenames = os.listdir(player_data_dir)
    for player_fit_filename in player_fit_filenames:
        os.remove(player_data_dir + player_fit_filename)
    
    
    access_token = player_dict['access_token']

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    r = requests.get('https://www.polaraccesslink.com/v3/exercises', params={}, headers = headers)

    if r.status_code != 200:
        print(r)
        raise ValueError(f"Status code {r.status_code}")

    relevant_exercises_list = get_relevant_exercises(r.json(), start_time_intervals_list)

    for n_relevant_exercise, relevant_exercise in enumerate(relevant_exercises_list):
        relevant_exercise_id = relevant_exercise['id']
        relevant_exercise_start_time = relevant_exercise['start_time']

        r = requests.get(f'https://www.polaraccesslink.com/v3/exercises/{relevant_exercise_id}/fit', params={}, headers=headers)

        filename = f'fit_file_player_{player_id}_{n_relevant_exercise}_{relevant_exercise_start_time[:10]}'

        with open(f'{player_data_dir}{filename}.fit', 'wb') as f:
            f.write(r.content)

        with open(f'{player_data_dir}{filename}_start_time.txt', 'w') as f:
            f.write(relevant_exercise_start_time)







# hashed_id = r.json()[0]['id']  # just for test
#
# r = requests.get(f'https://www.polaraccesslink.com/v3/exercises/{hashed_id}/fit', params={}, headers = headers)
#
# if r.status_code != 200:
#     print(r)
#     raise ValueError(f"Status code {r.status_code}")












#
#
#
#
# r = requests.post(f'https://www.polaraccesslink.com/v3/users/{user_id}/exercise-transactions', params={
# }, headers = headers)
#
# transaction_id = r.json()['transaction-id']
# # r.text
# # print(r.json())
#
#
# # r = requests.get('https://www.polaraccesslink.com/v3/users/44498237', params={
# #
# # }, headers = headers)
#
#
# r = requests.get(f'https://www.polaraccesslink.com/v3/users/{user_id}/exercise-transactions/{transaction_id}', params={
# }, headers = headers)
#
# exercises_list = [exercise_link.split('/')[-1] for exercise_link in r.json()['exercises']]
#
# exercise_id = exercises_list[0]
#
# # r = requests.get(f'https://www.polaraccesslink.com/v3/users/{user_id}/exercise-transactions/{transaction_id}/exercises/{exercise_id}/tcx', params={
# #
# # }, headers = headers)
# #
# # r
#
# r = requests.get(f'https://www.polaraccesslink.com/v3/users/{user_id}/exercise-transactions/{transaction_id}/exercises/{exercise_id}/samples/0', params={
#
# }, headers = headers)
#
# r.json()
#
#
#
# r = requests.put(f'https://www.polaraccesslink.com/v3/users/{user_id}/exercise-transactions/{transaction_id}', params={
#
# }, headers = headers)
#
#
# r.json()
#
#
#
#
# import requests
# headers = {
#   # 'Content-Type': 'application/xml',
#   'Accept': 'application/json',
#   'Authorization': f'Bearer {config["access_token"]}',
# }
#
# r = requests.post('https://www.polaraccesslink.com/v3/users', params={
#
# }, headers = headers)
#
#
# r.json()
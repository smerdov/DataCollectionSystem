from datetime import datetime
import pandas as pd
from datetime import timedelta
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--date', default='', type=str)
args = parser.parse_args()
date = args.date

# date = '2019-11-15'

path = f'../Dataset/{date}/'
TIME_FORMAT = '%Y-%m-%d-%H:%M:%S'

df = pd.read_csv(path + 'labels/games_start_end_times_input_data.csv', sep=';')

def parse_timedelta(string):
    timedelta_value = datetime.strptime(string, '%H:%M:%S')
    timedelta_value = timedelta(
        hours=timedelta_value.hour,
        minutes=timedelta_value.minute,
        seconds=timedelta_value.second
    )

    return timedelta_value

date_formatted = datetime.strptime(date, '%Y-%m-%d')

df['game_start'] = None
df['game_end'] = None

for n_row in range(len(df)):
    row = df.loc[n_row, :]
    recording_finish_time = parse_timedelta(row['recording_finish_time'])
    recording_duration = parse_timedelta(row['recording_duration'])
    game_start_time_on_recording = parse_timedelta(row['game_start_time_on_recording'])
    game_length = parse_timedelta(row['game_length'])

    game_start = date_formatted + recording_finish_time - recording_duration + game_start_time_on_recording
    game_end = game_start + game_length

    game_start = game_start.strftime(TIME_FORMAT)
    game_end = game_end.strftime(TIME_FORMAT)

    df.loc[n_row, 'game_start'] = game_start
    df.loc[n_row, 'game_end'] = game_end

df = df[['game_num', 'game_start', 'game_end']]
df.to_csv(path + 'labels/games_start_end_times.csv', index=False)












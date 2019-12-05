import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--date', default='', type=str)
args = parser.parse_args()
date = args.date


os.system(f'python fetch_exercise_data.py --date {date}')
os.system(f'python file_parsing.py')





import joblib
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import itertools
from datetime import datetime
from config import *
import argparse
import json
from collections import defaultdict
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('--min-interval', default=10, type=float)
parser.add_argument('--margin', default=0.15, type=float)
args = parser.parse_args()
# args = parser.parse_args([])

matches_folder = os.path.join(dataset_folder, 'matches')
matches_processed_folder = os.path.join(dataset_folder, 'matches_processed')

matches = [match for match in os.listdir(matches_folder) if match.startswith('match')]
# matches = sorted(matches)
event_types = ['kill', 'death', 'assist']


class Event:

    def __init__(self, time, event_type, player_id, n_assistants):
        self.time = time
        self.event_type = event_type
        self.player_id = player_id
        self.n_assistants = n_assistants

    def __repr__(self):
        return f'player {self.player_id} {self.event_type} at {round(self.time,2)} s, ' \
               f'{self.n_assistants} assistants'

    def __lt__(self, other):
        return self.time < other.time


class Encounter:

    # def __init__(self, time, outcome, player_id):
    #     self.time = time
    #     self.outcome = outcome
    #     self.player_id = player_id

    def __init__(self, events, event_weights, margin):
        self.events = events
        self.event_weights = event_weights
        self.margin = margin
        self._parse_events(events, event_weights)

    def _parse_events(self, events, event_weights):
        # self.events_weights = [event_weights[event.event_type] for event in events]
        self.events_weights = [event_weights[event.event_type] / (1 + event.n_assistants) for event in events]
        self.outcome = self._weights2target(self.events_weights)
        self.time = events[0].time
        self.duration = events[-1].time - events[0].time
        self.player_id = events[0].player_id

    # @staticmethod
    def _weights2target(self, weights):
        self.total_weight = sum(weights)
        if self.margin == 0:
            if self.total_weight == 0:
                # print('Nonsense! total_weight == 0 !')
                return int(weights[0] > 0)
            else:
                return int(self.total_weight > 0)
        else:
            if self.total_weight > self.margin:
                return 1
            elif self.total_weight < - self.margin:
                return 0
            else:
                return None


    def __repr__(self):
        return f'encounter {self.outcome} at {round(self.time, 1)} s for player_{self.player_id}, ' \
               f'duration {round(self.duration, 1)} s, total weight {self.total_weight}, ' \
               f'weights {self.events_weights}'


class EncounterExtractor:

    default_event_weights = {
        'kill': 1,
        'death': -1,
        'assist': 1,
    }

    def __init__(self, min_interval=10, event_weights=None):
        self.min_interval = min_interval
        if event_weights is not None:
            self.event_weights = event_weights
        else:
            self.event_weights = self.default_event_weights

    def __call__(self, events):
        assert events == sorted(events)  # Events are sorted chronologically
        assert 1 == len(set([event.player_id for event in events]))  # Event are only for one player

        encounters = []
        current_events = []
        last_event_time = -self.min_interval

        for event in events:
            if len(current_events):
                if event.time - last_event_time > self.min_interval:  # or (n_event == len(events) - 1):
                    ### The previous encounter finished
                    # events_weights = [self.event_weights[event_instance.event_type] for event_instance in current_events]
                    # encounter_outcome = self._weights2target(events_weights) * 1
                    # encounter_start_time = current_events[0].time
                    # encounter2add = Encounter(time=encounter_start_time, outcome=encounter_outcome, player_id=player_id)
                    # encounters.append(encounter2add)
                    # encounter2add = self._events2encounter(current_events)
                    encounter2add = Encounter(current_events, self.event_weights, args.margin)
                    if encounter2add.outcome is not None:
                        encounters.append(encounter2add)

                    # current_events = [event]
                    # last_event_time = event.time
                    current_events = []
                    last_event_time = self._add_event(event, current_events)
                else:
                    ### The encounter continues
                    # current_events.append(event)
                    # last_event_time = event.time
                    last_event_time = self._add_event(event, current_events)
            else:
                # current_events.append(event)
                # last_event_time = event.time
                last_event_time = self._add_event(event, current_events)
        else:  # In the case some encounters are not finished after the end of the game
            if len(current_events):
                # encounter2add = self._events2encounter(current_events)
                encounter2add = Encounter(current_events, self.event_weights, args.margin)
                if encounter2add.outcome is not None:
                    encounters.append(encounter2add)

        return encounters

    @staticmethod
    def _add_event(event, current_events):
        current_events.append(event)
        return event.time

    # def _events2encounter(self, events):
    #     events_weights = [self.event_weights[event.event_type] for event in events]
    #     encounter_outcome = self._weights2target(events_weights) * 1
    #     encounter_start_time = events[0].time
    #     encounter = Encounter(time=encounter_start_time, outcome=encounter_outcome, player_id=player_id)
    #
    #     return encounter


if __name__ == '__main__':
    encounter_extractor = EncounterExtractor(min_interval=args.min_interval)

    # match = 'match_3'
    for match in matches:
        path2replay_json = os.path.join(matches_folder, match, 'replay.json')
        path2meta_info = os.path.join(matches_folder, match, 'meta_info.json')
        # events = []
        events4players = defaultdict(list)
        encounters4players = {}
        # player_id = 0

        with open(path2replay_json) as f:
            replay_json = json.load(f)

        with open(path2meta_info) as f:
            meta_info = json.load(f)

        match_result = replay_json['teams']['participants']['win']
        # replay_json['player_0']['killTimes']
        # replay_json['player_0']['deathTimes']

        for raw_event in replay_json['events']:
            if raw_event['type'] == 'CHAMPION_KILL':
                n_assistants = len(raw_event['assistingPlayerIds'])
                if raw_event['killerId'] in player_ids:
                    event = Event(
                        time=raw_event['timestamp'],
                        event_type='kill',
                        player_id=raw_event['killerId'],
                        n_assistants=n_assistants)
                    events4players[raw_event['killerId']].append(event)

                if raw_event['victimId'] in player_ids:
                    event = Event(
                        time=raw_event['timestamp'],
                        event_type='death',
                        player_id=raw_event['victimId'],
                        n_assistants=n_assistants)
                    events4players[raw_event['victimId']].append(event)

                for assisting_player_id in raw_event['assistingPlayerIds']:
                    if assisting_player_id in player_ids:
                        event = Event(
                            time=raw_event['timestamp'],
                            event_type='assist',
                            player_id=assisting_player_id,
                            n_assistants=n_assistants)
                        events4players[assisting_player_id].append(event)

                # event = Event(time=event['timestamp'], event_type=event_type, player_id=player_id)
                # events4players[player_id].append(event)


        # for player_id in player_ids:
        #     # path2player_data = os.path.join(matches_folder, match, f'player_{player_id}')
        #     event4player = replay_json[f'player_{player_id}']
        #
        #     for event_type in event_types:
        #         key4event_type = event_type + 'Times'
        #         event_times = event4player[key4event_type]
        #         for event_time in event_times:
        #             event = Event(time=event_time, event_type=event_type, player_id=player_id)
        #             events4players[player_id].append(event)
        #             # match_events

        # match_events
        # sorted(match_events)
        for player_id in player_ids:
            events4players[player_id] = sorted(events4players[player_id])
            encounters4players[player_id] = encounter_extractor(events4players[player_id])
            # pprint(encounters4players[player_id])

        for player_id, encounters4player in encounters4players.items():
            output_path = os.path.join(matches_processed_folder, match, f'player_{player_id}', 'encounters.json')
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            json_content = []
            for encounter4player in encounters4player:
                time = encounter4player.time
                outcome = encounter4player.outcome
                json_content.append({
                    'time': time,
                    'outcome': outcome,
                })

            with open(output_path, 'w') as f:
                json.dump(json_content, f)








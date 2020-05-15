To extract data for one experimental day:

1. Get game start end times with `python get_game_start_end_times.py --dates YOUR_DATES`

1. Process the data with `python ProcessingRawData.py --dates YOUR_DATES`

1. Fetch replays from RIOT database `python FetchingReplaysData.py --dates YOUR_DATES`

1. Process fetched replays with `python GameDataExtraction.py --dates YOUR_DATES`

1. Process players' responses `python AfterMatchSurveyProcessing`

1. Compose all matches to `matches` folder using `python compose_matches --dates YOUR_DATES`

To create a file with players info run `python PlayerSurveyProcessing.py`
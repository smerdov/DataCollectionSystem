import json
import os
import pandas as pd
from config import *

key_1 = 'score'
key_2 = 'test'
selected_results = {}

path2results = os.path.join(data_folder, 'results_last_2.json')
with open(path2results) as f:
    results = json.load(f)

results.keys()
results['5,2,1'].keys()

selected_results = {key: value[key_1][key_2] for key, value in results.items()}

pd.DataFrame.from_records(selected_results)
# pd.DataFrame(selected_results)




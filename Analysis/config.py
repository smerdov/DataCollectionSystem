import pandas as pd
import matplotlib.pyplot as plt

dataset_folder = '../Dataset/'
data_folder = '../Data/'
pic_folder = '../Pictures/'
API_KEY = 'RGAPI-5c76c858-9d1b-437a-9d2a-2ddc60f486f6'

plt.interactive(True)
pd.options.display.max_columns = 15

summoner_name2player_id_dict = {
    'AE Iromator': '0',
    'TUK Trannas': '1',
}

player_ids = list(summoner_name2player_id_dict.values())



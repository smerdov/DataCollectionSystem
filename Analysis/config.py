import pandas as pd
import matplotlib.pyplot as plt

dataset_folder = '../Dataset/'
data_folder = '../Data/'
pic_folder = '../Pictures/'
API_KEY = 'RGAPI-3e4ae736-1151-4541-9c45-c33593d25987'

plt.interactive(True)
pd.options.display.max_columns = 15

summoner_name2player_id_dicts = {
    'pros': {
        'Reiign': '0',
        'Biotom': '1',
        'TUK hi im ballat': '2',
        'TUK Psytolos': '3',
        'TUK Trannas': '4',
        },
    'amateurs': {
        'oi mori  ': '0',
        'TheSilverTusk': '1',
        'Fillps': '2',
        'ZdadrDeM': '3',
        'Supersaiyarunk3l': '4',
    }
}

# player_ids = list(summoner_name2player_id_dict.values())



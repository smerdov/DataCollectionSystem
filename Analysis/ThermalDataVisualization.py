import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from config import *

# plt.interactive(False)

# thermal_images_path = '../AndroidAppData/'
thermal_images_path = 'Dataset/2019-11-15/player_2/face_temperature/'
filenames = os.listdir(thermal_images_path)

for filenum, filename in enumerate(filenames):
    try:
        thermal_data = pd.read_csv(thermal_images_path + filename, header=None, sep=';').values
        # thermal_data.astype(float)
        thermal_data = thermal_data.T

        # plt.close()
        plt.close()
        fig, ax = plt.subplots()
        ax.imshow(thermal_data, vmax=40, vmin=30, cmap='Blues')
        fig.show()
        fig.savefig(f'{pic_folder}thermal_image_{filenum}.png')
    except:
        print(f'Can\'t read {filename}')




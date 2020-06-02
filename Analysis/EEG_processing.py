import glob
from config import *
import os
import json
import numpy as np

matches_dir = os.path.join(dataset_folder, 'matches')

data_rename_dict = {
    'EEG': ['eeg_band_power', 'imu_head', 'eeg_device_info', 'eeg_metrics'],
}
data_source = 'EEG'

def save2path(path2dir, filename, df):
    path = os.path.join(path2dir, f'{filename}.csv')
    df.to_csv(path)


if __name__ == '__main__':
    eeg_filepaths = glob.glob(f'{matches_dir}/*/*/eeg.csv')


    for eeg_filepath in eeg_filepaths:
        df4game = pd.read_csv(eeg_filepath)
        df4game.set_index(['time'], inplace=True)
        path2dir = os.path.dirname(eeg_filepath)

        ### 'EEG': ['eeg_band_power', 'imu_head', 'eeg_device_info', 'eeg_metrics'],
        # mot_entries = []
        # pow_entries = []
        entries = {
            'mot': [],
            'pow': [],
            'dev': [],
            'met': [],
        }

        time_indexes = {
            'mot': [],
            'pow': [],
            'dev': [],
            'met': [],
        }

        for n_row, row in df4game.iterrows():
            # entry = json.loads(df4data_source.iloc[0, 0])
            entry = json.loads(row['content'])
            key = list(entry.keys())[0]
            if key in entries:
                entries[key].append(entry[key])
                # time_indexes[key].append(row.name / pd.Timedelta(seconds=1))
                time_indexes[key].append(row.name)
            else:
                print(f'Unknown entry {entry}')
                # raise ValueError(f'Unknown entry {entry}')

        ### pow --- Band Power
        df_pow = pd.DataFrame(np.array(entries['pow']))
        df_pow.columns = [
            "AF3/theta", "AF3/alpha", "AF3/betaL", "AF3/betaH", "AF3/gamma",
            "T7/theta", "T7/alpha", "T7/betaL", "T7/betaH", "T7/gamma",
            "Pz/theta", "Pz/alpha", "Pz/betaL", "Pz/betaH", "Pz/gamma",
            "T8/theta", "T8/alpha", "T8/betaL", "T8/betaH", "T8/gamma",
            "AF4/theta", "AF4/alpha", "AF4/betaL", "AF4/betaH", "AF4/gamma"
        ]
        df_pow['time'] = np.array(time_indexes['pow'])
        df_pow.set_index(['time'], inplace=True)
        filename = data_rename_dict[data_source][0]
        save2path(path2dir, filename, df_pow)

        ### mot --- Head Motion (IMU)
        df_mot = pd.DataFrame(np.array(entries['mot'])[:, 2:])
        df_mot.columns = ['acc_x', 'acc_y', 'acc_z', 'mag_x', 'mag_y', 'mag_z', 'q0', 'q1',
                          'q2', 'q3']
        # df_mot['mag_y'].mean()
        # df_mot['mag_y'].max()
        # df_mot['mag_y'].min()
        # df_mot['acc_x'].mean()
        # df_mot.set_index(time_indexes['mot'], inplace=True)
        df_mot['time'] = np.array(time_indexes['mot'])
        df_mot.set_index(['time'], inplace=True)
        filename = data_rename_dict[data_source][1]
        save2path(path2dir, filename, df_mot)

        ### dev --- Device Info
        df_dev = pd.DataFrame(np.array(entries['dev']))
        # df_dev = df_dev.append(df_dev[2].apply(lambda x: pd.Series(x)))
        df_dev = pd.concat([df_dev, df_dev[2].apply(lambda x: pd.Series(x))], axis=1)
        df_dev.columns = ["Battery", "Signal", 'tmp', "AF3", "T7", "Pz", "T8", "AF4"]
        df_dev.drop(columns='tmp', inplace=True)
        # df_dev.set_index(time_indexes['dev'], inplace=True)
        df_dev['time'] = np.array(time_indexes['dev'])
        df_dev.set_index(['time'], inplace=True)
        filename = data_rename_dict[data_source][2]
        save2path(path2dir, filename, df_dev)

        ### met --- EEG Metrics
        df_met = pd.DataFrame(np.array(entries['met']))
        df_met.columns = [
            "Engagement.isActive", "Engagement",
            "Excitement.isActive", "Excitement", "Long term excitement",
            "Stress.isActive", "Stress",
            "Relaxation.isActive", "Relaxation",
            "Interest.isActive", "Interest",
            "Focus.isActive", "Focus",
        ]
        # df_met.columns = [
        #     "eng.isActive", "eng",
        #     "exc.isActive", "exc", "lex",
        #     "str.isActive", "str",
        #     "rel.isActive", "rel",
        #     "int.isActive", "int",
        #     "foc.isActive", "foc"
        # ]
        # df_met.set_index(time_indexes['met'], inplace=True)
        df_met['time'] = np.array(time_indexes['met'])
        df_met.set_index(['time'], inplace=True)
        filename = data_rename_dict[data_source][3]
        save2path(path2dir, filename, df_met)

        os.remove(eeg_filepath)
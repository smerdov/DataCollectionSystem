import pandas as pd

class GeneralAnalyser:

    def __init__(self,
                 df,
                 pic_prefix,
                 sensor_name,
                 session_id,
                 name=None,
                 ):
        self.df = df
        self.pic_prefix = pic_prefix
        self.sensor_name = sensor_name
        self.session_id = session_id
        self.name = name  # Need to be elaborated

    def get_dummy_features(self):
        column_means = self.df.mean(axis=0).to_dict()

        column_means = pd.Series(column_means, name=self.session_id)

        return column_means
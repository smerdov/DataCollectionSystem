To process the dataset:

1. Smoothed and preliminary resample data: `python SensorDataProcessing.py --resample-string 5s`

1. Extract information about encounters: `python EncountersProcessing.py`

1. Prepare training tensors for training: `python EncountersDatasetCreation.py`

1. Train a network: `python RNN.py`

1. Train a network: `python ClassicalML.py`
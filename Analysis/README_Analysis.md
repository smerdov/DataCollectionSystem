To process the dataset:

1. Smoothed and preliminary resample data: `python SensorDataProcessing.py --resample-string 5s`

1. Extract information about encounters: `python EncountersProcessing.py`

1. Prepare training tensors for training: `python TensorsCreation.py --resample-string 30s`

1. Traing a network: `python NN.py`
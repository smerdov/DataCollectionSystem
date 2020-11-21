This is code for sensor data collection for eSports players.
We used this code to simultaneously collect sensor data from 5 players in League of Legends.
The code collects data from the following sensors:

1. Electromyography sensor (EMG) _Grove EMG Sensor v1.1_ (captures muscle activity).
1. Galvanic skin response sensor (GSR) _Grove GSR Sensor v1.2_ (captures stress level).
1. Inertial measurement unit (IMU) _Bosch BNO055_ (captures movements).
1. Environmental atmosphere sensor _Bosch BME280_ (captures temperature, humidity, etc.).
1. CO2 sensor _MH-Z19B_.
1. Eye tracker Tobii 4C (captures eye movements, pupil diameter).
1. Electroencephalography (EEG) headset _Emotiv Insight_ (captures brain activity).
1. Infrared camera _Flir One_ (captures facial skin temperature).
1. Heart rate monitor _Polar OH1_ (captures stress level).
1. Pulse-oximeter sensor _Maxim MAX30102_ (captures oxygen saturation level).
1. Keyboard and mouse activity.

The dataset collected using this code is described in [this paper](https://arxiv.org/abs/2011.00958).
If you find the code or the paper interesting, please feel free to cite it as:

```
@article{smerdov2020collection,
  title={Collection and Validation of Psychophysiological Data from Professional and Amateur Players: a Multimodal eSports Dataset},
  author={Smerdov, Anton and Zhou, Bo and Lukowicz, Paul and Somov, Andrey},
  journal={arXiv preprint arXiv:2011.00958},
  year={2020}
}
```




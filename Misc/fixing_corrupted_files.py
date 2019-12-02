import pandas as pd

content = []

with open('/Volumes/NO NAME/arduino_1_playerID_3_2019-11-15-13-11-28.csv') as f:
    while True:
        try:
            line_content = f.readline()
            content.append(line_content)
        except:
            # print('Error')
            pass






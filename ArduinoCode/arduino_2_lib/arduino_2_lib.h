#ifndef arduino_2_lib
#define arduino_2_lib

#include "../eSportsLibrary/eSportsLibrary.h"
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"


extern const int ArduinoTypeID;
extern const int IDLE_DELAY;

//extern Adafruit_BME280 bme; //I2C
//extern Adafruit_BNO055 bno;

extern std::vector<String> columns;

void arduinoInit();
void Task_WritingData(void *pvParameters);
void Task_ReadingData(void *pvParameters);


#endif //TEST_LIBRARY_H

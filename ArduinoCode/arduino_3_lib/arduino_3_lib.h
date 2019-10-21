#ifndef arduino_3_lib
#define arduino_3_lib

#include "../eSportsLibrary/eSportsLibrary.h"
#include <Adafruit_BME280.h>
#include <SparkFun_GridEYE_Arduino_Library.h>
#include <Wire.h>


extern const int ArduinoTypeID;
extern const int IDLE_DELAY;

//extern Adafruit_BME280 bme; //I2C
extern Adafruit_BNO055 bno;

extern std::vector<String> columns;

void bmeInit();
void bnoInit();
void arduinoInit();
void Task_WritingData(void *pvParameters);
void Task_ReadingData(void *pvParameters);


#endif //TEST_LIBRARY_H

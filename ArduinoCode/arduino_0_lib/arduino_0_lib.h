#ifndef arduino_0_lib
#define arduino_0_lib

#include "../eSportsLibrary/eSportsLibrary.h"
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

extern const int ArduinoTypeID;
extern const int IDLE_DELAY;

extern Adafruit_BME280 bme; //I2C
extern Adafruit_BNO055 bno;

extern std::vector<String> columns;

void bmeInit();
void bnoInit();
void arduinoInit();
void Task_WritingData(void *pvParameters);
void Task_ReadingData(void *pvParameters);


#endif //TEST_LIBRARY_H

#ifndef arduino_3_lib
#define arduino_3_lib

#include "../eSportsLibrary/eSportsLibrary.h"
#include <Adafruit_BME280.h>
#include "MHZ19.h"

extern const int ArduinoTypeID;
extern const int IDLE_DELAY;

extern std::vector<String> columns;

void arduinoInit();
void Task_WritingData(void *pvParameters);
void Task_ReadingData(void *pvParameters);


#endif //TEST_LIBRARY_H

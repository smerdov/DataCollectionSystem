#include "arduino_4_lib.h"

const int ArduinoTypeID = 4;

Adafruit_BNO055 bno_0 = Adafruit_BNO055(55, BNO055_ADDRESS_A);
Adafruit_BNO055 bno_1 = Adafruit_BNO055(56, BNO055_ADDRESS_B);
//Adafruit_BNO055 bno = bno_0;

struct measurementsStruct{
    String current_time;
    float face_temparature_hottest;
};

std::vector<String> columns = {
    "Timestamp",
    "FaceTemperatureHottest",
};

int incr = 0;
const int QUEUE_SIZE = 500;
struct measurementsStruct dataArray[QUEUE_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;
int pixelTable[64];

float testPixelValue = 0;




void grideyeInit(){
    // Start your preferred I2C object
    Wire.begin();
    // Library assumes "Wire" for I2C but you can pass something else with begin() if you like
    grideye.begin();
}

void arduinoInit(){
    grideyeInit();
}


void Task_ReadingData(void *pvParameters){
    while (true) {
        if (do_measurements) {
            //      sensors_event_t event;
            //      bno.getEvent(&event);
            struct measurementsStruct measurements;

            measurements.current_time = dateTime(TIME_FORMAT);
            
            float hotPixelValue = 0;
            int hotPixelIndex = 0;

            for(unsigned char i = 0; i < 64; i++){
                testPixelValue = grideye.getPixelTemperature(i);
                if (testPixelValue > hotPixelValue){
                    hotPixelValue = testPixelValue;
                    hotPixelIndex = i;
                }
            }

            measurements.face_temparature_hottest = hotPixelValue;

            dataArray[incr] = measurements;
            
            P_send = dataArray+incr;
            
            incr = (incr + 1) % QUEUE_SIZE;
            
            xQueueSend(queue, &P_send, portMAX_DELAY);
//            delay(1);
        } else {
            delay(IDLE_DELAY);  // THAT'S JUST IN CASE do_measurements == false
        }
    }
}

void Task_WritingData(void *pvParameters){
    while (true) {
        xQueueReceive(queue, &P_receive, portMAX_DELAY);
        
        myFile.print(P_receive -> current_time);
        myFile.print(DELIMITER);
        

        

        myFile.print('\n');
        myFile.flush();
    }
}


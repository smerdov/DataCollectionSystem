#include "arduino_2_lib.h"

const int ArduinoTypeID = 2;

//Adafruit_BNO055 bno_0 = Adafruit_BNO055(55, BNO055_ADDRESS_A);
//Adafruit_BNO055 bno_1 = Adafruit_BNO055(56, BNO055_ADDRESS_B);
//Adafruit_BNO055 bno = bno_0;

struct measurementsStruct{
    String current_time;
    long irValue;
    long redValue;
//    long greenValue;
};

std::vector<String> columns = {
    "Timestamp",
    "irValue",
    "redValue",
//    "greenValue",
};

int incr = 0;
const int QUEUE_SIZE = 500;
struct measurementsStruct dataArray[QUEUE_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;

MAX30105 particleSensor;

const byte RATE_SIZE = 10; //Increase this for more averaging. 4 is good.
byte rates[RATE_SIZE]; //Array of heart rates
byte rateSpot = 0;
long lastBeat = 0; //Time at which the last beat occurred
long lastBeatTimes[RATE_SIZE] = {0};

//float beatsPerMinute;
//int beatAvg;
float heartrate, instantaneousBeatsPerMinute;
int n_sample = 0;
long irValue, redValue, greenValue;

bool isBadData(measurementsStruct measurements){
    if (measurements.irValue < 50000) {
        return true;
    } else {
        return false;
    }
}

void maxInit()
{
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) //Use default I2C port, 400kHz speed
  {
    Serial.println("MAX30105 was not found. Please check wiring/power. ");
    while (1);
  }
//  Serial.println("Place your index finger on the sensor with steady pressure.");

  particleSensor.setup(); //Configure sensor with default settings
//  particleSensor.setPulseAmplitudeRed(0x0A); //Turn Red LED to low to indicate sensor is running
//  particleSensor.setPulseAmplitudeGreen(0); //Turn off Green LED

}

void arduinoInit(){
    maxInit();
}


void Task_ReadingData(void *pvParameters){
    while (true) {
        if (do_measurements) {
            irValue = particleSensor.getIR();
            redValue = particleSensor.getRed();
//            greenValue = particleSensor.getGreen();

//            if (checkForBeat(irValue) == false){
//                continue;
//            }
//
//            n_sample++;
//
//            long current_beat_time = millis();
//            long delta = current_beat_time - lastBeatTimes[RATE_SIZE-1];
//            instantaneousBeatsPerMinute = 60 / (delta / 1000.0);
//            if (instantaneousBeatsPerMinute > 255 || instantaneousBeatsPerMinute < 20){  // Filter for fake detections
//                Serial.println("Strange beat!");
////                  continue
//            } else {
//                Serial.println("Got a normal beat!");
//            }
//
//            long timedelta4beats = current_beat_time - lastBeatTimes[0];
//            heartrate = (1000. * 60. * RATE_SIZE) / (timedelta4beats);
//
//            for (int i=1; i < RATE_SIZE; i++){
//                lastBeatTimes[i-1] = lastBeatTimes[i];
//            }
//
//            lastBeatTimes[RATE_SIZE-1] = current_beat_time;
//
//            if (n_sample < RATE_SIZE) {
//                continue;
//            }

            struct measurementsStruct measurements;
            measurements.current_time = dateTime(TIME_FORMAT);
            measurements.irValue = irValue;
            measurements.redValue = redValue;
//            measurements.greenValue = greenValue;

            dataArray[incr] = measurements;
            bad_data = isBadData(measurements);

            
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
        
        myFile.print(P_receive -> irValue);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> redValue);
//        myFile.print(DELIMITER);
//
//        myFile.print(P_receive -> greenValue);
////        myFile.print(DELIMITER);

        myFile.print('\n');
        myFile.flush();
    }
}





#include "arduino_3_lib.h"

#define BAUDRATE 9600 // For the CO2 sensor
const int ArduinoTypeID = 3;

//Adafruit_BNO055 bno_0 = Adafruit_BNO055(55, BNO055_ADDRESS_A);
//Adafruit_BNO055 bno_1 = Adafruit_BNO055(56, BNO055_ADDRESS_B);
Adafruit_BME280 bme;
MHZ19 myMHZ19;

struct measurementsStruct{
    String current_time;
    float temperature;
    float pressure;
    float altitude;
    float humidity;
    int co2;
};

std::vector<String> columns = {
    "Timestamp",
    "Temperature",
    "Pressure",
    "Altitude",
    "Humidity",
    "CO2",
};

int incr = 0;
const int QUEUE_SIZE = 500;
struct measurementsStruct dataArray[QUEUE_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;
int last_co2_level = -1;
unsigned long last_co2_measurement_time = 0;
int co2_measurement_period = 30 * 1000;


void bmeInit(){
    if (!bme.begin(0x76)) { //Alternative I2C address
      Serial.println("BME280 Sensor was not detected, check wiring!");
      while(1);
    }
}

void mhz19Init(){
    Serial1.begin(BAUDRATE);
    myMHZ19.begin(Serial1);
}

void arduinoInit(){
    bmeInit();
    mhz19Init();
}


void Task_ReadingData(void *pvParameters){
    while (true) {
        if (do_measurements) {
            //      sensors_event_t event;
            //      bno.getEvent(&event);
            struct measurementsStruct measurements;

            measurements.current_time = dateTime(TIME_FORMAT);
            measurements.temperature = bme.readTemperature();
            measurements.pressure = (bme.readPressure() / 100.0F);
            measurements.altitude = bme.readAltitude(SEALEVELPRESSURE_HPA);
            measurements.humidity = bme.readHumidity();

            if (millis() - last_co2_measurement_time > co2_measurement_period) {
                last_co2_measurement_time = millis();
                last_co2_level = myMHZ19.getCO2();
            }

            measurements.co2 = last_co2_level;

            dataArray[incr] = measurements;
            
            P_send = dataArray+incr;
            
            incr = (incr + 1) % QUEUE_SIZE;
            
            xQueueSend(queue, &P_send, portMAX_DELAY);
            delay(993);
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

        myFile.print(P_receive -> temperature);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> pressure);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> altitude);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> humidity);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> co2);

        myFile.print('\n');
        myFile.flush();
    }
}


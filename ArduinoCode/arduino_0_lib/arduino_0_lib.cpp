#include "arduino_0_lib.h"

const int ArduinoTypeID = 0;

Adafruit_BME280 bme;
Adafruit_BNO055 bno = Adafruit_BNO055(55);

struct measurementsStruct{
  String current_time;
  float temperature;
  float pressure;
  float altitude;
  float humidity;
  float linaccel_x;
  float linaccel_y;
  float linaccel_z;
  float gravity_x;
  float gravity_y;
  float gravity_z;
  float gyro_x;
  float gyro_y;
  float gyro_z;
  float euler_x;
  float euler_y;
  float euler_z;
  float quaternion_w;
  float quaternion_y;
  float quaternion_x;
  float quaternion_z;
};

std::vector<String> columns = {
  "Timestamp",
  "Temperature",
  "Pressure",
  "Altitude",
  "Humidity",
  "linaccel_x",
  "linaccel_y",
  "linaccel_z",
  "gravity_x",
  "gravity_y",
  "gravity_z",
  "gyro_x",
  "gyro_y",
  "gyro_z",
  "euler_x",
  "euler_y",
  "euler_z",
  "quaternion_w",
  "quaternion_y",
  "quaternion_x",
  "quaternion_z",
};

int incr = 0;
const int QUEUE_SIZE = 100;
struct measurementsStruct dataArray[QUEUE_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;

void bmeInit(){
    if (!bme.begin(0x76)) { //Alternative I2C address
      Serial.println("BME280 Sensor was not detected, check wiring!");
      while(1);
    }
}


void bnoInit(){
    if(!bno.begin())
    {
      Serial.println("BNO055 Sensor was not detected, check wiring!");
      while(1);
    }

    bno.setExtCrystalUse(true);

    pinMode(33, OUTPUT);
    digitalWrite(33, HIGH);
}

void arduinoInit(){
    bmeInit();
    bnoInit();
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

      imu::Vector<3> linaccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
      imu::Vector<3> gravity = bno.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
      imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
      imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
      imu::Quaternion quaternion = bno.getQuat();

      measurements.linaccel_x = linaccel.x();
      measurements.linaccel_y = linaccel.y();
      measurements.linaccel_z = linaccel.z();
      
      measurements.gravity_x = gravity.x();
      measurements.gravity_y = gravity.y();
      measurements.gravity_z = gravity.z();

      measurements.gyro_x = gyro.x();
      measurements.gyro_y = gyro.y();
      measurements.gyro_z = gyro.z();
      
      measurements.euler_x = euler.x();
      measurements.euler_y = euler.y();
      measurements.euler_z = euler.z();

      measurements.quaternion_w = quaternion.w();
      measurements.quaternion_y = quaternion.y();
      measurements.quaternion_x = quaternion.x();
      measurements.quaternion_z = quaternion.z();
        
      dataArray[incr] = measurements;
  
      P_send = dataArray+incr;
  
      incr = (incr + 1) % QUEUE_SIZE;
    
      xQueueSend(queue, &P_send, portMAX_DELAY);
      delay(5);
    } else {
      delay(5);  // THAT'S JUST IN CASE do_measurements == false
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

    myFile.print(P_receive -> linaccel_x);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> linaccel_y);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> linaccel_z);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> gravity_x);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> gravity_y);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> gravity_z);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> gyro_x, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> gyro_y, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> gyro_z, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> euler_x, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> euler_y, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> euler_z, N_DIGITS_PRECISION);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> quaternion_w, 2 * N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> quaternion_y, 2 * N_DIGITS_PRECISION);
    myFile.print(DELIMITER);
    
    myFile.print(P_receive -> quaternion_x, 2 * N_DIGITS_PRECISION);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> quaternion_z, 2 * N_DIGITS_PRECISION);
//    myFile.print(DELIMITER);
    
    myFile.print('\n');
    myFile.flush();
  }
}


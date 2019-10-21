#include "arduino_0_lib.h"

const int ArduinoTypeID = 0;

Adafruit_BNO055 bno_0 = Adafruit_BNO055(55, BNO055_ADDRESS_A);
Adafruit_BNO055 bno_1 = Adafruit_BNO055(56, BNO055_ADDRESS_B);

struct measurementsStruct{
    String current_time;
    int gsr;
    int emg_0;
    int emg_1;
    float linaccel_x_0;
    float linaccel_y_0;
    float linaccel_z_0;
    float gravity_x_0;
    float gravity_y_0;
    float gravity_z_0;
    float gyro_x_0;
    float gyro_y_0;
    float gyro_z_0;
    float euler_x_0;
    float euler_y_0;
    float euler_z_0;
    float quaternion_w_0;
    float quaternion_y_0;
    float quaternion_x_0;
    float quaternion_z_0;
    float linaccel_x_1;
    float linaccel_y_1;
    float linaccel_z_1;
    float gravity_x_1;
    float gravity_y_1;
    float gravity_z_1;
    float gyro_x_1;
    float gyro_y_1;
    float gyro_z_1;
    float euler_x_1;
    float euler_y_1;
    float euler_z_1;
    float quaternion_w_1;
    float quaternion_y_1;
    float quaternion_x_1;
    float quaternion_z_1;
};

std::vector<String> columns = {
    "Timestamp",
    "gsr",
    "emg_0",
    "emg_1",
    "linaccel_x_0",
    "linaccel_y_0",
    "linaccel_z_0",
    "gravity_x_0",
    "gravity_y_0",
    "gravity_z_0",
    "gyro_x_0",
    "gyro_y_0",
    "gyro_z_0",
    "euler_x_0",
    "euler_y_0",
    "euler_z_0",
    "quaternion_w_0",
    "quaternion_y_0",
    "quaternion_x_0",
    "quaternion_z_0",
    "linaccel_x_1",
    "linaccel_y_1",
    "linaccel_z_1",
    "gravity_x_1",
    "gravity_y_1",
    "gravity_z_1",
    "gyro_x_1",
    "gyro_y_1",
    "gyro_z_1",
    "euler_x_1",
    "euler_y_1",
    "euler_z_1",
    "quaternion_w_1",
    "quaternion_y_1",
    "quaternion_x_1",
    "quaternion_z_1",
};

int incr = 0;
const int QUEUE_SIZE = 500;
struct measurementsStruct dataArray[QUEUE_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;

const int GSRPin = A2;
const int EMG0Pin = A3;
const int EMG1Pin = A4;

uint8_t uch_dummy;

void bnoInit(Adafruit_BNO055 bno, String bno_name){
    if(!bno.begin())
    {
        Serial.println("BNO055 Sensor " + bno_name + " was not detected, check wiring!");
        while(1);
    }

    bno.setExtCrystalUse(true);

    pinMode(33, OUTPUT);
    digitalWrite(33, HIGH);
}

//void maxInit(){
//    maxim_max30102_reset();
//
//    maxim_max30102_read_reg(REG_INTR_STATUS_1, &uch_dummy); //Reads/clears the interrupt status register
//    delay(100);
//    uch_dummy = Serial.read();
//
//    maxim_max30102_init();
//}


///* MAX30102 */
//  //maxim_max30102_init();  //initialize the MAX30102
//
//  //for(i=0;i<2;i++)
//  //{
//  while (digitalRead(13) == 1); //wait until the interrupt pin asserts
//  maxim_max30102_read_fifo(&aun_red_buffer, &aun_ir_buffer);  //read from MAX30102 FIFO
//  //}
//
//  //maxim_heart_rate_and_oxygen_saturation(aun_ir_buffer, n_ir_buffer_length, aun_red_buffer, &n_spo2, &ch_spo2_valid, &n_heart_rate, &ch_hr_valid);
//
//  if (aun_ir_buffer == 0x00000000 || aun_red_buffer == 0x00000000) {
//    aun_ir_buffer = 0x00000001;
//    aun_red_buffer = 0x00000001;
//  }
//
//  BT_data.s_aun_ir_buffer[0] = ((aun_ir_buffer & 0xFF000000) >> 24);
//  BT_data.s_aun_ir_buffer[1] = ((aun_ir_buffer & 0x00FF0000) >> 16);
//  BT_data.s_aun_ir_buffer[2] = ((aun_ir_buffer & 0x0000FF00) >> 8);
//  BT_data.s_aun_ir_buffer[3] = aun_ir_buffer & 0x000000FF;
//
//  BT_data.s_aun_red_buffer[0] = ((aun_red_buffer & 0xFF000000) >> 24);
//  BT_data.s_aun_red_buffer[1] = ((aun_red_buffer & 0x00FF0000) >> 16);
//  BT_data.s_aun_red_buffer[2] = ((aun_red_buffer & 0x0000FF00) >> 8);
//  BT_data.s_aun_red_buffer[3] = aun_red_buffer & 0x000000FF;
//
//  Serial.print(F("red="));
//  Serial.print(aun_red_buffer, DEC);
//  Serial.print(F(", ir="));
//  Serial.println(aun_ir_buffer, DEC);



void arduinoInit(){
    bnoInit(bno_0, "bno_0");
    bnoInit(bno_1, "bno_1");
}

void Task_ReadingData(void *pvParameters){
  while (true) {
    if (do_measurements) {
//      sensors_event_t event;
//      bno.getEvent(&event);
      struct measurementsStruct measurements;

      measurements.current_time = dateTime(TIME_FORMAT);
      measurements.gsr = analogRead(GSRPin);
      measurements.emg_0 = analogRead(EMG0Pin);
      measurements.emg_1 = analogRead(EMG1Pin);

      imu::Vector<3> linaccel_0 = bno_0.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
            imu::Vector<3> gravity_0 = bno_0.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
            imu::Vector<3> gyro_0 = bno_0.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
            imu::Vector<3> euler_0 = bno_0.getVector(Adafruit_BNO055::VECTOR_EULER);
            imu::Quaternion quaternion_0 = bno_0.getQuat();

            imu::Vector<3> linaccel_1 = bno_1.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
            imu::Vector<3> gravity_1 = bno_1.getVector(Adafruit_BNO055::VECTOR_GRAVITY);
            imu::Vector<3> gyro_1 = bno_1.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
            imu::Vector<3> euler_1 = bno_1.getVector(Adafruit_BNO055::VECTOR_EULER);
            imu::Quaternion quaternion_1 = bno_1.getQuat();

            measurements.linaccel_x_0 = linaccel_0.x();
            measurements.linaccel_y_0 = linaccel_0.y();
            measurements.linaccel_z_0 = linaccel_0.z();

            measurements.gravity_x_0 = gravity_0.x();
            measurements.gravity_y_0 = gravity_0.y();
            measurements.gravity_z_0 = gravity_0.z();

            measurements.gyro_x_0 = gyro_0.x();
            measurements.gyro_y_0 = gyro_0.y();
            measurements.gyro_z_0 = gyro_0.z();

            measurements.euler_x_0 = euler_0.x();
            measurements.euler_y_0 = euler_0.y();
            measurements.euler_z_0 = euler_0.z();

            measurements.quaternion_w_0 = quaternion_0.w();
            measurements.quaternion_y_0 = quaternion_0.y();
            measurements.quaternion_x_0 = quaternion_0.x();
            measurements.quaternion_z_0 = quaternion_0.z();

            measurements.linaccel_x_1 = linaccel_1.x();
            measurements.linaccel_y_1 = linaccel_1.y();
            measurements.linaccel_z_1 = linaccel_1.z();

            measurements.gravity_x_1 = gravity_1.x();
            measurements.gravity_y_1 = gravity_1.y();
            measurements.gravity_z_1 = gravity_1.z();

            measurements.gyro_x_1 = gyro_1.x();
            measurements.gyro_y_1 = gyro_1.y();
            measurements.gyro_z_1 = gyro_1.z();

            measurements.euler_x_1 = euler_1.x();
            measurements.euler_y_1 = euler_1.y();
            measurements.euler_z_1 = euler_1.z();

            measurements.quaternion_w_1 = quaternion_1.w();
            measurements.quaternion_y_1 = quaternion_1.y();
            measurements.quaternion_x_1 = quaternion_1.x();
            measurements.quaternion_z_1 = quaternion_1.z();
        
      dataArray[incr] = measurements;
  
      P_send = dataArray+incr;
  
      incr = (incr + 1) % QUEUE_SIZE;
    
      xQueueSend(queue, &P_send, portMAX_DELAY);
      delay(10);
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

    myFile.print(P_receive -> gsr);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> emg_0);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> emg_1);
    myFile.print(DELIMITER);

    myFile.print(P_receive -> linaccel_x_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> linaccel_y_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> linaccel_z_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_x_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_y_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_z_0);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_x_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_y_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_z_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_x_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_y_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_z_0, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_w_0, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_y_0, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_x_0, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_z_0, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> linaccel_x_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> linaccel_y_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> linaccel_z_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_x_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_y_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gravity_z_1);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_x_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_y_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> gyro_z_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_x_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_y_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> euler_z_1, N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_w_1, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_y_1, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_x_1, 2 * N_DIGITS_PRECISION);
        myFile.print(DELIMITER);

        myFile.print(P_receive -> quaternion_z_1, 2 * N_DIGITS_PRECISION);
    
    myFile.print('\n');
    myFile.flush();
  }
}


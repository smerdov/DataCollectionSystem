#include <ezTime.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <SPI.h>
#include "SdFat.h"
#include <list>
//#include <string>
//#include <sstream>
#include <stdlib.h>
#include <ESP32_FTPClient.h>


String TIME_FORMAT = "Y-m-d-H:i:s.v"; // or '%Y-%m-%d-%H:%M:%S.%f' in python
String TIME_FORMAT4FILES = "Y-m-d-H:i:s";
const int TIME_FORMAT4FILES_LEN = 19;

//const char* ssid     = "OnePlusAnton";
//const char* password = "79998039003";
//const char* ssid     = "DFKI-PSK";
//const char* password = "50FSCN=j";
//const char* ssid     = "eSportsResearch";
//const char* password = "researchesports";
const char* ssid     = "DFKI-GLAS";
const char* password = "GG-FB-EI-p!";

//WiFiServer server(3000);
WiFiUDP udp;
const int udpPortIn = 3000;
const int ArduinoTypeID = 0;
const int playerID = 0;

const int udpPortOut = 10000 + ArduinoTypeID * 10 + playerID;
//char * udpAddress = "192.168.31.216"; // your pc ip
char udpAddress[20] = "192.168.31.216"; // your pc ip

char ftpAddress[20] = "192.168.31.216";
char ftp_user[20]   = "test";
char ftp_pass[20]   = "test";

//ESP32_FTPClient ftp (ftpAddress,ftp_user,ftp_pass, 5000, 2);

//IPAddress local_IP(192, 168, 31, 100);
//IPAddress gateway(192, 168, 31, 254);
//IPAddress subnet(255, 255, 255, 0);

SdFat SD;

#define SEALEVELPRESSURE_HPA (1014) //Sea level Kaiserslautern on August 20th
#define SD_CS_PIN 33 //File: "pins_arduino.h" Slave Select
#define SDSPEED SD_SCK_MHZ(20) //SPI by default works in 50MHz, but since I am working with ESP32, it is recommended to test other frequencies

File myFile;

Adafruit_BME280 bme; //I2C
Adafruit_BNO055 bno = Adafruit_BNO055(55);
Timezone timezone;
String current_time;
const char DELIMITER = ',';
const int N_DIGITS_PRECISION = 4;
bool do_measurements = false;

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

String start_time;
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

QueueHandle_t queue;
TaskHandle_t WritingData, ReadingData, GettingCommands;

int incr = 0;
const int DATA_BUFFER_SIZE = 100;
struct measurementsStruct dataArray[DATA_BUFFER_SIZE];
struct measurementsStruct *P_send = dataArray;
struct measurementsStruct *P_receive = NULL;

std::vector<String> getFilesInInterval(String date_start, String date_end);

void setup() {
  ////////////////////////////////////////////
  // SERIAL INITIALIZATION
  Serial.begin(115200);

  delay(10000);

  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  if (!bme.begin(0x76)) { //Alternative I2C address
    Serial.println("BME280 Sensor was not detected, check wiring!");
    while(1);
  }

  if(!bno.begin())
  {
    Serial.println("BNO055 Sensor was not detected, check wiring!");
    while(1);
  }
  
  bno.setExtCrystalUse(true);

  pinMode(33, OUTPUT);
  digitalWrite(33, HIGH);

  ////////////////////////////////////////////
  // Wi-Fi setup

  // If you need a static IP
//  if (!WiFi.config(local_IP, gateway, subnet)) {
//      Serial.println("STA Failed to configure");
//  }

  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password); // NO COMMENT

  while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

//  server.begin();
  udp.begin(udpPortIn);
  Serial.print("udpPortOut = ");
  Serial.println(udpPortOut);

  pinMode(LED_BUILTIN, OUTPUT);

  ////////////////////////////////////////////

  ////////////////////////////////////////////
  // TIME SYNCHRONIZATION

  Serial.println("TIME SYNCHRONIZATION PART");
  timeSynchronization();
  Serial.println("Waiting 1s delay...");
  delay(1000);
  timezoneSet();

  // JUST TEST
//  String start_time = dateTime(TIME_FORMAT);
  String current_time = dateTime(TIME_FORMAT4FILES);
  Serial.print("Current time:");
  Serial.println(current_time);

  ////////////////////////////////////////////

  ////////////////////////////////////////////
  // SD Card set up
  Serial.println();
  Serial.print("Initializing SD card..");
  
  if(!SD.begin(SD_CS_PIN, SDSPEED)){
    Serial.println();
    Serial.println("Initialization failed!");
    while(1);
  }

  Serial.println();
  Serial.println("Initialization done.");

  ////////////////////////////////////////////
  
  ////////////////////////////////////////////

  // ACTUAL START

  queue = xQueueCreate(100, sizeof(struct sensor *) );
  if(queue == NULL) {
    Serial.println("Error creating the queue");
  }

  xTaskCreatePinnedToCore(
                    Task_ReadingData,
                    "ReadingData",
                    10000,
                    NULL,
                    2, 
                    &ReadingData,
                    0); 
  
  xTaskCreatePinnedToCore(
                    Task_WritingData,    // Task function
                    "WritingData",       // A name just for humans
                    10000,          // This stack size can be checked & adjusted by reading the Stack Highwater
                    NULL,           // Parameter of the task
                    2,              // Priority
                    &WritingData,        // Task handle to keep the track of the created task
                    1);             // Pink task to core 0

  xTaskCreatePinnedToCore( 
                    Task_GettingCommands,
                    "GettingCommands",
                    10000,
                    NULL,
                    2, 
                    &GettingCommands,
                    1); 
                    
}

void loop() {

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
  
      incr = (incr + 1) % DATA_BUFFER_SIZE;
    
      xQueueSend(queue, &P_send, portMAX_DELAY);
      delay(50);
    } else {
      delay(50);  // THAT'S JUST IN CASE do_measurements == false
    }
  }
}

void Task_GettingCommands(void *pvParameters){
//  WiFiClient client;
  String currentLine = "";
  Serial.println("Waiting for a starting signal...");
  
  while (true) {
    uint8_t buffer[50];
//    String buffer;
    memset(buffer, 0, 50);
    udp.parsePacket();
    char x;
    //receive response from server, it will be HELLO WORLD
    while (udp.available()) {
      x = (char) udp.read();
      currentLine += x;
//      Serial.print(x);
    }

    if (currentLine != "") {
      Serial.print("Got command: ");
      Serial.println(currentLine);
//      Serial.println("Sending back...");
      

      if (currentLine == "start") {
        measurementsStart();
        sendMessage("Starting measurements...");
      } else if (currentLine == "end") {
        measurementsEnd();
        sendMessage("Ending measurements...");
      } else if (currentLine == "status") {
        String current_status = getStatus();
        Serial.println(current_status);
        sendMessage(current_status);
        currentLine = "";
      } else if (currentLine.startsWith("upload")) {
        String date4files_start = currentLine.substring(7, 7 + TIME_FORMAT4FILES_LEN);
        String date4files_end = currentLine.substring(7 + TIME_FORMAT4FILES_LEN + 1, 7 + TIME_FORMAT4FILES_LEN + 1 + TIME_FORMAT4FILES_LEN);
        Serial.println("Uploading files in the interval from " + date4files_start + " to " + date4files_end);
        auto filesInInterval = getFilesInInterval(date4files_start, date4files_end);
        for (auto filename: filesInInterval) {
           sendFileFTP(filename);
        }
      } else if (currentLine == "time_sync") {
        timeSynchronization();
        String current_time = dateTime(TIME_FORMAT);
        sendMessage("current_time: " + current_time);
      } else if (currentLine.startsWith("set udp")) {
        String udpAddressNew = currentLine.substring(8);
        char udpAddressNewChars[udpAddressNew.length() + 1];
        strcpy(udpAddressNewChars, udpAddressNew.c_str());
        setUdpAddress(udpAddressNewChars);
//        delay(10);
        sendMessage("Done command " + currentLine);
      } else if (currentLine.startsWith("set ftp")) {
        String ftpAddressNew = currentLine.substring(8);
        char ftpAddressNewChars[ftpAddressNew.length() + 1];
        strcpy(ftpAddressNewChars, ftpAddressNew.c_str());
        setFtpAddress(ftpAddressNewChars);
//        delay(10);
        sendMessage("Done command " + currentLine);
      }
      else {
        Serial.print("I dont know command ");
        Serial.println(currentLine);
      }
      currentLine = "";
    } else {
      delay(100);
    }
  } 
}

String getStatus(){
  if (do_measurements) {
    return "Measuring";
  } else {
    return "Idle";
  }
}


void sendMessage(String msg){
  Serial.print("Sending msg \"");
  Serial.print(msg);
  Serial.print(" to ");
  Serial.print(udpAddress);
  Serial.println("\"");
  
  udp.beginPacket(udpAddress, udpPortOut);
  for (int i = 0; i < msg.length(); i++) {
    udp.write(msg[i]);
  }
  udp.endPacket();
}

void measurementsStart() {
  Serial.println("STARTING MEASUREMENTS");
  digitalWrite(LED_BUILTIN, HIGH);
  start_time = dateTime("Y-m-d-H-i-s");
  Serial.print("Start time:");
  Serial.println(start_time);

//  String filename = "Arduino_0_" + start_time + ".csv";
  String filename = String("arduino_") + (char)(ArduinoTypeID+48) + "_playerID_" + (char)(playerID+48) + "_" + start_time + ".csv";
//  String filename = "Arduino_" + char(ArduinoTypeID + 48) + (String)"_" + start_time + ".csv";
//  String x = sprintf(out_string, "%d", base_string);
  
  myFile = SD.open(filename, O_CREAT | O_TRUNC | O_WRITE);
  if(myFile){
        Serial.print("Writing to ");
        Serial.println(filename);
  } else {
    // if the file didn't open, print an error:
    Serial.println("Error opening the file");
  }

  for(int i=0; i < columns.size(); i++){
    myFile.print(columns[i]);
    if (i < columns.size() - 1) myFile.print(DELIMITER);
  }
  
  myFile.print('\n');
  do_measurements = true;
}

void measurementsEnd() {
  Serial.println("ENDING MEASUREMENTS");
  do_measurements = false;
  digitalWrite(LED_BUILTIN, LOW);
  delay(50);  // In order to write remaining data
  myFile.close();
}

std::vector<String> getFilesInInterval(String date_start, String date_end) {
  std::vector<String> filesVector;
  int datePartStart, datePartEnd;
  
  File root = SD.open("/");
  while (true) {
    File entry = root.openNextFile();
    if (! entry) { // no more files
      break;
    }
    char nameBuffer[100];
    
    entry.getName(nameBuffer, 100);
    String nameBufferString = (String) nameBuffer;

    if ((nameBufferString[0] == '.') || (nameBufferString.length() < TIME_FORMAT4FILES_LEN)) {
      continue;
    }
    
    datePartEnd = nameBufferString.length() - 4;
    datePartStart = datePartEnd - TIME_FORMAT4FILES_LEN;
    String datePart = nameBufferString.substring(datePartStart, datePartEnd);

    if ((date_start < datePart) && (datePart < date_end)) {
      Serial.println("BINGO!!! SUITABLE DATETIME:");
      Serial.println(datePart);
      filesVector.push_back(nameBufferString);
    }    
    entry.close();
  }
  
  root.close();
  
  return filesVector;
}

void timeSynchronization() {
  bool sync_success = 0;
  while (!sync_success){
    sync_success = waitForSync();
    if (!sync_success) {
      Serial.println("Cant sync time, trying again...");
      delay(5000);
    } else {
      Serial.println("Time has been syncronized");
    } 
  }
}

void timezoneSet() {
  bool sync_success = 0;
  while (!sync_success){
    sync_success = timezone.setLocation(F("DE"));
    if (!sync_success) {
      Serial.println("Cant sync timezone, trying again...");
      Serial.println(sync_success);
      delay(5000);
    } else {
      Serial.println("Timezone has been set");
    }
  }
  
  timezone.setDefault();
}


//char* string2Chars(String string2convert, char* chars) {
////  char chars[string2convert.length() + 1];
////  Serial.println("before strcpy");
//  strcpy(chars, string2convert.c_str());
////  Serial.println("after strcpy");
////  return chars;
//}


void sendFileFTP(String filename) {
  myFile = SD.open(filename, FILE_READ);

  char filenameChars[filename.length() + 1];
//  filename.copy(filenameChars, filename.length() + 1);
  strcpy(filenameChars, filename.c_str());
//  filenameChars[filename.length()] = '\0';

  ESP32_FTPClient ftp (ftpAddress,ftp_user,ftp_pass, 5000, 2);
  ftp.OpenConnection();
  ftp.ChangeWorkDir("my_new_dir");
  ftp.InitFile("Type I");
  ftp.NewFile(filenameChars);
  const int bufferSize = 1000;
  unsigned char mybytes[bufferSize];
  Serial.println("TRYING TO WRITE TO FTP FILE");
  for (int n_part = 0; n_part < myFile.size() / bufferSize; n_part++) {
    myFile.read(mybytes, bufferSize);
    ftp.WriteData(mybytes, bufferSize);
  }
  int n_remaining_bytes = myFile.size() % bufferSize;
  myFile.read(mybytes, n_remaining_bytes);
  ftp.WriteData(mybytes, n_remaining_bytes);
  ftp.CloseFile();
  myFile.close();

  ftp.CloseConnection();
}

void setUdpAddress(char* udpAddressNew) {
  Serial.print("Setting the new udpAddress to ");
  Serial.println(udpAddressNew);
  memset(udpAddress, '\0', sizeof(udpAddress));
  strcpy(udpAddress, udpAddressNew);
//  udpAddress = udpAddressNew;
}


void setFtpAddress(char* ftpAddressNew) {
  Serial.print("Setting the new ftpAddress to ");
  Serial.println(ftpAddressNew);
  memset(ftpAddress, '\0', sizeof(ftpAddress));
  strcpy(ftpAddress, ftpAddressNew);
//  udpAddress = udpAddressNew;
}

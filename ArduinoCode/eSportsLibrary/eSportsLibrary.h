#ifndef TEST_LIBRARY_H
#define TEST_LIBRARY_H

#define SEALEVELPRESSURE_HPA (1014) //Sea level Kaiserslautern on August 20th
#define SD_CS_PIN 33 //File: "pins_arduino.h" Slave Select
#define SDSPEED SD_SCK_MHZ(20) //SPI by default works in 50MHz, but since I am working with ESP32, it is recommended to test other frequencies

#include "Arduino.h"
#include <ezTime.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <SPI.h>
#include "SdFat.h"
#include <stdlib.h>
#include <ESP32_FTPClient.h>



extern String TIME_FORMAT, TIME_FORMAT4FILES;
extern const int TIME_FORMAT4FILES_LEN; //  = 19;
extern const char *ssid, *password;
extern const int udpPortIn;
extern char udpAddress[20], ftpAddress[20], ftp_pass[20], ftp_user[20];
extern const int IDLE_DELAY;

extern const char DELIMITER;
extern const int N_DIGITS_PRECISION;
extern bool do_measurements;
extern String current_time;

extern SdFat SD;
extern File myFile;
extern WiFiUDP udp;
extern Timezone timezone;
extern QueueHandle_t queue;

extern String start_time;

extern const int ArduinoTypeID;
extern const int playerID;
extern const int udpPortOut;
extern std::vector<String> columns;
extern TaskHandle_t WritingData, ReadingData, GettingCommands, UploadViaFTP;
extern void Task_ReadingData(void *pvParameters);
extern void Task_WritingData(void *pvParameters);
extern const int QUEUE_SIZE;


void hello();
void setFtpAddress(char* ftpAddressNew);
void setUdpAddress(char* udpAddressNew);
void sendFileFTP(String filename);
void timezoneSet();
void timeSynchronization();
void measurementsEnd();
std::vector<String> getFilesInInterval(String date_start, String date_end);
void measurementsStart();
void sendMessage(String msg);
String getStatus();
void Task_GettingCommands(void *pvParameters);
void loop();
void serialInit();
void wifiInit();
void udpInit();
void timeInit();
void sdInit();
void initQueue();
void generalInit();

#endif //TEST_LIBRARY_H

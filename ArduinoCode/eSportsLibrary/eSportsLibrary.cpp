#include "eSportsLibrary.h"
#include <cstring>
#include <queue>

String TIME_FORMAT = "Y-m-d-H:i:s.v"; // or '%Y-%m-%d-%H:%M:%S.%f' in python
String TIME_FORMAT4FILES = "Y-m-d-H-i-s";
const int TIME_FORMAT4FILES_LEN = 19;

//const char* ssid     = "OnePlusAnton";
//const char* password = "79998039003";
//const char* ssid     = "DFKI-PSK";
//const char* password = "50FSCN=j";
//const char* ssid     = "eSportsResearch";
//const char* password = "researchesports";
const char* ssid     = "DFKI-GLAS";
const char* password = "GG-FB-EI-p!";

const int udpPortIn = 3000;
const int udpPortOut = 10000 + ArduinoTypeID * 10 + playerID;

char udpAddress[20] = "192.168.31.210"; // your pc ip
char ftpAddress[20] = "192.168.31.210";
char ftp_pass[20]   = "thepassword";
char ftp_user[20]   = "player_X_arduino_X";


const char DELIMITER = ',';
const int N_DIGITS_PRECISION = 4;
bool do_measurements = false, ftp_sending = false, file_error = false, bad_data = false;
const int IDLE_DELAY = 100;


//Timezone timezone;
//String current_time;
//QueueHandle_t queue;

SdFat SD;
File myFile, FTPFile;
WiFiUDP udp;
Timezone timezone;
QueueHandle_t queue;
String start_time;

TaskHandle_t WritingData, ReadingData, GettingCommands, UploadViaFTP;

const int ftpBufferSize = 5000;
//const int FTP_QUEUE_SIZE = 100, MAX_FILENAME_LENGTH = 50;

//char dataArrayFtp[FTP_QUEUE_SIZE][MAX_FILENAME_LENGTH];
//char **P_send_filename_ftp = dataArrayFtp;
//char **P_receive_filename_ftp;

std::queue<String> queue_ftp;

void setUdpAddress(char* udpAddressNew) {
    Serial.print("Setting the new udpAddress to ");
    Serial.println(udpAddressNew);
    memset(udpAddress, '\0', sizeof(udpAddress));
    strcpy(udpAddress, udpAddressNew);
}


void setFtpAddress(char* ftpAddressNew) {
    Serial.print("Setting the new ftpAddress to ");
    Serial.println(ftpAddressNew);
    memset(ftpAddress, '\0', sizeof(ftpAddress));
    strcpy(ftpAddress, ftpAddressNew);
}

void sendFileFTP(String filename) {
    FTPFile = SD.open(filename, FILE_READ);
    
    char filenameChars[filename.length() + 1];
    //  filename.copy(filenameChars, filename.length() + 1);
    strcpy(filenameChars, filename.c_str());
    //  filenameChars[filename.length()] = '\0';
    
    ESP32_FTPClient ftp (ftpAddress,ftp_user,ftp_pass, 5000, 2);
    ftp.OpenConnection();
    String prefix = "player_" + String(playerID) + "/" + "arduino_" + String(ArduinoTypeID) + "_data";
    char prefixChars[prefix.length() + 1];
    strcpy(prefixChars, prefix.c_str());
    ftp.ChangeWorkDir(prefixChars);
    //    ftp.ChangeWorkDir("my_new_dir");
    ftp.InitFile("Type I");
    ftp.NewFile(filenameChars);
    
    unsigned char mybytes[ftpBufferSize];
    Serial.println("TRYING TO WRITE TO FTP FILE");
    for (int n_part = 0; n_part < FTPFile.size() / ftpBufferSize; n_part++) {
        FTPFile.read(mybytes, ftpBufferSize);
        ftp.WriteData(mybytes, ftpBufferSize);
    }
    int n_remaining_bytes = FTPFile.size() % ftpBufferSize;
    FTPFile.read(mybytes, n_remaining_bytes);
    ftp.WriteData(mybytes, n_remaining_bytes);
    ftp.CloseFile();
    FTPFile.close();
    
    ftp.CloseConnection();
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
//            Serial.println("File " + nameBufferString + " obviously doesnt suit for ftp upload");
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
//        else {
//            Serial.println("Entry " + nameBufferString + " doesnt suit for ftp upload because of date");
//            Serial.println("Date should be from " + date_start + " to " + date_end + "but here we have " + datePart);
//        }
        
        
        entry.close();
    }
    
    root.close();
    
    return filesVector;
}

void measurementsStart() {
    if (do_measurements) {
        Serial.println("Already measuring, cant start twice");
        return;
    }
    
    Serial.println("STARTING MEASUREMENTS");
    digitalWrite(LED_BUILTIN, HIGH);
    start_time = dateTime(TIME_FORMAT4FILES);
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
        file_error = false;
    } else {  // if the file is not opened, print an error
        Serial.println("Error opening the file"); // YOU HAVE TO NOTIFY ABOUT IT (SET STATUS FILE_ERROR)
        file_error = true;
    }
    
    for(int i=0; i < columns.size(); i++){
        myFile.print(columns[i]);
        if (i < columns.size() - 1) myFile.print(DELIMITER);
    }
    
    myFile.print('\n');
    do_measurements = true;
}

void measurementsEnd() {
    if (!do_measurements) {
        Serial.println("I am not measuring, so cant stop measurements");
        return;
    }
    Serial.println("ENDING MEASUREMENTS");
    do_measurements = false;
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);  // In order to write remaining data
    myFile.flush();
    myFile.close();
}

void sendMessage(String msg){
//    Serial.print("Sending msg \"");
//    Serial.print(msg);
//    Serial.print(" to ");
//    Serial.print(udpAddress);
//    Serial.println("\"");
    
    udp.beginPacket(udpAddress, udpPortOut);
    for (int i = 0; i < msg.length(); i++) {
        udp.write(msg[i]);
    }
    udp.endPacket();
}

String getStatus(){
    String status = "";
    
    if (file_error) {
        status += "File error";
    } else {
        if (do_measurements) {
            status += "Measuring";
            if (bad_data) {
                status += ",Bad_data";
            }
        } else {
            status += "Idle";
        }
    }
    
    if (ftp_sending) {
        status += ",FTP_sending";
    }
    
    
    return status;
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
        
        while (udp.available()) {
            x = (char) udp.read();
            if (x == ';') {  // Commands separator
//                Serial.println("Ignoring ; for " + currentLine);
                break;
            } else {
                currentLine += x;
            }
            
            //      Serial.print(x);
        }
        
        if (currentLine != "") {
            if (currentLine != "status") {
                Serial.print("Got command: ");
                Serial.println(currentLine);
            }
                
            //      Serial.println("Sending back...");
            
            if (currentLine == "start") {
                if (ftp_sending) {
                    currentLine = "";
                    Serial.println("I will not start measurements for safety reasons and because the data is uploaded via FTP");
                    continue; // Already sending something via FTP
                }
                
                measurementsStart();
                sendMessage("Starting measurements...");
            } else if (currentLine == "end") {
                measurementsEnd();
                sendMessage("Ending measurements...");
            } else if (currentLine == "status") {
                String current_status = getStatus();
//                Serial.println(current_status);
                sendMessage("status: " + current_status);
                currentLine = "";
            } else if (currentLine.startsWith("upload")) {
                if (ftp_sending || do_measurements) {
                    currentLine = "";
                    continue; // Already sending something via FTP
                }
                
                String date4files_start = currentLine.substring(7, 7 + TIME_FORMAT4FILES_LEN);
                String date4files_end = currentLine.substring(7 + TIME_FORMAT4FILES_LEN + 1, 7 + TIME_FORMAT4FILES_LEN + 1 + TIME_FORMAT4FILES_LEN);
                Serial.println("Uploading files in the interval from " + date4files_start + " to " + date4files_end);
                auto filesInInterval = getFilesInInterval(date4files_start, date4files_end);
                for (auto filename: filesInInterval) {
                    queue_ftp.push(filename);
//                    sendFileFTP(filename);
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
            delay(IDLE_DELAY);
        }
    }
}

void loop() {}


void serialInit(){
    Serial.begin(115200);
    //    delay(1000);  // Why?
//    while (!Serial) {
//        ; // wait for serial port to connect. Needed for native USB port only
//    }
}





void wifiInit(){
    // If you need a static IP
    //  if (!WiFi.config(local_IP, gateway, subnet)) {
    //      Serial.println("STA Failed to configure");
    //  }
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
}

void udpInit(){
    udp.begin(udpPortIn);
    Serial.print("udpPortOut = ");
    Serial.println(udpPortOut);
}


void timeInit(){
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
}



void sdInit(){
    Serial.println();
    Serial.print("Initializing SD card..");
    
    if(!SD.begin(SD_CS_PIN, SDSPEED)){
        Serial.println();
        Serial.println("Initialization failed!");
        while(1);
    }
    
    Serial.println();
    Serial.println("Initialization done.");
}

void Task_UploadViaFTP(void *pvParameters){
    while (true){
        if (!queue_ftp.empty()) {
            ftp_sending = true;
            String filename = queue_ftp.front();
            queue_ftp.pop();
            sendFileFTP(filename);
        } else {
            ftp_sending = false;
            delay(IDLE_DELAY);
        }
    }
}


void initQueue(){
    queue = xQueueCreate(QUEUE_SIZE, sizeof(struct sensor *) );
//    queue_ftp = xQueueCreate(QUEUE_SIZE, 50);
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
                            0);
    
    xTaskCreatePinnedToCore(
                            Task_UploadViaFTP,
                            "UploadViaFTP",
                            10000,
                            NULL,
                            2,
                            &UploadViaFTP,
                            0);
}

void ftpInit(){
    ftp_user[7] = (char)(playerID+48);
    ftp_user[17] = (char)(ArduinoTypeID+48);
}



void generalInit(){
    serialInit();
    wifiInit();
    udpInit();
    ftpInit();
    pinMode(LED_BUILTIN, OUTPUT);
    timeInit();
    sdInit();
    initQueue();
}




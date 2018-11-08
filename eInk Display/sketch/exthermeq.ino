#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <epd2in7b.h>
#include <epdif.h>
#include <epdpaint.h>
#include <fonts.h>
#include <SPI.h>
#include <epd2in7b.h>
#include <epdpaint.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <strings.h>
#include <avr/pgmspace.h>
#include "FS.h"

#define DEBUG_PRG                                   // use if need debug via serial
#define COLORED     1                               // value for eInk
#define UNCOLORED   0                               // value for eInk
#define MAX_VAL 32                                  // max array size for valves and openwindows
#define SSID_NAME "Your_SSID"                       // SSID name
#define SSID_PWD "Your_key" 		            // SSID pwd
#define MAX_VALVE_CHARS 8                           // max length of valve name displayed
#define STR_IDLE "idle"                             // idle heating string
#define STR_OK " OK "                               // string for "no open window"
#define STR_WIFI_ERROR "WiFi connect failed"        // error string displayed on ePaper if no wifi connected
#define DEEP_SLEEP_INTERVAL 60                      // how many seconds will be esp in deep sleep

// images start
const unsigned char gImage_heatingIcon[512] = { /* 0X01,0X01,0X40,0X00,0X40,0X00, */
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X07,0XFF,0X80,0X00,0X00,0X00,0X00,0X00,0X3F,0XFF,0XE0,0X00,
0X00,0X00,0X00,0X01,0XFF,0XFF,0XF8,0X00,0X00,0X00,0X00,0X0F,0XFF,0XFF,0XFE,0X00,
0X00,0X00,0X00,0X3F,0XFF,0XFF,0XFF,0X00,0X00,0X00,0X00,0X1F,0XFF,0XFF,0XFF,0X80,
0X00,0X00,0X00,0X0F,0XFF,0XFF,0XFF,0XC0,0X00,0X00,0X00,0X03,0XFF,0XFF,0XFF,0XE0,
0X00,0X00,0X00,0X00,0X3F,0XFF,0XFF,0XE0,0X00,0X00,0X00,0X00,0X0F,0XFF,0XFF,0XF0,
0X00,0X00,0X00,0X00,0X0F,0XFF,0XFF,0XF8,0X00,0X00,0X01,0XE0,0X07,0XFF,0XFF,0XF8,
0X00,0X00,0X07,0XFE,0X0F,0XFF,0XFF,0XFC,0X00,0X00,0X0F,0XFF,0X9F,0XFF,0XDF,0XFC,
0X00,0X00,0X1F,0XFF,0XFF,0XFC,0X03,0XFC,0X00,0X00,0X3F,0XFF,0XFF,0XF8,0X01,0XFC,
0X00,0X00,0XFF,0XFF,0XFF,0XFE,0X00,0XFE,0X00,0X01,0XFF,0XFF,0XFF,0XFF,0X00,0X7E,
0X00,0X07,0XFF,0XFF,0XFF,0XC0,0X00,0X7E,0X00,0X1F,0XFF,0XFF,0XFF,0X80,0X00,0X7E,
0X00,0XFF,0XFF,0XFF,0XFE,0X00,0X00,0X7E,0X3F,0XFF,0XFF,0XFF,0XF0,0X00,0X00,0X7E,
0X1F,0XFF,0XFF,0XFF,0XF8,0X00,0X00,0X7E,0X0F,0XFF,0XFF,0XFF,0XFC,0X00,0X00,0X7E,
0X07,0XFF,0XFF,0XFF,0XFF,0XF8,0X00,0XFE,0X03,0XFF,0XFF,0XFF,0XFF,0XE0,0X00,0XFC,
0X01,0XFF,0XFF,0XFF,0XFF,0XF8,0X01,0XFC,0X00,0XFF,0XFF,0XFF,0XFF,0XFE,0X07,0XFC,
0X00,0X3F,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,0X00,0X0F,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,
0X00,0X00,0X00,0X0F,0XFF,0XFF,0XFF,0XF8,0X00,0X00,0X00,0X07,0XFF,0XFF,0XFF,0XF0,
0X00,0X00,0X00,0XFF,0XFF,0XFF,0XFF,0XE0,0X00,0X00,0X03,0XFF,0XFF,0XFF,0XFF,0XC0,
0X00,0X00,0X07,0XFF,0XFF,0XFF,0XFF,0X80,0X00,0X00,0X00,0X3F,0XFF,0XFF,0XFF,0X00,
0X00,0X00,0X00,0X0F,0XFF,0XFF,0XFE,0X00,0X00,0X00,0X00,0X03,0XFF,0XFF,0XFC,0X00,
0X00,0X00,0X00,0X00,0X7F,0XFF,0XF0,0X00,0X00,0X00,0X00,0X00,0X0F,0XFF,0XC0,0X00,
0X00,0X00,0X00,0X00,0X00,0X38,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
};

const unsigned char gImage_openWindow[512] = { /* 0X01,0X01,0X40,0X00,0X40,0X00, */
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X0F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF0,
0X1F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,0X1F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,
0X0F,0X00,0X30,0X01,0X80,0X0C,0X00,0XF0,0X0F,0X00,0X30,0X01,0X80,0X0C,0X00,0XF0,
0X07,0X00,0X18,0X01,0X80,0X1C,0X00,0XE0,0X07,0X80,0X18,0X01,0X80,0X18,0X01,0XE0,
0X03,0X80,0X19,0X8D,0XB0,0XD8,0X01,0XC0,0X03,0XC0,0X19,0X8D,0XB0,0X98,0X03,0XC0,
0X01,0XC0,0X1B,0X0D,0XA1,0XB0,0X03,0X80,0X01,0XE0,0X0F,0X19,0XE1,0XB0,0X07,0X80,
0X00,0XE0,0X0C,0X01,0X80,0X30,0X07,0X00,0X00,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0X00,
0X00,0X7F,0XFF,0XFF,0XFF,0XFF,0XFE,0X00,0X00,0X7F,0XFF,0XFF,0XFF,0XFF,0XFE,0X00,
0X00,0X78,0X00,0X00,0X00,0X00,0X1E,0X00,0X00,0X70,0X0C,0X21,0X86,0X00,0X0E,0X00,
0X00,0X70,0X0C,0X61,0X86,0X00,0X0E,0X00,0X00,0X70,0X0C,0X61,0X86,0X00,0X0E,0X00,
0X00,0X70,0X0C,0X61,0X86,0X00,0X0E,0X00,0X00,0X70,0X0C,0X61,0X86,0X00,0X0E,0X00,
0X00,0X70,0X0C,0X61,0X86,0X00,0X0E,0X00,0X00,0X70,0X0C,0X31,0X86,0X00,0X0E,0X00,
0X00,0X70,0X0C,0X30,0XC6,0X00,0X0E,0X00,0X00,0X70,0X06,0X30,0XC3,0X00,0X0E,0X00,
0X00,0X70,0X06,0X38,0XC3,0X00,0X0E,0X00,0X00,0X70,0X07,0X18,0X63,0X80,0X0E,0X00,
0X00,0X70,0X03,0X1C,0X61,0X80,0X0E,0X00,0X00,0X70,0X03,0X8C,0X31,0XC0,0X0E,0X00,
0X00,0X70,0X01,0X8E,0X30,0XC0,0X0E,0X00,0X00,0X70,0X01,0XC6,0X18,0XE0,0X0E,0X00,
0X00,0X70,0X00,0XC7,0X18,0X60,0X0E,0X00,0X00,0X70,0X00,0XE3,0X0C,0X60,0X0E,0X00,
0X00,0X70,0X00,0X63,0X0C,0X30,0X0E,0X00,0X00,0X70,0X00,0X61,0X8C,0X30,0X0E,0X00,
0X00,0X70,0X00,0X71,0X86,0X30,0X0E,0X00,0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,
0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,
0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,
0X00,0X70,0X00,0X31,0X86,0X18,0X0E,0X00,0X00,0X78,0X00,0X31,0X86,0X38,0X1E,0X00,
0X00,0X7F,0XFF,0XFF,0XFF,0XF7,0XFE,0X00,0X00,0X7F,0XFF,0XFF,0XFF,0XFF,0XFE,0X00,
0X00,0XFF,0XFF,0XEF,0XFD,0XF7,0XFF,0X00,0X00,0XE0,0X0C,0XE3,0X8C,0X60,0X07,0X00,
0X01,0XE0,0X1C,0XC7,0X98,0X70,0X07,0X80,0X01,0XC0,0X18,0XC7,0X98,0X70,0X03,0X80,
0X03,0XC0,0X19,0X87,0XB8,0XF8,0X03,0XC0,0X03,0X80,0X19,0X8D,0XB0,0XD8,0X01,0XC0,
0X07,0X80,0X38,0X01,0X80,0X18,0X01,0XE0,0X07,0X00,0X30,0X01,0X80,0X18,0X00,0XE0,
0X0F,0X00,0X30,0X01,0X80,0X18,0X00,0XF0,0X0F,0X00,0X70,0X01,0X80,0X1C,0X00,0XF0,
0X1F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,0X1F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF8,
0X0F,0XFF,0XFF,0XFF,0XFF,0XFF,0XFF,0XF0,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00,
};
// images end

const char* ssid = SSID_NAME;
const char* password = SSID_PWD;

// initialize display
// WIDTH 176, HEIGHT 264
Epd epd;  
unsigned char image[2048];
Paint paint(image, 24, 264);

// thermeq3 variables
String t_valves = "";
String t_valve_switch = "";
String t_preference = "";
String t_mode = "";
String t_profile = "";
String t_status = "";
String i_status = "";

// max MAX_VAL rooms per EQ3 system
struct room_t {
  String nam;
  byte pos;
  float stmp;
  float ctmp;
} t_rooms[MAX_VAL]; 

// open windows 
String owl[MAX_VAL];
byte owl_len = 0;

void clearTopCanvas() {
  paint.SetWidth(88);
  paint.SetHeight(88);
  paint.Clear(UNCOLORED);  
  paint.DrawRectangle(1, 1, 87, 87, COLORED); 
}

void clearBottomCanvas() {
  paint.SetWidth(88);
  paint.SetHeight(132);
  paint.Clear(UNCOLORED);  
  paint.DrawRectangle(1, 1, 131, 87, COLORED);
}


char* toChar(String tmpStr) {
  boolean where = true;
  while (tmpStr.length() < 6) {
    if (where) {
      tmpStr = " " + tmpStr;
    } else {
      tmpStr = tmpStr + " ";
    }
    where = not where;
  }
  static char tmpChar[7];
  tmpStr.toCharArray(tmpChar, 7);
  return tmpChar;
}

void displayThermeqSetup() {
  char charBuf[16];
  clearTopCanvas();  
  paint.DrawStringAt(10,  8, toChar(String(t_valve_switch + "%/#" + t_valves)), &Font16, COLORED);
  paint.DrawStringAt(10, 26, toChar(t_preference), &Font16, COLORED);
  paint.DrawStringAt(10, 44, toChar(t_mode), &Font16, COLORED);
  paint.DrawStringAt(10, 60, toChar(t_profile), &Font16, COLORED);
  epd.TransmitPartialBlack(paint.GetImage(), 0, 88, paint.GetWidth(), paint.GetHeight());
}

char* getRoomString(byte idx){
  String tmpStr = t_rooms[idx].nam;
  char fbuff[5];
  byte tmpLen = tmpStr.length();
  static char tmpChar[24];
  
  if (tmpLen > MAX_VALVE_CHARS) {
    tmpStr = tmpStr.substring(0, MAX_VALVE_CHARS);
  } else {
    while (tmpStr.length() < MAX_VALVE_CHARS) {
      tmpStr += " ";
    }  
  }
  
  sprintf(fbuff, " %02d%% ", t_rooms[idx].pos);
  tmpStr += String(fbuff);
  dtostrf(t_rooms[idx].stmp, 2, 1, fbuff);
  tmpStr += String(fbuff); 
  tmpLen = tmpStr.length();
  tmpStr.toCharArray(tmpChar, tmpLen + 1);
  
  #ifdef DEBUG_PRG
  Serial.println(tmpStr);
  #endif
  
  return tmpChar;
}

void showValves() {
  #ifdef DEBUG_PRG
  Serial.println("showValves START");
  #endif
  clearBottomCanvas();
  // max 7 valves per screen
  // rotator to be implemented
  for (byte i=0; i<7; i++) {
    if (t_rooms[i].nam != "") paint.DrawStringAt(4,   4 + (i * 12), getRoomString(i), &Font12, COLORED);
  }
  epd.TransmitPartialBlack(paint.GetImage(), 89, 132, paint.GetWidth(), paint.GetHeight());
  #ifdef DEBUG_PRG
  Serial.println("showValves STOP");
  #endif

}

char* getWinString(byte idx) {
  static char tmpChar[24];
  String tmpStr = owl[idx];
  byte tmpLen = tmpStr.length() + 1;
  tmpStr.toCharArray(tmpChar, tmpLen);
  #ifdef DEBUG_PRG
  Serial.println(tmpChar);
  #endif
  return tmpChar;
}

void showWindows() {
  #ifdef DEBUG_PRG
  Serial.println("showWindows START");
  #endif
  clearBottomCanvas();
  for (byte i=0; i<4; i++) {
    if (owl[i] != "") {
      paint.DrawStringAt(4,   4 + (i * 20), getWinString(i), &Font20, COLORED);
    }
  }
  epd.TransmitPartialRed(paint.GetImage(), 89, 0, paint.GetWidth(), paint.GetHeight());
  #ifdef DEBUG_PRG
  Serial.println("showWindows STOP");
  #endif
}

void getData() {
  HTTPClient http;
  String payload;
  DynamicJsonDocument tjson;
  DynamicJsonDocument sys;
  DynamicJsonDocument tmp;
  JsonArray arr;
  JsonObject root;
  
  #ifdef DEBUG_PRG
  Serial.println("getData START");
  #endif
  http.begin("http://10.60.0.11:8180/bridge.json"); 

  int httpCode = http.GET();

  if (httpCode > 0) {
    #ifdef DEBUG_PRG
    Serial.printf("[HTTP] GET... return code: %d\n", httpCode);
    #endif
    // file found at server
    if (httpCode == HTTP_CODE_OK) {
      payload = http.getString();
      #ifdef DEBUG_PRG
      // Serial.println(payload);
      #endif
    }
  } else {
    #ifdef DEBUG_PRG
    Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
    #endif
  }
  http.end();
  
  DeserializationError error = deserializeJson(tjson, payload);
  if (error) {
    #ifdef DEBUG_PRG
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    #endif
    return;
  }

  root = tjson.as<JsonObject>();
  t_valves = root["valves"].as<String>();
  t_valve_switch = root["valve_switch"].as<String>();
  t_preference = root["preference"].as<String>();
  t_mode = root["mode"].as<String>();
  t_profile = root["profile"].as<String>();
  t_status = root["status_key"].as<String>();

  // unpack system status
  error = deserializeJson(sys, root["system_status"].as<String>());
  if (error) {
    #ifdef DEBUG_PRG
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    #endif
    return;
  }
  JsonObject v_root = sys.as<JsonObject>();
  
  // unpack rooms
  byte i = 0;
  JsonObject tmpRoot;
  for (JsonObject::iterator it=v_root.begin(); it!=v_root.end(); ++it) {
    t_rooms[i].nam = it->key().c_str();
    
    error = deserializeJson(tmp, v_root[it->key().c_str()].as<String>());
    tmpRoot = tmp.as<JsonObject>();
    // unpack room valves
    byte j = 0;
    word valve_pos = 0;
    float temp = 0.0;
    float curr_temp = 0.0;
    for (JsonObject::iterator it=tmpRoot.begin(); it!=tmpRoot.end(); ++it) {
      arr = it->value().as<JsonArray>();
      
      valve_pos += arr.get<byte>(1);  
      temp += arr.get<float>(2);
      curr_temp += arr.get<float>(3);
      j++;
    }
    t_rooms[i].pos = byte(valve_pos / j);
    t_rooms[i].stmp = float(temp / j);
    t_rooms[i].ctmp = float(curr_temp / j);
    i++;
  }
  
  // unpack open window list
  error = deserializeJson(tmp, root["open_window_list"].as<String>());
  if (error) {
    #ifdef DEBUG_PRG
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    #endif
    return;
  }
  tmpRoot = tmp.as<JsonObject>();
  i = 0;
  for (JsonObject::iterator it=tmpRoot.begin(); it!=tmpRoot.end(); ++it) {
     arr = it->value().as<JsonArray>();
     owl[i] = arr.get<String>(1); 
     i++;
  }
  owl_len = i;
  #ifdef DEBUG_PRG
  Serial.println("getData STOP");
  #endif
}

void displayHeating() {
  byte h = 0;
  byte v = 0;
  #ifdef DEBUG_PRG
  Serial.println("displayHeating START");
  #endif
  if (i_status != t_status) {
    if (t_status.charAt(0) == 'h') {
      h = 1;
    }
    if (t_status.charAt(1) == 'v' || owl_len > 0) {
      v = 1;
    }
    #ifdef DEBUG_PRG
    Serial.print("h=");
    Serial.println(h);
    Serial.print("v=");
    Serial.println(v);
    #endif
    clearTopCanvas();
    if (h == 1) {
      if (v == 0) {
        epd.TransmitPartialRed(gImage_heatingIcon, 11, 189, 64, 64);  
      } else {
        epd.TransmitPartialBlack(gImage_heatingIcon, 11, 189, 64, 64);  
      }
    } else {
        paint.DrawStringAt(8,  32, STR_IDLE, &Font24, COLORED);     
    }
    epd.TransmitPartialBlack(paint.GetImage(), 0, 176, paint.GetWidth(), paint.GetHeight());
    
    // windows
    clearTopCanvas();  
    if (v == 1) {
      epd.TransmitPartialRed(gImage_openWindow, 12, 12, 64, 64);
    } else {
      paint.DrawStringAt(8,  32, STR_OK, &Font24, COLORED);
    }
    i_status = t_status;
  }
  epd.TransmitPartialBlack(paint.GetImage(), 0, 0, paint.GetWidth(), paint.GetHeight());
  #ifdef DEBUG_PRG
  Serial.println("displayHeating STOP");
  #endif
}

boolean connect() {
  // WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  #ifdef DEBUG_PRG
  Serial.println("thermeq3 eDisplay");
  Serial.println("-----------------");
  Serial.print("Connected to ");
  Serial.println(ssid);
  #endif
  
  // Wait for connection
  // max 15 sec
  byte i = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    if (i > 15) {
      break;
    }
    #ifdef DEBUG_PRG
    Serial.print(".");
    #endif
  }

  if (i > 15) return false;
  else {
     #ifdef DEBUG_PRG
    Serial.print("\r\nIP address: ");
    Serial.println(WiFi.localIP());
    #endif
    return true;
  }
}

bool saveConfig() {
  File configFile = SPIFFS.open("/status.cfg", "w");
  if (!configFile) {
    #ifdef DEBUG_PRG
    Serial.println("Failed to open config file for writing");
    #endif
    return false;
  }
  configFile.println(i_status);
  configFile.close();
  return true;
}

bool loadConfig() {
    // open file for reading
  #ifdef DEBUG_PRG
  Serial.println("loadConfig START");
  #endif
  File configFile = SPIFFS.open("/status.cfg", "r");
  if (!configFile) {
    #ifdef DEBUG_PRG
    Serial.println("file open failed");
    #endif
  }
  String tmpStr = configFile.readStringUntil('\n');
  i_status = tmpStr;
  configFile.close();
  #ifdef DEBUG_PRG
  Serial.println(tmpStr);
  #endif
  #ifdef DEBUG_PRG
  Serial.println("loadConfig STOP");
  #endif
}

void setup() {
  // initialize serial port
  #ifdef DEBUG_PRG
  Serial.begin(115200);
  while (!Serial);
  #endif

  // if ePaper is not present, quit
    if (epd.Init() != 0) {
    #ifdef DEBUG_PRG
    Serial.print("e-Paper init failed");
    #endif
    return;
  }

  if (!SPIFFS.begin()) {
    #ifdef DEBUG_PRG
    Serial.println("Failed to mount file system");
    #endif
    return;
  }

  loadConfig();
  // clear display
  epd.ClearFrame();
  // rotate to landscape
  paint.SetRotate(ROTATE_270);

  // if connected, get data, display
  if (connect()) {
    getData();
  
    // display data
    displayHeating();
    displayThermeqSetup();
    showValves();
    showWindows();  
    saveConfig();
  } else {
    paint.DrawStringAt(0, 0, STR_WIFI_ERROR, &Font24, COLORED);  
    epd.TransmitPartialRed(paint.GetImage(), 8, 16, paint.GetWidth(), paint.GetHeight());
  }

  epd.DisplayFrame();
  // deep sleep for epaper
  epd.Sleep();
 
  ESP.deepSleep(DEEP_SLEEP_INTERVAL * 1000000);
}

void loop() {
    
}

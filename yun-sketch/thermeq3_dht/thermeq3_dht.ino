// #define DEBUG_PRG

// define if temperature sensor is used
#define USE_TEMP_SENSOR
// define if reverse logic (or optocoupler relay) is used
#define RELAY_OPTOCOUPLER_MODE
#ifdef RELAY_OPTOCOUPLER_MODE
  #define LOGIC_1 LOW
  #define LOGIC_0 HIGH
#else
  #define LOGIC_1 HIGH
  #define LOGIC_0 LOW
#endif

#ifdef USE_TEMP_SENSOR
// Install DHTLib http://playground.arduino.cc//Main/DHTLib 
// Require DHT22 sensor
#include <dhtlib.h>

dht DHT;
// DHT sensor PIN
#define DHT_PIN 2
// DHT error led
#define TEMP_ERROR_LED 3
// Min DHT22 sampling frequency is 0.5Hz!
#define DHT_INTERVAL 5000
// Below these temperature anitfreezing feature is on! 
#define MIN_TEMP 5

unsigned long dhtReadUntil = 0;
#endif

#include <Process.h>

#define RELAY_PIN 10
#define RELAY_RESET_PIN 11
#define STATUS_LED 9
#define ERROR_LED 8
#define LOOP_LED 13
#define BLINK_INTERVAL 150
#define CUBE_RESET_TIME 10000
#define WAIT_UPDATE_SYNC 10000

#define IWANNABESAFE

Process p;
char bridgeBuffer[16];
boolean sysStatus = false;
boolean planned_heating = false;
boolean alarmHit = false;
unsigned long waitUntil = 0;
unsigned long interval = 10*1000;               // interval in seconds, change 10 to anything you want
unsigned long app_interval = 10*60000;          // interval in minutes, change 10 to anything you want
unsigned long waitForApp = 0;
unsigned long waitUntilCubeReset = 0;
boolean inCubeReset = false;

void alloff() {
  digitalWrite(LOOP_LED, LOW);
  digitalWrite(STATUS_LED, LOW);
  digitalWrite(ERROR_LED, LOW);  
}

void allon() {
  digitalWrite(LOOP_LED, HIGH);
  digitalWrite(STATUS_LED, HIGH);
  digitalWrite(ERROR_LED, HIGH);  
}

void blinkLED() {
  for (byte i = 0; i < 4; i++) {
    allon();
    delay(BLINK_INTERVAL);
    alloff();
    delay(BLINK_INTERVAL);
  }
}

void turnIt(boolean onoff) {
  showError(false);
  if (sysStatus == onoff) return;
  
  if (onoff) {
    digitalWrite(RELAY_PIN, LOGIC_1);
    digitalWrite(STATUS_LED, HIGH);
  } else {
    if (!alarmHit) {  
    digitalWrite(RELAY_PIN, LOGIC_0);
    digitalWrite(STATUS_LED, LOW);
    }
  }
  sysStatus = onoff;
  Bridge.put("msg", "");
}

void doResetCube (boolean onoff) {
  if (onoff) {
    inCubeReset = true;
    digitalWrite(RELAY_RESET_PIN, LOGIC_1);
  }
  else {
    digitalWrite(RELAY_RESET_PIN, LOGIC_0);
    inCubeReset = false;    
  }  
}

void fatalError() {
  turnIt(false);
  alloff();
  while (true) {
    digitalWrite(LOOP_LED, HIGH);
    delay(BLINK_INTERVAL);
    digitalWrite(LOOP_LED, LOW);
    digitalWrite(STATUS_LED, HIGH);
    delay(BLINK_INTERVAL);
    digitalWrite(STATUS_LED, LOW);
    digitalWrite(ERROR_LED, HIGH);
    delay(BLINK_INTERVAL);
    digitalWrite(ERROR_LED, LOW);
  }
}

void showDead() {
  turnIt(false);
  alloff();
  while (true) {
    for(int j = 0 ; j <= 255; j +=5) { 
      analogWrite(STATUS_LED, j);         
      delay(30);                            
    }   
    for(int j = 255 ; j >= 0; j -=10) { 
      analogWrite(STATUS_LED, j);         
      delay(30);                            
    }
    digitalWrite(STATUS_LED, LOW);
    delay(BLINK_INTERVAL * 5);
  }
}

void showError(boolean onoff) {
  if (onoff) digitalWrite(ERROR_LED, HIGH);
    else digitalWrite(ERROR_LED, LOW);
  Bridge.put("msg", "");
}

void showTempError(boolean onoff) {
  #ifdef USE_TEMP_SENSOR
  if (onoff) digitalWrite(TEMP_ERROR_LED, HIGH);
    else digitalWrite(TEMP_ERROR_LED, LOW);
  #endif
}

void runApp() {
  turnIt(false);
  // you can use p.begin("/root/nsm.py") without .addParameter
  p.begin("python"); 
  p.addParameter("/root/thermeq3/nsm.py"); 
  p.runAsynchronously();
}

void reset_cube() {
  waitUntilCubeReset = millis() + CUBE_RESET_TIME;
  doResetCube(true);  
}

void setup() {
  #ifdef DEBUG_PRG
  Serial.begin(9600);
  while (!Serial);
  #endif

  #ifdef USE_TEMP_SENSOR
  pinMode(TEMP_ERROR_LED, OUTPUT);
  #endif  
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOGIC_0);

  pinMode(RELAY_RESET_PIN, OUTPUT);
  digitalWrite(RELAY_RESET_PIN, LOGIC_0);
    
  pinMode(ERROR_LED, OUTPUT);
  pinMode(STATUS_LED, OUTPUT);
  pinMode(LOOP_LED, OUTPUT);
    
  blinkLED();
  allon();
  Bridge.begin();
  blinkLED();
   
  runApp();

  #ifdef DEBUG_PRG
  Serial.println("GO!");
  Serial.println(interval);
  Serial.println(app_interval);
  #endif
}

void loop() {  
unsigned long mls = millis();

  if (mls - waitUntil >= interval) {
    digitalWrite(LOOP_LED, HIGH);
    Bridge.get("msg", bridgeBuffer, 16);
    char c = bridgeBuffer[0];
    
    switch (c) {
      case 'H': 
        turnIt(true);
        planned_heating = true;
        break;
      case 'S': 
        turnIt(false);
        planned_heating = false;
        break;
      case 'E':
        #ifdef IWANNABESAFE
          turnIt(false);
          planned_heating = false;
        #endif
        showError(true);
        break;
      case 'A':
        alloff();
        break;
      case 'Q':
        fatalError();
        break;
      case 'D':
        turnIt(false);
        showDead();
        break;
      case 'R':
        #ifdef IWANNABESAFE
          turnIt(false);
        #endif
        digitalWrite(ERROR_LED, LOW);
        digitalWrite(STATUS_LED, LOW);
        digitalWrite(ERROR_LED, HIGH);
        digitalWrite(STATUS_LED, HIGH);
        p.close();
        delay(WAIT_UPDATE_SYNC);
        runApp();
        digitalWrite(ERROR_LED, LOW);
        digitalWrite(STATUS_LED, LOW);
        break;
      case 'r':
        reset_cube();
        break;
    }
    waitUntil = waitUntil + interval;
    digitalWrite(LOOP_LED, LOW);    
  }
  
  if (mls - waitForApp >= app_interval) {
    #ifdef DEBUG_PRG
    Serial.println(mls);
    Serial.println(p.running());
    #endif
    digitalWrite(LOOP_LED, HIGH);
    if (p.running() == false) {
      p.close();
      runApp();
    }
    waitForApp = waitForApp + app_interval;
    digitalWrite(LOOP_LED, LOW);    
  }

  if (inCubeReset) {
    if (mls - waitUntilCubeReset >= 0 ) {
      doResetCube(false);
    }        
  }

  #ifdef USE_TEMP_SENSOR  
  if (mls - dhtReadUntil >=0 ) {
    dhtReadUntil = dhtReadUntil + DHT_INTERVAL;
    int chk = DHT.read22(DHT_PIN);
    
    switch (chk)
    {
    case DHTLIB_OK:
    #ifdef DEBUG_PRG  
      Serial.print("OK,\t"); 
      Serial.println(DHT.temperature, 1);
    #endif
    showTempError(false);

    if (DHT.temperature <= MIN_TEMP ) {
      alarmHit = true;
      turnIt(true);
    }
    else {
      alarmHit = false;
      if (!planned_heating) {
        turnIt(false);
      }
    }    
    
    break;
    case DHTLIB_ERROR_CHECKSUM: 
      #ifdef DEBUG_PRG
      Serial.print("Checksum error,\t"); 
      #endif
      showTempError(true);
    break;
    case DHTLIB_ERROR_TIMEOUT: 
      #ifdef DEBUG_PRG    
      Serial.print("Time out error,\t"); 
      #endif
      showTempError(true);
      break;
    default: 
      #ifdef DEBUG_PRG    
      Serial.print("Unknown error,\t"); 
      #endif
      showTempError(true);    
    break;
    }
  }    
  #endif
  
  #ifdef DEBUG_PRG
  Serial.println(mls);
  Serial.println(p.running());
  #endif  
}

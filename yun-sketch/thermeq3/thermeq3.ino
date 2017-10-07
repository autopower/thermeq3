// #define DEBUG_PRG

#include <Process.h>

#define RELAY_PIN 10
// #define RELAY_POWER 8
#define STATUS_LED 9
#define ERROR_LED 8
#define LOOP_LED 13
#define BLINK_INTERVAL 150
#define WAIT_UPDATE_SYNC 10000

#define IWANNABESAFE

Process p;
char bridgeBuffer[16];
boolean sysStatus = false;
unsigned long waitUntil = 0;
unsigned long interval = 10*1000;              // interval in seconds, change 10 to anything you want
unsigned long app_interval = 5*60000;          // interval in minutes, change 5 to anything you want
unsigned long waitForApp = 0;

void blinkLED() {
  for (byte i = 0; i < 4; i++) {
    digitalWrite(LOOP_LED, HIGH);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(ERROR_LED, HIGH);
    delay(BLINK_INTERVAL);
    digitalWrite(LOOP_LED, LOW);
    digitalWrite(STATUS_LED, LOW);
    digitalWrite(ERROR_LED, LOW);
    delay(BLINK_INTERVAL);
  }
}

void turnIt(boolean onoff) {
  showError(false);
  if (sysStatus == onoff) return;
  
  if (onoff) {
    #ifdef RELAY_POWER
    digitalWrite(RELAY_POWER, HIGH);
    delay(500);
    #endif
    digitalWrite(RELAY_PIN, HIGH);
    digitalWrite(STATUS_LED, HIGH);
  } else {
    digitalWrite(RELAY_PIN, LOW);
    #ifdef RELAY_POWER
    delay(500);
    digitalWrite(RELAY_POWER, LOW);
    #endif
    digitalWrite(STATUS_LED, LOW);
  }
  sysStatus = onoff;
  Bridge.put("msg", "");
}

void fatalError() {
  turnIt(false);
  digitalWrite(LOOP_LED, LOW);
  digitalWrite(STATUS_LED, LOW);
  digitalWrite(ERROR_LED, LOW);
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
  digitalWrite(LOOP_LED, LOW);
  digitalWrite(STATUS_LED, LOW);
  digitalWrite(ERROR_LED, LOW);
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

void runApp() {
  turnIt(false);
  // start python app
  p.begin("python"); 
  p.addParameter("/root/nsm.py"); 
  p.runAsynchronously();
}

void signalReadNotOK() {
  turnIt(false);
  // turn on all LEDs, to show that linux part is started
  digitalWrite(LOOP_LED, HIGH);
  digitalWrite(STATUS_LED, HIGH);
  digitalWrite(ERROR_LED, HIGH);
}

void setup() {
  #ifdef DEBUG_PRG
  Serial.begin(9600);
  while (!Serial);
  #endif
  
  pinMode(RELAY_PIN, OUTPUT);
  #ifdef RELAY_POWER
  pinMode(RELAY_POWER, OUTPUT); 
  #endif
  pinMode(ERROR_LED, OUTPUT);
  pinMode(STATUS_LED, OUTPUT);
  pinMode(LOOP_LED, OUTPUT);
  
  blinkLED();
  digitalWrite(STATUS_LED, HIGH);
  digitalWrite(ERROR_LED, HIGH);
  digitalWrite(LOOP_LED, HIGH);
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
        break;
      case 'S': 
        turnIt(false);
        break;
      case 'E':
        // in case that cube is not available, e.g. timeout
        #ifdef IWANNABESAFE
          turnIt(false);
        #endif
        showError(true);
        break;
      case 'C':
        showError(false);
        break;
      case 'Q':
        fatalError();
        break;
      case 'D':
        turnIt(false);
        showDead();
        break;
      case 'M':
        // in case that read from max cube malformed
        signalReadNotOK();
        break; 
      case 'R':
        #ifdef IWANNABESAFE
          turnIt(false);
        #endif
        digitalWrite(ERROR_LED, HIGH);
        digitalWrite(STATUS_LED, HIGH);
        p.close();
        delay(WAIT_UPDATE_SYNC);
        runApp();
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

}

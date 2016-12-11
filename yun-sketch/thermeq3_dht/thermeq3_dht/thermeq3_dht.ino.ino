//#define DEBUG_PRG

#include <Process.h>

//DHT sesnor PIN
#define DHT_PIN A4

#define TEMP_ERROR_LED 11
#define RELAY_PIN 10
#define STATUS_LED 9
#define ERROR_LED 8
#define LOOP_LED 13
#define BLINK_INTERVAL 150
#define WAIT_UPDATE_SYNC 10000

//#define IWANNABESAFE

// define this if you wanna use some optocoupler for relay or reverse logic
#define REVERSE_LOGIC
#ifdef REVERSE_LOGIC
#define LOGIC_1 LOW
#define LOGIC_0 HIGH
#else
#define LOGIC_1 HIGH
#define LOGIC_0 LOW
#endif

//Install DHTLib http://playground.arduino.cc//Main/DHTLib
//Require DHT22 sensor
#include <dht.h>

dht DHT;

//Min DHT22 sampling frequency is 0.5Hz!
#define DHT_INTERVAL 5000
//Bellow these temperature anitfreezing feature is on!
#define MIN_TEMP 7

unsigned long dhtReadUntil = 0;

boolean temp_error = false;
boolean temp_anti_freeze_on = false;
boolean temp_led_on = false;
#define TEMP_ERROR_BLINK_PERIOD 500
unsigned long tempBlink = 0;


Process p;
char bridgeBuffer[16];
boolean sysStatus = false;
boolean planned_heating = false;
boolean alarmHit = false;
unsigned long waitUntil = 0;
unsigned long interval = 10 * 1000;             // interval in seconds, change 10 to anything you want
unsigned long app_interval = 10 * 60000;        // interval in minutes, change 10 to anything you want
unsigned long waitForApp = 0;

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

void turnIt_nomsg(boolean onoff) {
  if (sysStatus == onoff) return;
  if (onoff) {
    digitalWrite(RELAY_PIN, LOGIC_1);
    digitalWrite(STATUS_LED, HIGH);
  } else {
    if (!alarmHit)
    {
      digitalWrite(RELAY_PIN, LOGIC_0);
      digitalWrite(STATUS_LED, LOW);
    }
  }
  sysStatus = onoff;
}

void turnIt(boolean onoff) {
  showError(false);
  if (sysStatus == onoff) return;
  if (onoff) {
    digitalWrite(RELAY_PIN, LOGIC_1);
    digitalWrite(STATUS_LED, HIGH);
  } else {
    if (!alarmHit)
    {
      digitalWrite(RELAY_PIN, LOGIC_0);
      digitalWrite(STATUS_LED, LOW);
    }
  }
  sysStatus = onoff;
  Bridge.put("msg", "");
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
    for (int j = 0 ; j <= 255; j += 5) {
      analogWrite(STATUS_LED, j);
      delay(30);
    }
    for (int j = 255 ; j >= 0; j -= 10) {
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
  if (onoff) {
    digitalWrite(TEMP_ERROR_LED, HIGH);
    temp_led_on = true;
  }
  else {
    digitalWrite(TEMP_ERROR_LED, LOW);
    temp_led_on = false;
  }
}

void tempError(boolean onoff)
{
  temp_error = onoff;
}

void runApp() {
  turnIt(false);
  // you can use p.begin("/root/nsm.py") without .addParameter
  p.begin("python");
  p.addParameter("/root/thermeq3/nsm.py");
  p.runAsynchronously();
}

void setup() {
#ifdef DEBUG_PRG
  Serial.begin(115200);
  while (!Serial);
#endif

  pinMode(RELAY_PIN, OUTPUT);
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
        planned_heating = true;
        turnIt(true);
        break;
      case 'S':
        planned_heating = false;
        turnIt(false);
        break;
      case 'E':
#ifdef IWANNABESAFE
        planned_heating = false;
        turnIt(false);
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
    }
    waitUntil = waitUntil + interval;
    digitalWrite(LOOP_LED, LOW);
  }

  if (mls - dhtReadUntil >= DHT_INTERVAL ) {
    dhtReadUntil = dhtReadUntil + DHT_INTERVAL;
    int chk = DHT.read22(DHT_PIN);

    switch (chk)
    {
      case DHTLIB_OK:
        tempError(false);
        if (DHT.temperature <= MIN_TEMP ) {
          alarmHit = true;
          turnIt_nomsg(true);
        }
        else {
          alarmHit = false;
          if (!planned_heating) {
            turnIt_nomsg(false);
          }
        }
        break;
      case DHTLIB_ERROR_CHECKSUM:
        tempError(true);
        alarmHit = true;
        turnIt_nomsg(true);
        break;
      case DHTLIB_ERROR_TIMEOUT:
        tempError(true);
        alarmHit = true;
        turnIt_nomsg(true);
        break;
      default:
        tempError(true);
        alarmHit = true;
        turnIt_nomsg(true);
        break;
    }
  }

  if (temp_error)
  {
    if (mls - tempBlink >= TEMP_ERROR_BLINK_PERIOD )
    {
      tempBlink = tempBlink + TEMP_ERROR_BLINK_PERIOD;
      if (temp_led_on) {
        showTempError(false);
      }
      else {
        showTempError(true);
      }
    }
  }
  else
  {
    showTempError(alarmHit);
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

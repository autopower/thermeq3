# Arduino sketch
## Code
There are two parts of thermeq3:
* python code, upload into /root/ files nsm.py and config.py and then please edit config.py
* **arduino code, upload with IDE**, 

## What I can change in sketch?
In arduino sketch
* `#define DEBUG_PRG` if you wanna print debug values via serial connection
* `#define RELAY_PIN 10` where is the relay pin?
* `#define RELAY_POWER 8` where is the power for relay? undef if relay is connected to 5V directly
* `#define STATUS_LED 9` status LED pin
* `#define ERROR_LED 8` error LED pin
* `#define LOOP_LED 13` activity/loop LED pin
* `#define BLINK_INTERVAL 150` blink interval in miliseconds
* `#define WAIT_UPDATE_SYNC 10000` how many millis wait to rerun upgraded python code
* `#define IWANNABESAFE` in case of any trouble, shutdown relay, undef for stay in last selected mode
* `unsigned long interval = 10*1000;` loop interval in seconds, arduino'll check for messages every 10 seconds, change 10 to anything you want
* `unsigned long app_interval = 10*60000;` check for running app interval in minutes, change 10 to anything you want

## Messages for arduino
* `H` heat!
* `S` stop heating!
* `E` error, error LED is lit
* `C` clear error LED
* `A` clear all LEDs
* `Q` fatal error, lit some disco effects on LEDs
* `D` dead! status LED breathing
* `R` restart app, eg. after upgrade
* 'M' show error if data from Max!Cube are not valid
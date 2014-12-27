#thermeq3
Boiler actor device for ELV/EQ-3 MAX! cube. And this is quick&dirty readme.

##Check betabeat directory
There's always new code, which seems to work on my development thermeq :)

##What is new?
###2014-Dec-27
* Simple install script: update opkg, installs openssl for python, create some scripts for nsm.py controlling.

###2014-Dec-26
* Ignoring valve after closing window
* Redesigned rooms/valves listing in log file
* Support for tasker, new bridge values: openwinlist and current_status, please take a look at `tasker` directory, there's simple example how to list open windows. Usefull especially when leaving house :)
* New CSV file handling, file is generated daily. New column in CSV, after date/time col, you can read 0/1 for heating (0=off, 1=on), so you can analyze when is boiler turned on or off (no more cat log | grep)
* Redesigned bridge functions (load/save), little bit failsafe (nothing extraordinary)
* Implemented support for day table, just enable beta functionality (thermeq3.ip/data/put/beta/yes) and edit table in nsm.py. You can control boiler in different way during day.

##Setup
You'll need:
* Arduino Yún
* 5V relay
* two or three (or one RGB LED) LED diodes and min 220ohm resistors
* installed and correctly running ELV/EQ-3 MAX! Cube
* boiler with switched heat by wire, via relay
* python-openssl library `opkg update; opkg install python-openssl`
* credentials for mail server with TLS (or modify code)
* storage space on microSD or USB,

Wiring:
* 220ohm resitor to pin13, then to code_run LED (in my setup green LED, lit when arduino script is reading messages from python part, this is sign of activity)
* 220ohm resitor to pin8, then to error LED (in my setup red LED, lit when any error)
* 220ohm resitor to pin9, then to status LED (in my setup blue LED, lit when heating is on)
* relay voltage +5V to pin8, or to the power 5V and you must comment `RELAY_POWER`
* relay in to pin10
* relay GND to GND
* LED diodes to GND
* your DHW/Boiler to com and NO (or NC) pins of relay (check your boiler documentation)

##Code
There are two parts of thermeq3:
* python code, upload into /root/ files nsm.py and config.py and then please edit config.py
* arduino code, upload with IDE

##How it works?
Arduino sketch runs python script `nsm.py` located in /root. And then check if it's running.
If not, runs it again from start. This script reads status from MAX! Cube and if any of radiator 
thermostat's valve is opened above `valve_pos` value, the relay is switched on, thus boiler/DHW is switched on.
This is done by saving char into the 'msg' bridge value, which is readable at Arduino side.
Heating also can be started if sum of radiator valves positions are geater than `num_of_valves * stp.per_switch`, 
where `stp.per_switch` is value in %. So if you have 10 valves in house and `stp.per_switch=8`, and sum of these
valves positions are 80+, relay is switched on. You can turn on this feature byt `stp.preference="per"` in python code.
If you need only simple total value, set `stp.preference="total"` and setup `total_switch` variable.

On start LEDs blink 4 times, then remains lit until arduino yun bridge component is initialized. 
Then blinks 4 times again.

##How to change values?
Just browse to `http://arduino.ip/data/put/interval/<your value>` to change 'interval' setting. E.g. if your browse to 
`http://arduino.ip/data/put/valve_pos/<your value>` you can change valve_pos value (e.g. how many % must be valve opened).

##What I can change?
###In Python code
* `devname` = device name
* `error` = errors since last status reports
* `status` = status of device (heating, idle, starting, error)
* `totalerrs` = total errors from start
* `valve_pos` = see above
* `per_switch` = see above
* `total_switch` = sum of valve positions, no matter how many valves are in house
* `interval` = see above
* `heattime` = total heat time from start, in seconds
* `command` = can be:
  * `quit` quits application
  * `mail` sends status report via mail
  * `dump` dumps valves into the `dumpdata` variable
  * `init` reinits python app
  * `uptime` updates uptime value
  * `log_debug` turns on logging on debug level
  * `log_info` turns on loggin on info level (default)
  * `mute` mutes warning for some time
  * `rebridge` reloads bridge file
  * `updatetime` updates uptime and heat time
  * `led` turns on or off heating LED (according to current heat status)
  * `upgrade` checks for upgrade, and if new version is available, upgrades nsm.py

###In config.py file
* `stp.max_ip = "192.168.0.10"` IP address of MAX! cube
* `stp.fromaddr = "devices@foo.local"` from, user name
* `stp.toaddr = "user@foo.local"` to email 
* `stp.mailserver = "mail.foo.local"` via this server
* `stp.mailport = 25` on port
* `stp.frompwd = "this.is.password"` login with this password
* `stp.devname = "hellmostat"` device name
* `stp.timeout = 10` timeout in secods, used in communicating with MAX! Cube and as a sleep time for flushing msg queue, set to similar value as `unsigned long interval` in arduino sketch
* `stp.extport = 29080` external port, this is the port (typically) on firewall where NAT is defined (so you can mute thermeq3 from internet), please setup your firewall/router to such scenario

###In arduino sketch
* `#define DEBUG_PRG` if you wanna print debug values via serial connection
* `#define RELAY_PIN 10` where is the relay pin?
* `#define RELAY_POWER 8` where is the power for relay? undef if relay is connected to 5V directly
* `#define STATUS_LED 9` status LED pin
* `#define ERROR_LED 8` error LED pin
* `#define LOOP_LED 13` activity/loop LED pin
* `#define BLINK_INTERVAL 150` blink interval in miliseconds
* `#define WAIT_UPDATE_SYNC 10000` how many millis wait to rerun upgraded python code
* `#define IWANNABESAFE` in case of any trouble shutdown relay, undef for stay in last selected mode
* `unsigned long interval = 10*1000;` loop interval in seconds, arduino'll check for messages every 10 seconds, change 10 to anything you want
* `unsigned long app_interval = 10*60000;` check for running app interval in minutes, change 10 to anything you want

##Messages for arduino
* `H` heat!
* `S` stop heating!
* `E` error, error LED is lit
* `C` clear error LED
* `Q` fatal error, lit some disco effects on LEDs
* `D` dead! status LED breathing
* `R` restart app, eg. after upgrade

##How to debug?
Python code produce 3 files:
* `/mnt/sd<x1>/<device_name>.csv`, simple comma separated value file with valve positions and temperature readings
* `/mnt/sd<x1>/<device_name>.log`, log file, really huge on `log_debug`
* `/mnt/sd<x1>/<device_name>_error.log`, python stderr redirected, use in case of crash, or send me this file.
* `/mnt/sd<x1>/<device_name>.bridge` saved bridge client values
* `/root/nsm.error` low level errors, which cant be written do .log file (e.g. due to lack of mounted storage media)
This file is also mailed to recipient on start. Then is truncated to zero size.

###Thats all folks. Stay tuned :)

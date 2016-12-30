#thermeq3
Boiler actor device for [ELV/EQ-3](http://www.eq-3.de/) [MAX! cube](http://www.eq-3.de/max-heizungssteuerung-produktdetail-kopie/items/bc-lgw-o-tw.html). Monitors radiators with MAX! eTRVs, so that the boiler will fire up when any radiator calls for heat. You will need a boiler with switched heat via wire, ie. an external thermostat. This will replace that. Designed to run on Arduino Yún.

thermeq3 features:
* switching DHW/Boiler according to valve position, you can set how many valves must be opened for how many %, or sum of the all valves in house to switch on DHW/Boiler
* profiles to choose right control values based on time or external temperature
* senses open windows and start heating after safe time to eliminate "panic" heating after forced ventilation
* any event on MAX! cube tracked down to log file
* notifies owner about opened windows after defined period, this period is automatically set according to external temperature
* owner can set various intervals for any important value
* autoupdate from github
* simple self diagnostics
* can be remote controlled via standard yún features (http/https)
* daily summary
* simple html status on user selectable port (via uhttpd)

##How it works (part I)?
Please take a look at this flowchart. This flowchart is simple representation of decision process. Green color denotes variables.
![flow1](https://raw.githubusercontent.com/autopower/thermeq3/master/flowchart/flowchart_1.png)

##Setup

### Equipment

* Arduino Yún
* 5V relay
* two or three (or one RGB LED) LED diodes and min 220ohm resistors
* installed and correctly running ELV/EQ-3 MAX! Cube
* boiler with switched heat by wire, via relay
* python-openssl library `opkg update; opkg install python-openssl`
* credentials for mail server with TLS (or modify code)
* storage space on microSD or USB

### Installation

1. Verify your ELV/EQ-3 MAX! Cube is up and running, and get its IP address.
1. On Arduino Yún or other Linux board with Arduino's Python Bridge library installed
  1. Wire 3 status LEDs and boiler relay as per `sketch` directory (circuit diagram or Fritzing sketch)
    * 220ohm resitor to pin13, then to code_run LED (in my setup green LED, lit when arduino script is reading messages from python part, this is sign of activity)
    * 220ohm resitor to pin8, then to error LED (in my setup red LED, lit when any error)
    * 220ohm resitor to pin9, then to status LED (in my setup blue LED, lit when heating is on)
    * relay in to pin10
    * relay GND to GND
    * LED diodes to GND
    * your DHW/Boiler to COM and NO (or NC) pins of relay (check your boiler documentation)
  1. Upload Arduino sketch `thermeq3.ino` to Yún using Arduino IDE on your computer
    * For v150, use `yun-sketch/thermeq3/thermeq3.ino`
    * For v200+, use `yun-sketch/thermeq3_V200/thermeq3_V200.ino`
    * if you are using DHT sensor, please use `yun-sketch/thermeq3_dht/thermeq3_dht.ino` by @bilbolodz
1. Via SSH
  * Update `opkg`: `opkg update`
  * Update `wget`: `opkg upgrade wget`
  * Install `thermeq3` (V200+ is current version, V1xx is obsolete, sorry for such mess, fix in progress)
    * For v150, use  `wget --no-check-certificate --quiet --output-document /root/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/obsolete/install.sh`
    * For v200+, use `wget --no-check-certificate --quiet --output-document /root/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/install.sh`
    * Make the installer executable: `chmod +x /root/install.sh` (if you are upgrading from V231-, skip this step )
    * Run the installer script: `/root/install.sh thermeq3` (if you are upgrading from V231-, run `/root/upgrade.sh`)
    * Fill out the required values in the config file: `/root/config.py`
      * You'll need SMTP server details and [Open Weather Map API key](http://openweathermap.org/appid) (sign-up is free).

###Upgrading from V2xx to V231+
If you are upgrading from version below V231** and you have working installation, please use [this script](https://github.com/autopower/thermeq3/tree/master/install/current/upgrade.sh) or `wget --no-check-certificate --quiet --output-document /root/upgrade.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/upgrade.sh;chmod +x /root/upgrade.sh`.
Beta directory is symlink for compatibility and semiauto update.

## Troubleshooting

See the [diagnostic readme](https://github.com/autopower/thermeq3/tree/master/install/diag/README.md)
 
##How to ignore some valves "forever"
It's really simple. After succesfull start of thermeq3, check log file for heater thermostat IDs (HT).
Then find out bridge file and run editor (vi for example).
Look for "ignored" word (with quotes), if it's empty (looks like `"ignored":{}`) and update. Let be HT1=06ABCD and HT2=06ABCE, then ignored will look like this:
```
...
"ignored":{"06ABCD": 1924991999, "06ABCE": 1924991999}
...
```
Save file and wait. If you aren't sporting `vi` just use browser and set ignored with URL:
`http://<arduino.local>/data/put/ignored/{"06ABCD": 1924991999, "06ABCE": 1924991999}`
And why 1924991999? It's simple, this is time since epoch, 1924991999=31/Dec/2030. 


##What's new?
###2016-Dec-30
* for the bravest there is an [alpha channel](https://github.com/autopower/thermeq3/tree/master/install/alpha)
* this is only for upgrade, please use [this upgrade script](https://github.com/autopower/thermeq3/tree/master/install/alpha/upgrade.sh)

###2016-Dec-25
* bridge file moved to sd card, if found in `/root` then moved do sd card
* some new shell scripts below
  * [upgrade](https://github.com/autopower/thermeq3/tree/master/install/upgrade.sh) thermeq3
  * [recreate uhttpd files](https://github.com/autopower/thermeq3/tree/master/install/recreate_http.sh) on sd card
  * [create nsm file](https://github.com/autopower/thermeq3/tree/master/install/create_nsm.sh) in `/root`, just for compatibility issues 
* wall thermostat temperature fixed

###2016-Nov-13
* RPi preparedness. Please follow instruction in code. Unfortunatelly I don't have RPi to test it, please report if you need any changes.

###2016-Nov-01
* Lot of fixes. 

###2016-Apr-08
* to use "current" temperature for loggging find out this text `# comment line below to use current temp` in nsm.py (for V1xx) or in thermeq3.py (for V2xx) and follow 
instructions. Please keep in mind, that current temperature on heater thermostat can be 0.0 (zero) because of limitations of HT! 

###2016-Mar-12
* despite fact that V1xx is obsolete, here is the new version, V152, fixing some bugs, thanks to TonyV from UK :0

###2015-Dec-18
* lib version updated

###2015-Dec-13
* directory structure reorganised
* new install script for all version (old one in one file (nsm.py), new one with libraries)

###2015-Dec-11
* some cleanup on github

###2015-Dec-10
* new librarysed version in betabeat
* new install script for lib version in scripts
* some code overhaul :)

###2015-Dec-04
* betabeat: new RPi version 

###2015-Nov-28
* betabeat: bridge routine rewrited, some support for literal processing
* betabeat: ignore intervals corrected
* betabeat: you can ignore valve forever, just edit bridgefile and to ign codeword add valveserial and time since epoch=1924991999, its 31/Dec/2030 :), e.g. {"06ABCD": 1924991999}
* betabeat: new boiler controlling variable, svpnmw (Single Valve Position, No Matter What) in %, if any of valves opened more than svpnmw then heating is on, to turn off just set to 101% 

###2015-Nov-27
* betabeat: new weather API used, yahoo YQL and OWM, API key for OWM is from OWM example page, please change it
* just for sure, use "new" bridge python library from https://codeload.github.com/arduino/YunBridge/zip/master

###2015-Nov-26
* new codeword, mode, can be auto or manual, added after request, in auto mode thermeq3 sends H/S commands to arduino part, in manual mode do nothing :)

###2015-Nov-02
* betabeat: some javascript code (based on jquery ui) to control device, ugly, not fully functional, first steps with JS and CSS ;)
* betabeat: code cleanup

###2015-Nov-01
* betabeat: new arduino command A, clears LED
* betabeat: some cleanup, codeword dump removed

###2015-Oct-31
* minor fixes
* new status messages
* JSON formated string in current status

###2015-Oct-21
* some fix in RPi version, please check commented code and uncomment (setblocking)
* if anyone need room names in CSV, uncomment code in exportCSV()
* minor updates 

###2015-Oct-10
* minor updates, betabeat and production are the same version
* alpha RPi version, only change is the abstraction code replacing bridgeclient (but as reported from users, it works! :)) 

###2015-Mar-23
* minor updates

###2015-Mar-15
* updating valve ignore interval according to outer temperature

###2015-Jan-18
* more pythonic code, classes etc.

###2015-Jan-07
* betabeat: yahoo weather and oww interval sampling working
* betabeat: in secondary web folder `nice.html` file is generated, contains nice formated status (hm, if pre means nice)

###2015-Jan-06
* support for yahoo weather, stay tuned for open window interval auto update by actual weather situation (temperature, humidity), better ventilation 'support'
* resample function
* support directory in betabeat, check code for sampling function, modify to your needs

###2015-Jan-03
* betabeat: if webserver directory not exist, is created
* betabeat: correct response on secondary web server, eg: http://arduino.ip:second_port/cgi-bin/status returns app/json from status.xml file

###2014-Dec-28
* betabeat: open window list and current status separated into secondary web server as xml files, accessible w/o any credentials

###2014-Dec-27
* Simple install script: update opkg, installs openssl for python, create some scripts for nsm.py controlling.

###2014-Dec-26
* Ignoring valve after closing window
* Redesigned rooms/valves listing in log file
* Support for tasker, new bridge values: openwinlist and current_status, please take a look at `tasker` directory, there's simple example how to list open windows. Usefull especially when leaving house :)
* New CSV file handling, file is generated daily. New column in CSV, after date/time col, you can read 0/1 for heating (0=off, 1=on), so you can analyze when is boiler turned on or off (no more cat log | grep)
* Redesigned bridge functions (load/save), little bit failsafe (nothing extraordinary)
* Implemented support for day table, just enable beta functionality (thermeq3.ip/data/put/beta/yes) and edit table in nsm.py. You can control boiler in different way during day.



##Code
There are two parts of thermeq3:
* python code, upload into /root/ files nsm.py and config.py and then please edit config.py
* arduino code, upload with IDE

##How it works (part II)?
Arduino sketch runs python script `nsm.py` located in /root. And then check if it's running.
If not, runs it again from start. This script reads status from MAX! Cube and if any of radiator 
thermostat's valve is opened above `valve_pos` value, the relay is switched on, thus boiler/DHW is switched on.
This is done by saving char into the 'msg' bridge value, which is readable at Arduino side.
Heating also can be started if sum of radiator valves positions are geater than `num_of_valves * stp.per_switch`, 
where `stp.per_switch` is value in %. So if you have 10 valves in house and `stp.per_switch=8`, and sum of these
valves positions are 80+, relay is switched on. You can turn on this feature by `stp.preference="per"` in python code.
If you need only simple total value, set `stp.preference="total"` and setup `total_switch` variable.

On start LEDs blink 4 times, then remains lit until arduino yun bridge component is initialized. 
Then blinks 4 times again.

##How to change values?
If you want change some values when nsm.py is running, just browse to `http://arduino.ip/data/put/interval/<your value>` 
to change 'interval' setting. E.g. if your browse to `http://arduino.ip/data/put/valve_pos/<your value>` 
you can change valve_pos value (e.g. how many % must be valve opened).

##What I can change?
###In Python code
* `devname` = device name
* `error` = errors since last status reports
* `status` = status of device (heating, idle, starting, error)
* `totalerrs` = total errors from start
* `valve_pos` = see above
* `total_switch` = sum of valve positions, no matter how many valves are in house
* `interval` = see above
* `heattime` = total heat time from start, in seconds
* `command` = can be:
  * `quit` quits application
  * `mail` sends status report via mail
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
You scan edit `config.py` file with default editor `vi`. If you are no familiar with `vi` (try [this man](https://www.freebsd.org/cgi/man.cgi?vi)), you can use your favourite editor on your platform and transfer file via ftp/scp. For example if you are using windows, you can use [pspad](http://www.pspad.com/en/) and transfer file via [winscp](https://winscp.net/eng/index.php).
* `stp.max_ip = "192.168.0.10"` IP address of MAX! cube
* `stp.fromaddr = "devices@foo.local"` from, user name
* `stp.toaddr = "user@foo.local"` to email 
* `stp.mailserver = "mail.foo.local"` via this server
* `stp.mailport = 25` on this port
* `stp.frompwd = "this.is.password"` login with this password
* `stp.devname = "hellmostat"` device name
* `stp.timeout = 10` timeout in secods, used in communicating with MAX! Cube and as a sleep time for flushing msg queue, set to similar value as `unsigned long interval` in arduino sketch
* `stp.extport = 29080` external port, this is the port (typically) on firewall where NAT is defined (so you can mute thermeq3 from internet), please setup your firewall/router to such scenario
* `stp.owm_api_key = "your owm api key"` this is API key for OWM service

For V200+ is `stp.`` replaced with `self.setup.`

###In arduino sketch
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

##Messages for arduino
* `H` heat!
* `S` stop heating!
* `E` error, error LED is lit
* `C` clear error LED
* `A` clear all LEDs
* `Q` fatal error, lit some disco effects on LEDs
* `D` dead! status LED breathing
* `R` restart app, eg. after upgrade

##How to debug?
Python code produce these files:
* `/mnt/sd<x1>/csv/<device_name>.csv`, simple comma separated value file with valve positions and temperature readings
* `/mnt/sd<x1>/<device_name>.log`, log file, really huge on `log_debug`
* `/mnt/sd<x1>/<device_name>_error.log`, python stderr redirected, use in case of crash, or send me this file.
* `/root/<device_name>.bridge` saved bridge client values
* `/root/nsm.error` low level errors, which cant be written do .log file (e.g. due to lack of mounted storage media). This file is also mailed to recipient on start. Then is truncated to zero size.

Please note, that x1 stands for a1 or b1, so full path will be `/mnt/sda1` or `/mnt/sdb1`.

###Thats all folks. Stay tuned :)

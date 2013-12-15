#thermeq3
Boiler actor device for ELV/EQ-3 MAX! cube. And this is quick&dirty readme :)

##Setup
You'll need:
* Arduino Yún
* 5V relay
* two or three (or one RGB LED) LED diodes and min 220ohm resistors
* installed and correctly running ELV/EQ-3 MAX! Cube
* boiler with switched heat by wire, via relay
* python-openssl library `opkg update; opkg install python-openssl`
* credentials for mail server with TLS (or modify code)
* storage space on microSD or USB (please modify path to storage, default is `/mnt/sda1`)

Wiring:
* 220ohm resitor to pin13, then to code_run LED (in my setup blue LED, lit when arduino script is reading messages from python part, this is sign of activity)
* 220ohm resitor to pin6, then to error LED (in my setup red LED, lit when any error)
* 220ohm resitor to pin5, then to status LED (in my setup green LED, lit when heating is on)
* relay voltage +5V to pin7, or to the power 5V and you must modify arduino sketch (relay is swithed on only if heating is required)
* relay in to pin8
* relay GND to GND
* LED diodes to GND
* your DHW/Boiler to com and NO (or NC) pins of relay (check your boiler documentation)

##Code
There are two parts of thermeq3:
* python code, upload into /root/nsm.py and then please change:
 * IP of your Max Cube
 * mail server address
 * from and to address
 * password
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
* `devname` = device name (another script (in testing) sends status reports according to crontab settings)
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

##How to debug?
Python code produce 3 files:
* `/mnt/sda1/<device_name>.csv`, simple comma separated value file with valve positions and temperature readings
* `/mnt/sda1/<device_name>.log`, log file, really huge on `log_debug`
* `/mnt/sda1/<device_name>_error.log`, python stderr redirected, use in case of crash, or send me this file. 
This file is also mailed to recipient on start. Then is truncated to zero size.

###Thats all folks. Stay tuned :)

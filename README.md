# thermeq3
Boiler actor device for [ELV/EQ-3](http://www.eq-3.de/) [MAX! cube](http://www.eq-3.de/max-heizungssteuerung-produktdetail-kopie/items/bc-lgw-o-tw.html).
Please [take a look](https://github.com/autopower/thermeq3/wiki) at wiki for detailed information.
 
## What's new?
### 2019-Dec-30
* alpha V298, many V297 bug fixed :)
* known issue: open window adjustment can go wrong, debugging support for maxeq3 module added

### 2019-Dec-29
* alpha V297
* proxy fully implemented
* multiple checks and error implemented, especially for wrong M response from MaxCube
* manual mode implemented as fail safe, if any error experienced, thermeq3 switched to manual mode to retain heating
* minor improvements

### 2019-Nov-17
* multiple checks and error response added in alpha V295
* support for proxying Max!Cube response to other devices, new file proxy.eq3 generated every cube read

### 2019-Nov-15
* alpha V294 ready for standalone operation, e.g. no need for yun or RPi, can operate in any linux/windows distro
* relay actions separated into extaction.py file, this must be implemented to suite your separate relay

### 2019-Feb-16
* config_me script updated
* dashboard updated
* alpha V287 with new yahoo weather support

### 2019-Feb-15
If you experiencing problems with retired yahoo weather code, please switch to OpenWeather. Simply update bridge value `weather_reference` with value `owm`, e.g. http://<ardu.ip>/data/put/weather_reference/owm
If you want still use yahoo weather, please get your AppID and keys on [this page](https://developer.yahoo.com/weather/). Support for new API will be available in few days.

### 2019-Feb-01
Yahoo weather API is [retired](https://developer.yahoo.com/weather/?guccounter=1). Please wait for fix.

### 2018-Nov-25
* minor fix
* Python 3 compatible version in alpha

### 2018-Nov-19
* RPi port update, minor fixes
* new [universal installer](https://github.com/autopower/thermeq3/blob/master/install/uni_install.sh) for both platforms, feel free to test
* redesigned dashboard installers 

### 2018-Nov-13
* RPi port in alpha stage, testers still wanted

### 2018-Nov-11
* RPi support added, testers wanted

### 2018-Nov-09
* simple external device based on ESP8266 and eInk to display status with open windows list. Feel free to test and comment.

### 2018-Oct-22
* calling to arms Yún Rev2 users, I'll be pointed to some incompatibilities between Rev1 and Rev2. Rev2 users, please use `https://github.com/autopower/thermeq3/tree/master/install/alpha_Yun_Rev2`
 install script to check if install script/wget is working flawless 

### 2018-Jul-06
* someone calls for manual heating override, please take a look at new dashboard. For those who sports simple URL, please use `http://ardu.ip/data/put/msg/S` to stop or
 `http://ardu.ip/data/put/msg/H` to start heating
 
### 2017-Oct-14
* possibility to get temperature and humidity from local source, bridge values: local_temp, local_humidity and weather_reference
* fixed persistence of values after reboot
* complete system dump in bridge, key "dump"

### 2017-Oct-10
* minor fixes in nsm and dashboard
* separated mail user for login and from address variable

### 2017-Oct-07
* readme update
* yun sketch update addressing wrong response from cube (typically wrong M response)
* watchdog script preparedness

### 2017-Sep-16
* V250 in alpha
* weather fixes
* new config file support
* lifetime valve ignore from config file, there is no need to add valve manual via bridge! 

### 2017-Jan-14
* file del_dev.py in support directory for deleting devices from cube. In case that you have corrupted condfiguration and many Wrong address errors in log file.

### 2016-Dec-30
* for the bravest there is an [alpha channel](https://github.com/autopower/thermeq3/tree/master/install/alpha)
* this is only for upgrade, please use [this upgrade script](https://github.com/autopower/thermeq3/tree/master/install/alpha/upgrade.sh)

### 2016-Dec-25
* bridge file moved to sd card, if found in `/root` then moved do sd card
* some new shell scripts below
  * [upgrade](https://github.com/autopower/thermeq3/tree/master/install/upgrade.sh) thermeq3
  * [recreate uhttpd files](https://github.com/autopower/thermeq3/tree/master/install/recreate_http.sh) on sd card
  * [create nsm file](https://github.com/autopower/thermeq3/tree/master/install/create_nsm.sh) in `/root`, just for compatibility issues 
* wall thermostat temperature fixed

### 2016-Nov-13
* RPi preparedness. Please follow instruction in code. Unfortunatelly I don't have RPi to test it, please report if you need any changes.

### 2016-Nov-01
* Lot of fixes. 

### 2016-Apr-08
* to use "current" temperature for loggging find out this text `# comment line below to use current temp` in nsm.py (for V1xx) or in thermeq3.py (for V2xx) and follow 
instructions. Please keep in mind, that current temperature on heater thermostat can be 0.0 (zero) because of limitations of HT! 

### 2016-Mar-12
* despite fact that V1xx is obsolete, here is the new version, V152, fixing some bugs, thanks to TonyV from UK :0

### 2015-Dec-18
* lib version updated

### 2015-Dec-13
* directory structure reorganised
* new install script for all version (old one in one file (nsm.py), new one with libraries)

### 2015-Dec-11
* some cleanup on github

### 2015-Dec-10
* new librarysed version in betabeat
* new install script for lib version in scripts
* some code overhaul :)

### 2015-Dec-04
* betabeat: new RPi version 

### 2015-Nov-28
* betabeat: bridge routine rewrited, some support for literal processing
* betabeat: ignore intervals corrected
* betabeat: you can ignore valve forever, just edit bridgefile and to ign codeword add valveserial and time since epoch=1924991999, its 31/Dec/2030 :), e.g. {"06ABCD": 1924991999}
* betabeat: new boiler controlling variable, svpnmw (Single Valve Position, No Matter What) in %, if any of valves opened more than svpnmw then heating is on, to turn off just set to 101% 

### 2015-Nov-27
* betabeat: new weather API used, yahoo YQL and OWM, API key for OWM is from OWM example page, please change it
* just for sure, use "new" bridge python library from https://codeload.github.com/arduino/YunBridge/zip/master

### 2015-Nov-26
* new codeword, mode, can be auto or manual, added after request, in auto mode thermeq3 sends H/S commands to arduino part, in manual mode do nothing :)

### 2015-Nov-02
* betabeat: some javascript code (based on jquery ui) to control device, ugly, not fully functional, first steps with JS and CSS ;)
* betabeat: code cleanup

### 2015-Nov-01
* betabeat: new arduino command A, clears LED
* betabeat: some cleanup, codeword dump removed

### 2015-Oct-31
* minor fixes
* new status messages
* JSON formated string in current status

### 2015-Oct-21
* some fix in RPi version, please check commented code and uncomment (setblocking)
* if anyone need room names in CSV, uncomment code in exportCSV()
* minor updates 

### 2015-Oct-10
* minor updates, betabeat and production are the same version
* alpha RPi version, only change is the abstraction code replacing bridgeclient (but as reported from users, it works! :)) 

### 2015-Mar-23
* minor updates

### 2015-Mar-15
* updating valve ignore interval according to outer temperature

### 2015-Jan-18
* more pythonic code, classes etc.

### 2015-Jan-07
* betabeat: yahoo weather and oww interval sampling working
* betabeat: in secondary web folder `nice.html` file is generated, contains nice formated status (hm, if pre means nice)

### 2015-Jan-06
* support for yahoo weather, stay tuned for open window interval auto update by actual weather situation (temperature, humidity), better ventilation 'support'
* resample function
* support directory in betabeat, check code for sampling function, modify to your needs

### 2015-Jan-03
* betabeat: if webserver directory not exist, is created
* betabeat: correct response on secondary web server, eg: http://arduino.ip:second_port/cgi-bin/status returns app/json from status.xml file

### 2014-Dec-28
* betabeat: open window list and current status separated into secondary web server as xml files, accessible w/o any credentials

### 2014-Dec-27
* Simple install script: update opkg, installs openssl for python, create some scripts for nsm.py controlling.

### 2014-Dec-26
* Ignoring valve after closing window
* Redesigned rooms/valves listing in log file
* Support for tasker, new bridge values: openwinlist and current_status, please take a look at `tasker` directory, there's simple example how to list open windows. Usefull especially when leaving house :)
* New CSV file handling, file is generated daily. New column in CSV, after date/time col, you can read 0/1 for heating (0=off, 1=on), so you can analyze when is boiler turned on or off (no more cat log | grep)
* Redesigned bridge functions (load/save), little bit failsafe (nothing extraordinary)
* Implemented support for day table, just enable beta functionality (thermeq3.ip/data/put/beta/yes) and edit table in nsm.py. You can control boiler in different way during day.

# Thats all folks. Stay tuned :)

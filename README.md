# thermeq3

Boiler controller for the [ELV/eQ-3](http://www.eq-3.de/) [MAX! Cube](http://www.eq-3.de/max-heizungssteuerung-produktdetail-kopie/items/bc-lgw-o-tw.html)
heating system, and now also for **HomeMatic IP** with a CCU3 or RaspberryMatic.

thermeq3 reads the valve positions of the radiator thermostats and switches
the boiler on only when the rooms actually need heat. See the
[wiki](https://github.com/autopower/thermeq3/wiki) for detailed information.

## Repository contents

| Folder | Description |
|---|---|
| [`ccu3`](ccu3) | **New.** HomeMatic script for the CCU3 / RaspberryMatic that switches a boiler (via HmIP-WHS2) based on HomeMatic IP TRV valve positions. Features automatic TRV discovery, valve-count hysteresis, SVPNMW, a failsafe, and Home Assistant integration. Runs on the CCU itself; no extra hardware is needed. See [`ccu3/README.md`](ccu3/README.md). |
| [`install`](install) | Installers and packages for the MAX! version (Arduino Yún, Raspberry Pi, dashboard) |
| [`yun-sketch`](yun-sketch) | Arduino sketches for the Yún |
| [`eInk Display`](eInk%20Display) | External ESP8266 status display with an e-ink screen |
| [`support`](support) | Helper scripts (relay test, deleting devices from the cube) |
| [`sketch`](sketch), [`flowchart`](flowchart) | Wiring sketch and flowchart |
| [`obsolete`](obsolete) | Old versions, kept for reference |

## What's new?

### 2026-Oct-24
* New [`ccu3`](ccu3) folder: boiler control for HomeMatic IP on the CCU3 / RaspberryMatic.
  * Automatically discovers all HmIP radiator thermostats (eTRV); no editing is needed when you add or remove one.
  * Switches the boiler via an HmIP-WHS2 with ON/OFF valve thresholds and a minimum number of open valves.
  * Supports SVPNMW (Single Valve Position, No Matter What), known from the MAX! version.
  * Ignores unreachable thermostats and switches the boiler off if none are reachable.
  * Selectable controller: CCU, ESP (OpenTherm thermostat, with automatic fallback to the CCU), or manual.
  * All settings are CCU system variables, editable from the WebUI or from Home Assistant.

### 2020-Oct-13
* Fixed processing of malformed L responses. Up to 128 devices can be processed (more than eQ-3 allows).

### 2020-Oct-07
* Fixed wrong processing of cube data, especially the L response. If the cube was misconfigured (for example, a device was present in the L response but missing from the C response), the loop never ended.

### 2020-Sep-29
* Alpha V307: added support for SVPNMW in profiles.

### 2020-May-24
* Alpha V304: fix for manual mode. If the temperature is above `setup.summertime`, heating is not started. This is a quick fix for inconsistent MAX! Cube behaviour in summer.

### 2020-Apr-04
* Alpha V302 with more diagnostics for temperature/time profiles.

### 2020-Jan-07
* Alpha V299: manual mode is fully implemented. thermeq3 is now fail-safe against MAX! Cube errors such as a lost configuration.
* Fixed the open window adjustment.

### 2019-Dec-31
* Alpha V298: many V297 bugs fixed :)
* Known issue: the open window adjustment can go wrong. Added debugging support to the maxeq3 module.

### 2019-Dec-29
* Alpha V297.
* Proxy fully implemented.
* Added checks and error handling, especially for a wrong M response from the MAX! Cube.
* Manual mode implemented as a failsafe: if any error occurs, thermeq3 switches to manual mode to keep heating.
* Minor improvements.

### 2019-Nov-17
* Alpha V295: added checks and error responses.
* Support for proxying the MAX! Cube response to other devices. A new file, `proxy.eq3`, is generated on every cube read.

### 2019-Nov-15
* Alpha V294 is ready for standalone operation: no Yún or Raspberry Pi is needed, and it runs on any Linux or Windows system.
* Relay actions are separated into the `extaction.py` file. Implement it to suit your own relay.

### 2019-Feb-16
* Updated the `config_me` script.
* Updated the dashboard.
* Alpha V287 with support for the new Yahoo Weather API.

### 2019-Feb-15
If you have problems with the retired Yahoo Weather code, switch to OpenWeatherMap: set the bridge value `weather_reference` to `owm`, for example `http://<ardu.ip>/data/put/weather_reference/owm`.
If you still want to use Yahoo Weather, get your AppID and keys on [this page](https://developer.yahoo.com/weather/). Support for the new API will be available in a few days.

### 2019-Feb-01
The Yahoo Weather API has been [retired](https://developer.yahoo.com/weather/?guccounter=1). A fix is on the way.

### 2018-Nov-25
* Minor fix.
* Python 3 compatible version in alpha.

### 2018-Nov-19
* Raspberry Pi port update, minor fixes.
* New [universal installer](install/uni_install.sh) for both platforms; feel free to test it.
* Redesigned dashboard installers.

### 2018-Nov-13
* Raspberry Pi port in alpha stage; testers are still wanted.

### 2018-Nov-11
* Raspberry Pi support added; testers wanted.

### 2018-Nov-09
* Simple [external display](eInk%20Display) based on an ESP8266 and an e-ink screen that shows the status and the list of open windows. Feel free to test and comment.

### 2018-Oct-22
* Call to Yún Rev2 users: I was told about some incompatibilities between Rev1 and Rev2. Rev2 users, please use the [Rev2 install script](obsolete/install/alpha_Yun_Rev2) and check that the install script and wget work flawlessly.

### 2018-Jul-06
* Manual heating override was requested; take a look at the new dashboard. If you prefer a simple URL, use `http://ardu.ip/data/put/msg/S` to stop heating or
  `http://ardu.ip/data/put/msg/H` to start it.

### 2017-Oct-14
* Temperature and humidity can be read from a local source; bridge values `local_temp`, `local_humidity` and `weather_reference`.
* Fixed persistence of values after a reboot.
* Complete system dump in the bridge, key `dump`.

### 2017-Oct-10
* Minor fixes in nsm and the dashboard.
* Separate variables for the mail login user and the "from" address.

### 2017-Oct-07
* README update.
* Yún sketch update addressing wrong responses from the cube (typically a wrong M response).
* Preparation for a watchdog script.

### 2017-Sep-16
* V250 in alpha.
* Weather fixes.
* Support for the new config file.
* Permanent valve ignore from the config file; there is no need to add valves manually via the bridge.

### 2017-Jan-14
* New file [`del_dev.py`](support/del_dev.py) in the `support` directory for deleting devices from the cube. Use it if you have a corrupted configuration and many "Wrong address" errors in the log file.

### 2016-Dec-30
* For the bravest, there is an [alpha channel](install/alpha).
* It is for upgrades only. The original upgrade script is no longer available in the repository.

### 2016-Dec-25
* The bridge file moved to the SD card. If it is found in `/root`, it is moved to the SD card.
* New shell scripts (now in the [`obsolete`](obsolete) folder):
  * [recreate uhttpd files](obsolete/recreate_http.sh) on the SD card;
  * [create the nsm file](obsolete/create_nsm.sh) in `/root`, for compatibility only.
* Fixed the wall thermostat temperature.

### 2016-Nov-13
* Raspberry Pi preparation. Please follow the instructions in the code. Unfortunately, I don't have a Raspberry Pi to test it, so please report any changes you need.

### 2016-Nov-01
* Lots of fixes.

### 2016-Apr-08
* To use the "current" temperature for logging, find the text `# comment line below to use current temp` in `nsm.py` (for V1xx) or in `thermeq3.py` (for V2xx) and follow
  the instructions. Keep in mind that the current temperature on a heater thermostat can be 0.0 (zero) because of a limitation of the thermostat.

### 2016-Mar-12
* Although V1xx is obsolete, here is a new version, V152, fixing some bugs. Thanks to TonyV from the UK :)

### 2015-Dec-18
* Library version updated.

### 2015-Dec-13
* Directory structure reorganised.
* New install script for all versions (the old single-file `nsm.py` and the new library version).

### 2015-Dec-11
* Some cleanup on GitHub.

### 2015-Dec-10
* New library version in betabeat.
* New install script for the library version in scripts.
* Some code overhaul :)

### 2015-Dec-04
* Betabeat: new Raspberry Pi version.

### 2015-Nov-28
* Betabeat: bridge routine rewritten, some support for literal processing.
* Betabeat: ignore intervals corrected.
* Betabeat: you can ignore a valve forever. Edit the bridge file and add the valve serial with the time since epoch 1924991999 (31 Dec 2030 :)) to the `ign` codeword, for example `{"06ABCD": 1924991999}`.
* Betabeat: new boiler control variable, `svpnmw` (Single Valve Position, No Matter What), in %. If any valve is open more than `svpnmw`, heating is on. To disable it, set it to 101 %.

### 2015-Nov-27
* Betabeat: new weather APIs, Yahoo YQL and OWM. The OWM API key is taken from the OWM example page; please replace it with your own.
* To be sure, use the "new" bridge Python library from https://codeload.github.com/arduino/YunBridge/zip/master.

### 2015-Nov-26
* New codeword, `mode`, added on request. It can be `auto` or `manual`. In auto mode thermeq3 sends H/S commands to the Arduino part; in manual mode it does nothing :)

### 2015-Nov-02
* Betabeat: some JavaScript code (based on jQuery UI) to control the device. Ugly and not fully functional; my first steps with JS and CSS ;)
* Betabeat: code cleanup.

### 2015-Nov-01
* Betabeat: new Arduino command `A`, clears the LED.
* Betabeat: some cleanup; codeword `dump` removed.

### 2015-Oct-31
* Minor fixes.
* New status messages.
* Current status as a JSON-formatted string.

### 2015-Oct-21
* Fix in the Raspberry Pi version; please check the commented code and uncomment `setblocking`.
* If you need room names in the CSV, uncomment the code in `exportCSV()`.
* Minor updates.

### 2015-Oct-10
* Minor updates; betabeat and production are the same version.
* Alpha Raspberry Pi version. The only change is the abstraction code replacing `bridgeclient` (and, as users report, it works! :)).

### 2015-Mar-23
* Minor updates.

### 2015-Mar-15
* The valve ignore interval is updated according to the outdoor temperature.

### 2015-Jan-18
* More Pythonic code, classes etc.

### 2015-Jan-07
* Betabeat: Yahoo Weather and OWM interval sampling working.
* Betabeat: a `nice.html` file is generated in the secondary web folder with a nicely formatted status (well, if `<pre>` counts as nice).

### 2015-Jan-06
* Support for Yahoo Weather. Stay tuned for automatic updates of the open window interval based on the current weather (temperature, humidity) for better ventilation support.
* Resample function.
* New `support` directory in betabeat; check the code for the sampling function and modify it to your needs.

### 2015-Jan-03
* Betabeat: the web server directory is created if it does not exist.
* Betabeat: correct response from the secondary web server, e.g. `http://arduino.ip:second_port/cgi-bin/status` returns `application/json` from the `status.xml` file.

### 2014-Dec-28
* Betabeat: the open window list and the current status are served as XML files by a secondary web server, accessible without credentials.

### 2014-Dec-27
* Simple install script: updates opkg, installs OpenSSL for Python, and creates some scripts for controlling `nsm.py`.

### 2014-Dec-26
* Valves are ignored after a window is closed.
* Redesigned room/valve listing in the log file.
* Support for Tasker, with new bridge values `openwinlist` and `current_status`. Take a look at the [`tasker`](obsolete/tasker) directory for a simple example of how to list open windows. Useful especially when leaving the house :)
* New CSV file handling: a new file is generated daily. A new column after the date/time column shows 0/1 for heating (0 = off, 1 = on), so you can analyse when the boiler was on or off (no more `cat log | grep`).
* Redesigned bridge functions (load/save), a little more fail-safe (nothing extraordinary).
* Support for a day table. Enable beta functionality (`thermeq3.ip/data/put/beta/yes`) and edit the table in `nsm.py` to control the boiler differently during the day.

# That's all, folks. Stay tuned :)

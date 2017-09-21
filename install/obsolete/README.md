# thermeq3
### Install application
Access yún via ssh (e.g. Windows users can use putty)
* Update `opkg`: `opkg update`
* Update `wget`: `opkg upgrade wget`
* Install `thermeq3`, please look below for help  
* Run the installer script: `/root/install.sh <your installation name>` (if you are upgrading from V231-, run `/root/upgrade.sh`), for example `/root/install.sh boilerstarter`, this `boilerstarter` name will be used as 
device name
* **Edit required values in the config file** Please take a look below how to modify config file. 
* You'll need SMTP server details and [Open Weather Map API key](http://openweathermap.org/appid) (sign-up is free).

### I want to install version below 231
For v200+, use `wget --no-check-certificate --quiet --output-document /root/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/install.sh;chmod +x /root/upgrade.sh`

### I want to install v150
Versions below 200 are obsolete! For v150, use `wget --no-check-certificate --quiet --output-document /root/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/obsolete/install.sh;chmod +x /root/upgrade.sh`

### Upgrading from V2xx to V231+
**If you are upgrading from version below V231** and you have working installation, please use [this script](https://github.com/autopower/thermeq3/tree/master/install/current/upgrade.sh) or `wget --no-check-certificate --quiet --output-document /root/upgrade.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/upgrade.sh;chmod +x /root/upgrade.sh`.

### Modifying config file
#### V199-
You can edit `config.py` file with default editor `vi`. If you are no familiar with `vi` (try [this man](https://www.freebsd.org/cgi/man.cgi?vi)), you can use your favourite editor on your platform and transfer file via ftp/scp. For example if you are using windows, you can use [pspad](http://www.pspad.com/en/) and transfer file via [winscp](https://winscp.net/eng/index.php).
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

#### V200 to V230
For V200+ `stp.` is replaced with `self.setup.` or `self.` so `stp.max_ip` becomes `self.setup.max_ip`.

#### V231 to V249
**Version 231+ automatically reads old config.py file format (plain python code) and converts it to JSON format.**
If you are using V231+ please use current config file in JSON format with name `thermeq.json`


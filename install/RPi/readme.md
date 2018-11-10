# Installation on RPi
## This is very early alpha :) be patient

Access rpi via ssh or terminal
* Install `thermeq3` typing `wget --no-check-certificate --quiet --output-document /home/pi/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/RPi/install.sh;chmod +x /home/pi/install.sh`  
* Run the installer script: `./install.sh <your installation name>`, for example `./install.sh boilerstarter`, this `boilerstarter` name will be used as device name 
* You'll need SMTP server details and [Open Weather Map API key](http://openweathermap.org/appid) (sign-up is free).

## Get config file support
`wget --no-check-certificate --quiet --output-document /root/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x /home/pi/thermeq3/config_me.py`
and run it:
```
cd /home/pi/thermeq3
./config_me.py
```
Please answer questions and check final config file in JSON format vi `cat` or `vi`.

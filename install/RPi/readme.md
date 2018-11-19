# Installation on RPi

## Hardware installation
Please take a look at [wiki page](https://github.com/autopower/thermeq3/wiki/Setup-RPi-hardware).
## thermeq3 installation
This is very early alpha, please be very patient.
Please take a look at [wiki page](https://github.com/autopower/thermeq3/wiki/install-application).

## Get config file support
`wget --no-check-certificate --quiet --output-document /home/pi/thermeq3/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x /home/pi/thermeq3/config_me.py`
and run it:
```
cd /home/pi/thermeq3
./config_me.py
```
Please answer questions and check final config file in JSON format vi `cat` or `vi`.

## Diagnostics
Download diag.sh `wget --no-check-certificate --quiet --output-document /home/pi/thermeq3/diag.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/RPi/diag.sh; chmod +x /home/pi/thermeq3/diag.sh`

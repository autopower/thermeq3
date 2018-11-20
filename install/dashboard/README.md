# Dashboard for thermeq3
Simple dashboard for boiler actor device.
For complete thermeq3 readme, click [here](https://github.com/autopower/thermeq3/blob/master/README.md).

To install thermeq3 *alpha* dashboard please type commands below, be sure that you are running V252+ and while logged in as root

## Installation instructions Yún
* to get dashboard install script `wget --no-check-certificate --quiet -O /root/yun-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/yun-dash.sh;chmod +x /root/yun-dash.sh`
* to run script `/root/yun-dash.sh`

## Installation instructions RPi
* to get dashboard install script `wget --no-check-certificate --quiet -O /home/pi/rpi-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/rpi-dash.sh;chmod +x /root/rpi-dash.sh`
* to run script `/home/pi/rpi-dash.sh`

If script is not working, please update dashboard.py line `request = urllib2.Request("http://localhost:8180/" + str(url))` according to your setup, e.g.:
* RPi users to `request = urllib2.Request("http://localhost/" + str(url))`
* Yún users replace default port 8180 to port according to your uhttpd configuration `request = urllib2.Request("http://localhost:YOUR_PORT/" + str(url))`

### How to replace text in dashboard.py
`sed -i -e 's/localhost:8180/localhost/g' /PATH_TO_FILE/dashboard.py`

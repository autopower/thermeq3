# Dashboard for thermeq3
Simple dashboard for boiler actor device.
For complete thermeq3 readme, click [here](https://github.com/autopower/thermeq3/blob/master/README.md)

## Installation instructions
To install thermeq3 *alpha* dashboard please type this command, be sure that you are running V252+ and while logged in as root:
* `wget --no-check-certificate --quiet --output-document /root/install-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/install-dash.sh;chmod +x /root/install.sh`
* `cd /root;./install-dash.sh`
* if script is not working, please update dashboard.py line `request = urllib2.Request("http://localhost:8180/" + str(url))` according to your setup


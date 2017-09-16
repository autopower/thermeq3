# Alpha version

Not so very well tested version.
Just for test issues.

## Whats new?
* new config file format (json)
* auto convert old config file and rename old one
* send mail issues resolved
* code clean up
* win nt & rpi support
* lifetime valve ignore
* weather fixes

## How to get upgrade script
`wget --no-check-certificate --quiet --output-document /root/upgrade.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/alpha/upgrade.sh;chmod +x /root/upgrade.sh`
After download please run `/root/upgrade.sh`, script downloads new thermeq3 version and interactive config which will be run after succesfull download.

#!/bin/ash
echo "Downloading thermeq3 app"
wget --no-check-certificate --quiet --output-document /root/thermeq3-install/thermeq3.zip https://github.com/autopower/thermeq3/raw/master/install/alpha/thermeq3.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading thermeq3 app: $?"
	exit $?
fi
echo "Unzipping app"
unzip -q /root/thermeq3-install/thermeq3.zip -d /root/thermeq3
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi
echo "thermeq3 application succesfully upgraded."
echo "Downloading interactive config"
wget --no-check-certificate --quiet --output-document /root/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x /root/config_me.py
if [ $? -ne 0 ]; then
	echo "Error during downloading config app: $?"
	exit $?
fi
/root/config_me.py

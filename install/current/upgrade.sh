#!/bin/ash
echo Downloading thermeq3 app
wget --no-check-certificate --quiet --output-document /root/thermeq3-install/thermeq3.zip https://github.com/autopower/thermeq3/raw/master/install/current/thermeq3.zip
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
echo "thermeq3 succesfully upgraded."

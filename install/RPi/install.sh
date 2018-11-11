#!/bin/bash
if [ $# -lt 1 ]; then
	echo "Usage: install.sh <thermeq3 device name>"
	exit 1
fi

BASE_DIR=/home/pi/thermeq3
mkdir -p $BASE_DIR
mkdir -p $BASE_DIR/install

echo "Downloading thermeq3 app"
wget --no-check-certificate --quiet --output-document $BASE_DIR/install/thermeq3.zip https://github.com/autopower/thermeq3/raw/master/install/RPi/thermeq3.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading thermeq3 app: $?"
	exit $?
fi
mkdir $BASE_DIR/code
echo "Unzipping app"
unzip -q -o $BASE_DIR/install/thermeq3.zip -d $BASE_DIR/code
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi 

echo "Installing libraries"
echo "Updating apt-get and upgrading packages"
sudo apt-get update
sudo apt-get upgrade
PKG_OK=$(dpkg-query -W --showformat='${Status}\n' python-openssl|grep "install ok installed")
echo Checking for python-openssl: $PKG_OK
if [ "" == "$PKG_OK" ]; then
  echo "No python-openssl. Installing python-openssl"
  sudo apt-get --force-yes --yes install python-openssl
  if [ $? -ne 0 ]; then
	echo "Error during installing openssl library. Error: $?"
	exit $?
fi

DIR=$BASE_DIR/web
echo "Using $DIR as storage path."

sudo apt-get install apache2

echo "Creating apache configuration..."
sudo chown -R pi:www-data /var/www/html/
sudo chmod -R 770 /var/www/html/

echo "Creating directories and cgi scripts" 
mkdir -p $BASE_DIR/csv
cd $DIR/www

echo "Creating nsm.py compatibility file"
echo "#!/usr/bin/env python
import sys
sys.path.insert(0, \"$BASE_DIR/code/\")
execfile(\"$BASE_DIR/code/nsm.py\")
" > $BASE_DIR/nsm.py

echo "Installing scripts with $1 as device name and $BASE_DIR as target directory"
echo "tail -n 50 $DIR/$1.log" > $BASE_DIR/ct
echo "cat $DIR/$1_error.log" > $BASE_DIR/err
echo "ps|grep python" > $BASE_DIR/psg
echo "ps -ef | grep nsm.py | grep -v grep | awk '{print $1}' | xargs kill -9" > $BASE_DIR/killnsm
chmod +x $BASE_DIR/ct
chmod +x $BASE_DIR/err
chmod +x $BASE_DIR/psg
chmod +x $BASE_DIR/killnsm

echo "Downloading interactive config"
wget --no-check-certificate --quiet --output-document $BASE_DIR/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x $BASE_DIR/config_me.py
if [ $? -ne 0 ]; then
	echo "Error during downloading config app: $?"
	exit $?
fi

read -p "Install dahsboard? [y/n]" yn
echo "Downloading dashboard install script"
case $yn in
	[Yy]*)
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' apache2|grep "install ok installed")
    echo Checking for apache2: $PKG_OK
    if [ "" == "$PKG_OK" ]; then
      echo "No apache2. Installing apache2"
      sudo apt-get --force-yes --yes install apache2
      if [ $? -ne 0 ]; then
    	echo "Error during installing apache2 package. Error: $?"
    	exit $?
    fi
    wget --no-check-certificate --quiet --output-document $BASE_DIR/install-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/RPi/install-dash.sh;chmod +x $BASE_DIR/install-dash.sh 
    if [ $? -ne 0 ]; then
    	echo "Error during downloading dashboard install script: $?"
    	exit $?
    fi
    echo "Dashboard install..."
    $BASE_DIR/install-dash.sh
    ;; 
esac
echo "Interactive config..."
$BASE_DIR/config_me.py
if [ -d $BASE_DIR/location.json ]; then
	mv $BASE_DIR/location.json /var/www/html/location.json
else
	echo "Can't find file. Please make location.json file for dashboard!"
fi

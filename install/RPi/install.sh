#!/bin/bash
if [ $# -lt 1 ]; then
	echo "Usage: install.sh <thermeq3 device name>"
	exit 1
fi

BASE_DIR=/home/pi/thermeq3
mkdir $BASE_DIR

mkdir $BASE_DIR/install
echo Downloading thermeq3 app
wget --no-check-certificate --quiet --output-document $BASE_DIR/install/thermeq3.zip https://github.com/autopower/thermeq3/raw/master/install/RPi/thermeq3.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading thermeq3 app: $?"
	exit $?
fi
mkdir $BASE_DIR/code
echo "Unzipping app"
unzip -q $BASE_DIR/install/thermeq3.zip -d $BASE_DIR/code
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi 

echo "Installing libraries"
sudo apt-get install python-openssl
if [ $? -ne 0 ]; then
	echo "Error during installing openssl library. Error: $?"
	exit $?
fi

DIR=$BASE_DIR/web
echo "Using $DIR as storage path."

if ! grep -q "0.0.0.0:8180" /etc/config/uhttpd; then
	echo "Backing up uhttpd configuration..."
	mkdir /root/backup
	cp /etc/config/uhttpd /root/backup/uhttpd.old
	echo "Modifying uhttpd configuration..."
	echo "config uhttpd secondary
	        list listen_http        0.0.0.0:8180
	        option home             $DIR/www
	        option cgi_prefix		/cgi-bin
	        option max_requests     2
	        option script_timeout   10
	        option network_timeout  10
	        option tcp_keepalive    1
	" >> /etc/config/uhttpd
	echo "Restarting uhttpd..."
	/etc/init.d/uhttpd restart
fi

echo "Creating directories and cgi scripts" 
mkdir -p $DIR/www
cd $DIR/www
mkdir -p $DIR/csv
cd $DIR/www
mkdir -p cgi-bin
cd cgi-bin

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
wget --no-check-certificate --quiet --output-document $BASE_DIR/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x /root/config_me.py
if [ $? -ne 0 ]; then
	echo "Error during downloading config app: $?"
	exit $?
fi
echo "Downloading dashboard install script"
wget --no-check-certificate --quiet --output-document $BASE_DIR/install-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/install-dash.sh;chmod +x /root/install-dash.sh
if [ $? -ne 0 ]; then
	echo "Error during downloading dashboard install script: $?"
	exit $?
fi
echo "Dashboard install..."
$BASE_DIR/install-dash.sh
echo "Interactive config..."
$BASE_DIR/config_me.py
if [ -d $BASE_DIR/location.json]; then
	mv $BASE_DIR/location.json $DIR/www/location.json
else
	echo "Can't find file. Please make location.json file for dashboard!"
fi

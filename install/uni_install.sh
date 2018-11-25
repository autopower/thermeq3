#!/bin/sh
echo "thermeq3 install for Yún/RPi"
echo ""
if [ $# -lt 1 ]; then
  read -p "Install with default name thermeq3? [y/n]" yn
  case $yn in
    [Nn]* )
      echo "Usage: uni_install.sh [thermeq3 device name] [alpha]"
      exit 1   
     ;; 
  esac
  DEV_NAME="thermeq3"
else
  DEV_NAME=$1	
fi

GITHUB_BASE=https://github.com/autopower/thermeq3/raw/master/install/current/
if [ $2 -eq "alpha" ]; then
  read -p "Do you really want upgrade to latest (unstable) alpha? [y/n]" yn
  case $yn in
    [Yy]* )
      GITHUB_BASE=https://github.com/autopower/thermeq3/raw/master/install/alpha/   
     ;;
  esac
fi

PLATFORM=$(uname -m)
case "$PLATFORM" in
  *"arm"*)
    echo "RPi installer will be used"
    PLATFORM="rpi"
    BASE_DIR=/home/pi/thermeq3
    INSTALL_DIR=/home/pi/thermeq3
    WWW_DIR=/var/www/html
    ;;
  *"mips"*)
    echo "Yún installer will be used"
    PLATFORM="yun"
    BASE_DIR=/root/thermeq3
    if [ -d /mnt/sda1 ]; then
	   INSTALL_DIR=/mnt/sda1
    else
	   if [ -d /mnt/sdb1 ]; then
      INSTALL_DIR=/mnt/sdb1
	   else
		  echo "Please mount USB or SD card!"
		  exit 1
	   fi
    fi
    WWW_DIR=$INSTALL_DIR/www
    ;;
  *)
   echo "Unknown platform: $PLATFORM"
   exit 2
   ;;
esac

echo " - using $BASE_DIR as base directory"
echo " - using $INSTALL_DIR as install directory"

mkdir -p $BASE_DIR
mkdir -p $INSTALL_DIR/install
mkdir -p $BASE_DIR/support

echo ""
echo "Installing support"
case "$PLATFORM" in
  "rpi" )
    echo " - updating apt-get and upgrading packages"
    sudo apt-get update
    sudo apt-get upgrade
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' python-openssl|grep "install ok installed")
    echo Checking for python-openssl: $PKG_OK
    if [ "" == "$PKG_OK" ]; then
      echo " - no python-openssl. Installing python-openssl"
      sudo apt-get --force-yes --yes install python-openssl
      if [ $? -ne 0 ]; then
    	 echo "Error during installing openssl library. Error: $?"
      fi
    	exit $?
    fi
    ;;
  "yun" )
    echo " - updating opkg"
    opkg update --verbosity=0
    if [ $? -ne 0 ]; then
    	echo "Error during opkg update: $?"
    	exit $?
    fi
    echo " - installing unzip"
    opkg install unzip --verbosity=0
    if [ $? -ne 0 ]; then
    	echo "Error during installing unzip. Error: $?"
    	exit $?
    fi
    echo " - installing openssl libraries"
    opkg install python-openssl --verbosity=0
    if [ $? -ne 0 ]; then
    	echo "Error during installing openssl library. Error: $?"
    	exit $?
    fi
    ;;
esac

echo ""
echo "Installing thermeq3"
echo " - downloading thermeq3 app"
wget --no-check-certificate --quiet -O $INSTALL_DIR/install/thermeq3.zip $GITHUB_BASE/thermeq3.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading thermeq3 app: $?"
	exit $?
fi

mkdir -p $BASE_DIR/code
echo " - extracting thermeq3 app"
unzip -q -o $INSTALL_DIR/install/thermeq3.zip -d $BASE_DIR/code
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi 

echo " - creating nsm.py compatibility file"
echo "#!/usr/bin/env python
import sys
sys.path.insert(0, \"$BASE_DIR/code/\")
execfile(\"$BASE_DIR/code/nsm.py\")
" > $BASE_DIR/nsm.py

case "$PLATFORM" in
  "rpi" )
    echo " - creating systemd files"
    echo "[Unit]
    Description=thermeq3 Service
    After=multi-user.target
    
    [Service]
    Type=idle
    ExecStart=/usr/bin/python /home/pi/thermeq3/nsm.py
    
    [Install]
    WantedBy=multi-user.target" > /home/pi/thermeq3/tmp/thermeq3.service
    sudo mv /home/pi/thermeq3/tmp/thermeq3.service /lib/systemd/system/thermeq3.service
    sudo chmod 644 /lib/systemd/system/thermeq3.service
    sudo systemctl daemon-reload
    sudo systemctl enable thermeq3.service
    ;;
  "yun" )
    echo " - please upload yun sketch via Arduino IDE"
    ;;
esac

echo " - installing shell scripts with $DEV_NAME as device name"
echo "tail -n 50 $INSTALL_DIR/$DEV_NAME.log" > $BASE_DIR/ct
echo "cat $INSTALL_DIR/$1_error.log" > $BASE_DIR/err
echo "ps|grep python" > $BASE_DIR/psg
echo "ps -ef | grep nsm.py | grep -v grep | awk '{print $1}' | xargs kill -9" > $BASE_DIR/killnsm
echo "cat $BASE_DIR/$DEV_NAME.log.* | grep summary | awk '{print $1 "," $8}' | sort > $WWW_DIR/temp.csv
sort -u $WWW_DIR/temp.csv $WWW_DIR/dailysummary.csv > $WWW_DIR/result.csv
rm $WWW_DIR/temp.csv $WWW_DIR/dailysummary.csv
mv $WWW_DIR/result.csv $WWW_DIR/dailysummary.csv" > $BASEDIR/support/dailysum
chmod +x $BASE_DIR/ct
chmod +x $BASE_DIR/err
chmod +x $BASE_DIR/psg
chmod +x $BASE_DIR/killnsm
chmod +x $BASE_DIR/support/dailysum

echo " - creating folders:"
case "$PLATFORM" in
  "rpi" )
    echo "   - for CSV files" 
    mkdir -p $BASE_DIR/csv
    ;;
  "yun" )
    echo "   - for CSV files"
    mkdir -p $INSTALL_DIR/csv
    echo "   - for HTML files" 
    mkdir -p $INSTALL_DIR/www
    echo "   - for CGI-BIN files"
    mkdir -p $INSTALL_DIR/www/cgi-bin  
esac

 
echo " - downloading interactive config"
wget --no-check-certificate --quiet -O $BASE_DIR/config_me.py https://raw.githubusercontent.com/autopower/thermeq3/master/install/current/config_me.py;chmod +x $BASE_DIR/config_me.py
if [ $? -ne 0 ]; then
	echo "Error during downloading config app: $?"
	exit $?
fi

echo ""
read -p "Install dashboard? [y/n]" yn
case $yn in
	[Yy]*)
    echo " - downloading dashboard install script"
    case "$PLATFORM" in
      "rpi" )
        wget --no-check-certificate --quiet -O $BASE_DIR/install-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/rpi-dash.sh;chmod +x $BASE_DIR/install-dash.sh
        ;;
       "yun" )           
        wget --no-check-certificate --quiet -O $BASE_DIR/install-dash.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/dashboard/yun-dash.sh;chmod +x $BASE_DIR/install-dash.sh
        ;;
    esac
    if [ $? -ne 0 ]; then
    	echo "Error during downloading dashboard install script: $?"
	   exit $?
    fi    
    echo " - running dashboard install script"
    $BASE_DIR/install-dash.sh 
    ;;
esac

echo ""
read -p "Run interactive config? [y/n]" yn
case $yn in
	[Yy]*)
    $BASE_DIR/config_me.py
    if [ -f $BASE_DIR/location.json ]; then
      echo "Moving file..."
      case "$PLATFORM" in
        "rpi" )
          mv $BASE_DIR/location.json /var/www/html/location.json
          ;;
        "yun" )
          mv $BASE_DIR/location.json $INSTALL_DIR/www/location.json
          ;;
      esac	
    else
    	echo "Can't find file. Please make location.json file for dashboard!"
    fi
esac

echo ""
read -p "Delete install folder? [y/n]" yn
case $yn in
	[Yy]*)
    echo "Removing install folder..."
    rm -rf $INSTALL_DIR/install/*
    rmdir $INSTALL_DIR/install
    ;;
esac

case "$PLATFORM" in
  "rpi" )
    echo "Please check apache¾ configuration!"
    ;;
  "yun" )
    echo "Please upload yun sketch via Arduino IDE!"
    ;;
esac

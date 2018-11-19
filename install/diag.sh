#!/bin/sh
if [ $# -lt 1 ]; then
	echo "Usage: diag.sh <max!cube ip address>"
	echo "diag.sh 192.168.0.222"
	exit 1
fi

PLATFORM=$(uname -m)
case "$PLATFORM" in
  *"arm"*)
    echo "RPi diag will be used"
    PLATFORM="rpi"
    BASE_DIR=/home/pi/thermeq3
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' telnet|grep "install ok installed")
    echo Checking for telnet: $PKG_OK
    if [ "" == "$PKG_OK" ]; then
      echo "No telnet. Installing telnet"
      sudo apt-get --yes install telnet
    fi
    ;;
  *"mips"*)
    echo "Yún diag will be used"
    PLATFORM="yun"
    BASE_DIR=/root
    ;;
  *)
   echo "Unknown platform: $PLATFORM"
   exit 2
   ;;
esac

DIAGFILE=$BASE_DIR/diag.txt

if [ -f $DIAGFILE ]; then
	echo "Previous $DIAGFILE exists! Appending to file."
fi
echo "--- Diag script ---------" >> $DIAGFILE
date >> $DIAGFILE
echo "--- Mount directory ---------" >> $DIAGFILE
ls -al /mnt >> $DIAGFILE 
echo "--- Mount point ---------" >> $DIAGFILE
mount >> $DIAGFILE
echo "--- i/f config ---------" >> $DIAGFILE
ifconfig >> $DIAGFILE
echo "--- Ping ---------" >> $DIAGFILE
ping $1 -c 4 >> $DIAGFILE
echo "--- Telnet to MAX!Cube ---------" >> $DIAGFILE
sleep 3 | telnet $1 62910 >> $DIAGFILE
read -p "Include thermeq3.json file? WARNING: file may contains user credentials to email service! [y/n]" yn
case $yn in
	[Yy]* )
    echo "--- thermeq3.json ---------" >> $DIAGFILE
    cat $BASE_DIR/thermeq3.json >> $DIAGFILE
    ;; 
esac
echo "Please post diag.txt to autopowerdevice@gmail.com"
#!/bin/bash
if [ $# -lt 1 ]; then
	echo "Usage: diag.sh <max!cube ip address>"
	echo "diag.sh 192.168.0.222"
	exit 1
fi

DIAGFILE=/home/pi/thermeq3/diag.txt

PKG_OK=$(dpkg-query -W --showformat='${Status}\n' telnet|grep "install ok installed")
echo Checking for telnet: $PKG_OK
if [ "" == "$PKG_OK" ]; then
  echo "No telnet. Installing telnet"
  sudo apt-get --yes install telnet
fi

if [ -f /home/pi/thermeq3/diag.txt ]; then
	echo "Previous diag.txt exists! Appending to file."
fi
echo "--- Diag script ---------" >> $DIAGFILE
date >> $DIAGFILE
echo "df..."
echo "--- Diskfree ---------" >> $DIAGFILE
df -h >> $DIAGFILE
echo "mount..." 
echo "--- Mount point ---------" >> $DIAGFILE
mount >> $DIAGFILE
echo "ifconfig..."
echo "--- i/f config ---------" >> $DIAGFILE
ifconfig >> $DIAGFILE
echo "ping..."
echo "--- Ping ---------" >> $DIAGFILE
ping $1 -c 4 >> $DIAGFILE
echo "telnet..."
echo "--- Telnet to MAX!Cube ---------" >> $DIAGFILE
sleep 3 | telnet $1 62910 >> $DIAGFILE
read -p "Include thermeq3.json file? WARNING: file may contains user credentials to email service! [y/n]" yn
case $yn in
	[Yy]* )
    echo "--- thermeq3.json ---------" >> $DIAGFILE
    cat /home/pi/thermeq3/thermeq3.json >> $DIAGFILE
    ;; 
esac
echo "Please post diag.txt to autopowerdevice@gmail.com"
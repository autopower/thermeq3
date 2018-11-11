#!/bin/bash
if [ $# -lt 1 ]; then
	echo "Usage: diag.sh <max!cube ip address>"
	echo "diag.sh 192.168.0.222"
	exit 1
fi

PKG_OK=$(dpkg-query -W --showformat='${Status}\n' telnet|grep "install ok installed")
echo Checking for telnet: $PKG_OK
if [ "" == "$PKG_OK" ]; then
  echo "No telnet. Installing telnet"
  sudo apt-get --force-yes --yes install telnet
fi

if [ -f /home/pi/thermeq3/diag.txt ]; then
	echo "Previous diag.txt exists! Appending to file."
fi
echo "--- Diag script ---------" >> /home/pi/thermeq3/diag.txt
date >> /home/pi/thermeq3/diag.txt
echo "--- Mount directory ---------" >> /home/pi/thermeq3/diag.txt
ls -al /mnt >> /home/pi/thermeq3/diag.txt 
echo "--- Mount point ---------" >> /home/pi/thermeq3/diag.txt
mount >> /home/pi/thermeq3/diag.txt
echo "--- i/f config ---------" >> /home/pi/thermeq3/diag.txt
ifconfig >> /home/pi/thermeq3/diag.txt
echo "--- Ping ---------" >> /home/pi/thermeq3/diag.txt
ping $1 -c 4 >> /home/pi/thermeq3/diag.txt
echo "--- Telnet to MAX!Cube ---------" >> /home/pi/thermeq3/diag.txt
sleep 3 | telnet $1 62910 >> /home/pi/thermeq3/diag.txt
read -p "Include thermeq3.json file? WARNING: file may contains user credentials to email service! [y/n]" yn
case $yn in
	[Yy]* ) echo "--- thermeq3.json ---------" >> /home/pi/thermeq3/diag.txt; cat /home/pi/thermeq3/thermeq3.json >> /home/pi/thermeq3/diag.txt; 
esac
echo "Please post diag.txt to autopowerdevice@gmail.com"
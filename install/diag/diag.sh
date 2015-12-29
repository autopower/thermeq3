#!/bin/ash
if [ $# -lt 1 ]; then
	echo "Usage: diag.sh <max!cube ip address>"
	echo "diag.sh 192.168.0.222"
	exit 1
fi

if [ -f /root/diag.txt ]; then
	echo "Previous diag.txt exists! Appending to file."
fi
echo "--- Diag script ---------" >> /root/diag.txt
date >> /root/diag.txt
echo "--- Mount directory ---------" >> /root/diag.txt
ls -al /mnt >> /root/diag.txt 
echo "--- Mount point ---------" >> /root/diag.txt
mount >> /root/diag.txt
echo "--- i/f config ---------" >> /root/diag.txt
ifconfig >> /root/diag.txt
echo "--- Ping ---------" >> /root/diag.txt
ping $1 -c 4 >> /root/diag.txt
echo "--- Telnet to MAX!Cube ---------" >> /root/diag.txt
sleep 3 | telnet $1 62910 >> /root/diag.txt
read -p "Include config.py file? WARNING: config.py file may contains user credentials to email service! [y/n]" yn
case $yn in
	[Yy]* ) echo "--- config.py ---------" >> /root/diag.txt; cat /root/config.py >> /root/diag.txt
esac
echo "Please post diag.txt to autopowerdevice@gmail.com"
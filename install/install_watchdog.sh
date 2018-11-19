#!/bin/ash
if [ $# -lt 1 ]; then
	echo "Usage: install_watch.sh <thermeq3 device name>"
	exit 1
fi

if [ -d /mnt/sda1 ]; then
	DIR=/mnt/sda1
else
	if [ -d /mnt/sdb1 ]; then
		DIR=/mnt/sdb1
	else
		echo "Please mount USB or SD card!"
		exit 1
	fi
fi
echo "Using $DIR as storage path."

echo "#!/bin/ash
if [ $(( (`date +%s` - `date -r $DIR/$1.bridge +%s`) > (5 * 60) )) -eq 1 ]; then
  ps -ef | grep nsm.py | grep -v grep | awk '{print }' | xargs kill -9
fi" > /root/watch_bridge
chmod +x watch_bridge

if ! grep -q "/root/watch_bridge" /etc/crontab; then
  echo "*/5 * * * * /root/watch_bridge" >> /etc/crontab
fi

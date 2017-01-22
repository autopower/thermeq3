#!/bin/ash
echo Downloading dashboard...
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
echo "Using $DIR/www/cgi-bin as cgi-bin path."

wget --no-check-certificate --quiet --output-document $DIR/www/cgi-bin/dashboard.py https://github.com/autopower/thermeq3/raw/master/install/dashboard/dashboard.py
if [ $? -ne 0 ]; then
	echo "Error during downloading dahsboard: $?"
	exit $?
fi

cd $DIR
cd www/cgi-bin

echo "#!/bin/sh
/usr/bin/env python $DIR/www/cgi-bin/dashboard.py" > dash
chmod +x dash

if ! grep -q "0.0.0.0:8180" /etc/config/uhttpd; then
	echo "Wrong uhttpd configuration..."
	exit 1
fi
echo "Dashboard succesfully installed. Before browsing to http://arduino.ip:8180/cgi-bin/dash please edit credentials in dashboard.py file"

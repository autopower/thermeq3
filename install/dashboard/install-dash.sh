#!/bin/ash
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
cd $DIR
cd www/cgi-bin

echo "Downloading bootstrap"
wget --no-check-certificate --quiet --output-document $DIR/www/bootstrap.zip https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
echo "Unzipping bootstrap"
unzip $DIR/www/bootstrap.zip -d $DIR/www/
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi
echo "Moving bootstrap..."
cp -R $DIR/www/bootstrap-3.3.7-dist/* $DIR/www/
rm -rf $DIR/www/bootstrap-3.3.7-dist/
rm -rf $DIR/www/bootstrap.zip

echo "Downloading dashboard..."
wget --no-check-certificate --quiet --output-document $DIR/www/cgi-bin/dashboard.py https://github.com/autopower/thermeq3/raw/master/install/dashboard/dashboard.py
if [ $? -ne 0 ]; then
	echo "Error during downloading dahsboard: $?"
	exit $?
fi

echo "#!/bin/sh
/usr/bin/env python $DIR/www/cgi-bin/dashboard.py" > dash
chmod +x dash

if ! grep -q "0.0.0.0:8180" /etc/config/uhttpd; then
	echo "Wrong uhttpd configuration..."
	exit 1
fi
echo "Dashboard succesfully installed. Before browsing to http://arduino.ip:8180/cgi-bin/dash please edit credentials in dashboard.py file"

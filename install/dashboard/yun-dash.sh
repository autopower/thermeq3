#!/bin/sh
echo "thermeq3 dashboard install for yún"
echo ""
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
echo "Using $INSTALL_DIR/www/cgi-bin as cgi-bin path."

echo "Installing bootstrap"
echo " - downloading bootstrap"
wget --no-check-certificate --quiet -O $INSTALL_DIR/www/bootstrap.zip https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
echo " - unzipping bootstrap"
unzip $INSTALL_DIR/www/bootstrap.zip -d $INSTALL_DIR/www/
if [ $? -ne 0 ]; then
	echo "Error during unzipping bootstrap package: $?"
	exit $?
fi
echo " - moving bootstrap"
cp -R $INSTALL_DIR/www/bootstrap-3.3.7-dist/* $INSTALL_DIR/www/
echo " - removing zip file"
rm -rf $INSTALL_DIR/www/bootstrap-3.3.7-dist/
rm -rf $INSTALL_DIR/www/bootstrap.zip

echo ""
echo "Downloading dashboard..."
wget --no-check-certificate --quiet -O $INSTALL_DIR/www/cgi-bin/dashboard.py https://github.com/autopower/thermeq3/raw/master/install/dashboard/dashboard.py
if [ $? -ne 0 ]; then
	echo "Error during downloading dahsboard: $?"
	exit $?
fi

echo "Creating dash file"
echo "#!/bin/sh
/usr/bin/env python $INSTALL_DIR/www/cgi-bin/dashboard.py" > $INSTALL_DIR/www/cgi-bin/dash
chmod +x dash

if ! grep -q "0.0.0.0:8180" /etc/config/uhttpd; then
	echo "Wrong uhttpd configuration. Please check /etc/config/uhttpd!"
	exit 1
fi
echo "Dashboard succesfully installed. Before browsing to http://arduino.ip:8180/cgi-bin/dash please edit credentials in dashboard.py file"

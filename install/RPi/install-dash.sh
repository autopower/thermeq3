#!/bin/bash
DIR=/var/www/html
CGIDIR=/usr/lib/cgi-bin
echo "Using $CGIDIR as cgi-bin path."
cd $DIR

echo "Downloading bootstrap"
wget --no-check-certificate --quiet --output-document $DIR/bootstrap.zip https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
echo "Unzipping bootstrap"
unzip $DIR/bootstrap.zip -d $DIR/
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi
echo "Moving bootstrap..."
cp -R $DIR/bootstrap-3.3.7-dist/* $DIR/
rm -rf $DIR/bootstrap-3.3.7-dist/
rm -rf $DIR/bootstrap.zip

echo "Downloading dashboard..."
sudo wget --no-check-certificate --quiet --output-document $CGIDIR/dashboard.py https://github.com/autopower/thermeq3/raw/master/install/dashboard/dashboard.py
if [ $? -ne 0 ]; then
	echo "Error during downloading dashboard: $?"
	exit $?
fi

echo "Creating dash file"
echo "#!/bin/sh
/usr/bin/env python $CGIDIR/dashboard.py" > ~/dash
sudo chmod +x ~/dash
sudo mv ~/dash $CGIDIR/dash

echo "Dashboard succesfully installed. Before browsing to http://rpi.ip/cgi-bin/dash please edit credentials in dashboard.py file"

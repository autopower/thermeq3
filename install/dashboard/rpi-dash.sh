#!/bin/sh
echo "thermeq3 dashboard install for Rpi"
echo ""
WWWDIR=/var/www/html
CGIDIR=/usr/lib/cgi-bin
BASE_DIR=/home/pi/thermeq3

echo "Using $WWWDIR as base for html files"
echo "Using $CGIDIR as cgi-bin path"

PKG_OK=$(dpkg-query -W --showformat='${Status}\n' apache2|grep "install ok installed")
echo "Checking for apache2: $PKG_OK"
if [ "" == "$PKG_OK" ]; then
  echo "No apache2. Installing apache2"
  sudo apt-get --force-yes --yes install apache2
  if [ $? -ne 0 ]; then
	 echo "Error during installing apache2 package. Error: $?"
	 exit $?
  fi
fi

echo "Creating apache configuration..."
sudo chown -R pi:www-data /var/www/html/
sudo chmod -R 770 /var/www/html/
sudo a2enmod cgi 
sudo service apache2 restart
 
echo ""
echo "Installing bootstrap"
echo " - downloading bootstrap"
wget --no-check-certificate --quiet --output-document $WWWDIR/bootstrap.zip https://github.com/twbs/bootstrap/releases/download/v3.3.7/bootstrap-3.3.7-dist.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading dashboard: $?"
	exit $?
fi

echo " - unzipping bootstrap"
unzip -q $WWWDIR/bootstrap.zip -d $WWWDIR/
if [ $? -ne 0 ]; then
	echo "Error during unzipping dashboard: $?"
	exit $?
fi

echo " - moving bootstrap..."
cp -R $WWWDIR/bootstrap-3.3.7-dist/* $WWWDIR/
echo " - removing zip file"
rm -rf $WWWDIR/bootstrap-3.3.7-dist/
rm -rf $WWWDIR/bootstrap.zip

echo ""
echo "Downloading dashboard..."
sudo wget --no-check-certificate --quiet --output-document $CGIDIR/dashboard.py https://github.com/autopower/thermeq3/raw/master/install/dashboard/dashboard.py
if [ $? -ne 0 ]; then
	echo "Error during downloading dashboard: $?"
	exit $?
fi

echo "Creating dash file"
echo "#!/bin/sh
/usr/bin/env python $CGIDIR/dashboard.py" > ~/dash
echo " - chmod +x"
sudo chmod +x ~/dash
echo " - move file"
sudo mv ~/dash $CGIDIR/dash.sh
echo " - replace ip:port string"
sudo sed -i -e 's/localhost:8180/localhost/g' /usr/lib/cgi-bin/dashboard.py

echo "Modyfying apache config files"
echo ""
if ! grep -Fq 'AddHandler cgi-script .sh' /etc/apache2/conf-available/serve-cgi-bin.conf ; then
  echo " - add .sh handler in cgi-bin"
  sudo sed -i '/<Directory "\/usr\/lib\/cgi-bin">/a AddHandler cgi-script .sh' /etc/apache2/conf-available/serve-cgi-bin.conf
fi
if ! grep -Fq '#Include conf-available\/serve-cgi-bin.conf' /etc/apache2/sites-available/000-default.conf ; then
  echo " - include serve cgi-bin config file"
  sudo sed -i 's/#Include conf-available\/serve-cgi-bin.conf/Include conf-available\/serve-cgi-bin.conf/g' /etc/apache2/sites-available/000-default.conf
fi
echo "Dashboard succesfully installed."

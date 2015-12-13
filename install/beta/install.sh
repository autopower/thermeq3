#!/bin/ash
if [ $# -lt 1 ]; then
	echo "Usage: install.sh <thermeq3 device name>"
	exit 1
fi

echo "Preparing..."
echo "opkg update"
opkg update --verbosity=0
if [ $? -ne 0 ]; then
	echo "Error during opkg update: $?"
	exit $?
fi

echo "Installing zip"
opkg install unzip --verbosity=0
if [ $? -ne 0 ]; then
	echo "Error during installing unzip. Error: $?"
	exit $?
fi

mkdir /root/thermeq3-install
echo Downloading thermeq3 app
wget --no-check-certificate --quiet --output-document /root/thermeq3-install/thermeq3.zip https://github.com/autopower/thermeq3/raw/master/install/beta/thermeq3.zip
if [ $? -ne 0 ]; then
	echo "Error during downloading thermeq3 app: $?"
	exit $?
fi
mkdir /root/thermeq3
echo "Unzipping app"
unzip -q /root/thermeq3-install/thermeq3.zip -d /root/thermeq3
if [ $? -ne 0 ]; then
	echo "Error during unzipping thermeq3 app: $?"
	exit $?
fi 

echo "Installing libraries"
opkg install python-openssl --verbosity=0
if [ $? -ne 0 ]; then
	echo "Error during installing openssl library. Error: $?"
	exit $?
fi
opkg install python-expat --verbosity=0 
if [ $? -ne 0 ]; then
	echo "Error during installing expat library. Error: $?"
	exit $?
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

if ! grep -q "0.0.0.0:8180" /etc/config/uhttpd; then
	echo "Backing up uhttpd configuration..."
	mkdir /root/backup
	cp /etc/config/uhttpd /root/backup/uhttpd.old
	echo "Modifying uhttpd configuration..."
	echo "config uhttpd secondary
	        list listen_http        0.0.0.0:8180
	        option home             $DIR/www
	        option cgi_prefix		/cgi-bin
	        option max_requests     2
	        option script_timeout   10
	        option network_timeout  10
	        option tcp_keepalive    1
	" >> /etc/config/uhttpd
	echo "Restarting uhttpd..."
	/etc/init.d/uhttpd restart
fi

echo "Creating directories and cgi scripts" 
mkdir -p $DIR/www
cd $DIR/www
mkdir -p cgi-bin
cd cgi-bin

echo "#!/bin/sh
	echo \"Content-type: application/json\"
	echo \"\"
	cat $DIR/www/status.xml" > status
echo "#!/bin/sh
	echo \"Content-type: application/json\"
	echo \"\"
	cat $DIR/www/owl.xml" > owl
echo "#!/bin/sh
	echo \"Content-type: text/html\"
	echo \"\"
	cat $DIR/www/nice.html" > nice
chmod +x status
chmod +x owl
chmod +x nice

echo "Installing scripts with $1 as device name and $DIR as target directory"
echo "tail -n 50 $DIR/$1.log" > /root/ct
echo "cat $DIR/$1_error.log" > /root/err
echo "ps|grep python" > /root/psg
chmod +x /root/ct
chmod +x /root/err
chmod +x /root/psg
 
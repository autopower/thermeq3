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
echo "Using $DIR as storage path."
echo "Recreating directories and cgi scripts" 
mkdir -p $DIR/www
cd $DIR/www
mkdir -p $DIR/csv
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
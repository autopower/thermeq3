#!/bin/ash
opkg update
if [ $? -ne 0 ]; then
	echo "Error during opkg update: $?"
	exit $?
fi
opkg install python-openssl
if [ $? -ne 0 ]; then
	echo "Error during installing openssl library. Error: $?"
	exit $?
fi
echo "Modyfying uhttp configuration"
mkdir /root/backup
mkdir /mnt/sda1/www
cp /etc/config/uhttpd /root/uhttpd.old
echo "config uhttpd secondary
        list listen_http        0.0.0.0:8180
        option home             /mnt/sda1/www
        option max_requests     2
        option script_timeout   10
        option network_timeout  10
        option tcp_keepalive    1
" >> /etc/config/uhttpd
echo "Restarting uhttpd"
/etc/init.r/uhttpd restart
echo "#!/bin/ash
if [ \$# -lt 2 ]; then
	echo \"Please run with thermeq3 name and path as arguments.\"
	echo \"Example:\"
	echo \"cs3 /mnt/sda1 boiler\"
else
	echo \"Using \$2 as thermeq3 name and \$1 as path\"
	echo \"tail -n 50 \$1/\$2.log\" > /root/ct
	echo \"cat \$1/\$2_error.log\" > /root/err
	echo \"ps|grep python\" > /root/psg
	chmod +x /root/ct
	chmod +x /root/err
	chmod +x /root/psg
	ln -s \$1 sdcard
fi
	" > /root/cs3.sh
chmod +x /root/cs3.sh
echo "Installing with $1 device name"
/root/cs3.sh /mnt/sda1 $1
 
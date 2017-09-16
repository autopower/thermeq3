# Diagnostics
If something goes wrong, please do some diagnostics and paste results to the issues.
Or run:
```
wget --no-check-certificate --quiet --output-document /root/diag.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/diag/diag.sh;chmod +x /root/diag.sh
```
If everything goes ok, run `./diag.sh <max!cube ip address>`, e.g. `./diag.sh 192.168.0.222`. And send me `/root/diag.txt`.


## Yun
Always [upgrade to latest yun firmware](https://www.arduino.cc/en/Tutorial/YunSysupgrade).
Perhaps update [bridge library](https://github.com/arduino/YunBridge/tree/master/bridge)
Check storage mount points `cd /mnt|ls -al`, is there any storage mounted (USB or SD card?). Is your card/USB key readable in your PC/Mac? Is FAT32/exfat formatted? 

## Network issues
From shell on yun please check if you have connection to MAX!Cube:
* ping your MAX!Cube: `ping <maxcube_ip_address> -c 4`
* telnet to MAX!Cube: `telnet <maxcube_ip_address> 62910`, 62910 is default port 
* save results from `ifconfig > /root/ifconfig.txt`

## Version
Please check log file for version you are using. Find line like this:
```
thermeq3 - INFO - --> V139 started with PID=1851 <--
```
It tells you, that you are using version 139.
You can always check latest version for:
* production, in [autoupdate file](https://github.com/autopower/thermeq3/blob/master/install/current/autoupdate.data)
* beta, in [autoupdate file](https://github.com/autopower/thermeq3/blob/master/install/beta/autoupdate.data)

First 3 chars denote version. 

## config.py file
Did you edit `config.py` file correctly? Check for common mistakes such:
* all values must be string, 
* no API key for openweather
* wrong woeid

## Log file, error log
Please check your error log (located in `/mnt/sda1` or `/mnt/sdb1` or `/root` directory, depends on version and file).
If you see information like this:
```
thermeq3 - ERROR - Traceback: Traceback (most recent call last):
  File "/root/nsm.py", line 796, in openMAX
    var.client_socket.connect((stp.max_ip, 62910))
  File "/usr/lib/python2.7/socket.py", line 224, in meth
    return getattr(self._sock,name)(*args)
error: [Errno 148] No route to host
```
Probably you have problem with MAX!Cube connection.

If you see error like this:
```
thermeq3 - ERROR - Traceback: Traceback (most recent call last):
  File "/root/nsm.py", line 382, in sendEmail
    server = smtplib.SMTP(stp.mailserver, stp.mailport)
  File "/usr/lib/python2.7/smtplib.py", line 249, in __init__
    (code, msg) = self.connect(host, port)
  File "/usr/lib/python2.7/smtplib.py", line 309, in connect
    self.sock = self._get_socket(host, port, self.timeout)
  File "/usr/lib/python2.7/smtplib.py", line 284, in _get_socket
    return socket.create_connection((port, host), timeout)
  File "/usr/lib/python2.7/socket.py", line 553, in create_connection
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
```
Probably you din't edit config.py file with correct mail server information/credentials.

## Everything installed correctly, but nothing happens
* did you upload sketch file (.ino)?
* if arduino starts blink 4x, then LED is on, blinks 4x again?
* if you login to linux part, `/root/psg` reports fully functional bridge (`python -d bridge`)?
* did you insert SD crad or USB key?
* is this storage correctly formated (fat32, extfs2/3/4)?

## Any problem or question
Keep asking! If you have any problem or issue, just ask on [facebook](https://www.facebook.com/autopow) or via [email](mailto:autopowerdevice@gmail.com).

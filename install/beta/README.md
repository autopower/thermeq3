#thermeq3
Boiler actor device for [ELV/EQ-3](http://www.eq-3.de/) [MAX! cube](http://www.eq-3.de/max-heizungssteuerung-produktdetail-kopie/items/bc-lgw-o-tw.html).
For complete readme, click [here](https://github.com/autopower/thermeq3/blob/master/README.md)

##Installation instructions
Plase check sketch (in fritzing) and setup [here](https://github.com/autopower/thermeq3/blob/master/README.md).
First you must upload sketch from yun-sketch to the yun. Then login to yun via ssh.
To install thermeq3 *beta* please type this command, while logged in:
```
wget --no-check-certificate --quiet --output-document /root/install.sh https://raw.githubusercontent.com/autopower/thermeq3/master/install/beta/install.sh|chmod +x /root/install.sh
```
And after that (you can change thermeq3 name to your own):
```
cd /root
./install.sh thermeq3
```
**Don't forget to edit config.py file!** Scroll down below [here](https://github.com/autopower/thermeq3/blob/master/README.md) for "In config.py file" chapter.


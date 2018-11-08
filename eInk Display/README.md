# eInk display for thermeq3
Simple device with eInk display based of ESP8266 and 2.7 eInk display.
This sketch using Waveshare [ESP8266 driver](https://www.waveshare.com/wiki/E-Paper_ESP8266_Driver_Board) and [2.7" display module](https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT_(B)).
Please download [library](https://www.waveshare.com/wiki/File:2.7inch_e-paper_hat_b_code.7z) for 2.7" display, edit pin definitions in `epdif.h`:
```
#define CS_PIN           15
#define RST_PIN          5
#define DC_PIN           4
#define BUSY_PIN         16
```
Finally you must edit sketch values for WiFi:
```
#define SSID_NAME "Your_SSID"
#define SSID_PWD "Your_key"
```
Code using deep sleep feature on ESP, so you must connect PIN16 and RST pin of ESP via 470ohm resitor, to correctly wake up.
And upload sketch to ESP via Arduino IDE.

thmermeq3 version must be 250+ and second website with bridge support must be installed, please check `http://ardu.ip:8180/bridge.json` if working.
 

# Thats all folks. Stay tuned :)

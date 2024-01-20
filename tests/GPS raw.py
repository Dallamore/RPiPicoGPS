from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C

import utime, time

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
print(gpsModule)

buff = bytearray(255)


    
    
while True:
    gpsModule.readline()
    buff = str(gpsModule.readline())
    parts = buff.split(',')
    
    if(parts[0] == "b'$GPGGA"):
          print(buff)
    if(parts[0] == "b'$GPZDA"):
          print(buff)       
       
    utime.sleep_ms(500)



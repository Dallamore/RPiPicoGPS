from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C

import utime, time

i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

oled.fill(1)
gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
print(gpsModule)

buff = bytearray(255)


def convertToDegree(RawDegrees):
    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)
    
    



while True:
#     print("GO")
    gpsModule.readline()
    buff = str(gpsModule.readline())
    parts = buff.split(',')
    time = ""
    GPSdate = ""
    
#     print(buff)
    
    if (parts[0] == "b'$GPRMC" and len(parts) > 9):
        if(parts[9]):
            GPSdate = "20" + parts[9][4:6] + "-" + parts[9][2:4] + "-" + parts[9][0:2]
    if(parts[0] == "b'$GPGGA"):
        time = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
        latitude = convertToDegree(parts[2])
        if (parts[3] == 'S'):
            latitude = '-'+latitude
        longitude = convertToDegree(parts[4])
        if (parts[5] == 'W'):
             longitude = '-'+longitude
        
        print(GPSdate + " " + time + " & " + latitude + " & " + longitude)

#     if(parts[0] == "b'$GPGGA"):
#           print(buff)
#     if(parts[0] == "b'$GPZDA"):
#           print(buff)       
       
    utime.sleep_ms(250)

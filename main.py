from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C

import utime, time

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)
led = Pin(25, Pin.OUT)

gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
print(gpsModule)

buff = bytearray(255)

TIMEOUT = False
FIX_STATUS = False

latitude = ""
longitude = ""
satellites = ""
GPStime = ""

def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, GPStime
    
    timeout = time.time() + 8 
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parts = buff.split(',')
    
        if (parts[0] == "b'$GPGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                
          #      print(buff)
                latitude = convertToDegree(parts[2])
                if (parts[3] == 'S'):
                    latitude = '-'+latitude
                longitude = convertToDegree(parts[4])
                if (parts[5] == 'W'):
                     longitude = '-'+longitude
                satellites = parts[7]
                GPStime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                FIX_STATUS = True
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        utime.sleep_ms(500)
        
def convertToDegree(RawDegrees):
    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)
    
oled.fill(0)
oled.text("Finding",0,10)
oled.text("satellites",0,20)
oled.show()   
while True:
    led.off()
    getGPS(gpsModule)

    if(FIX_STATUS == True):
        print("----------------------")
        print(str(buff, 'utf-8'))
        print("Latitude: "+latitude)
        print("Longitude: "+longitude)
        print("Satellites: " +satellites)
        print("Time: "+GPStime)
        
        
        oled.fill(0)
        oled.text("Lat: "+latitude, 0, 0)
        oled.text("Lng: "+longitude, 0, 10)
        oled.text("Satellites: "+satellites, 0, 20)
        oled.text("Time: "+GPStime, 0, 30)
        oled.show()
        
        FIX_STATUS = False
        led.on()
        ## turn on the led when writing to sd card, its a nice indicator
        time.sleep(0.5)
         
    if(TIMEOUT == True):
        print("----------------------")
        print("No GPS data is found.")
        #oled.fill(0)
        oled.text("No GPS data.", 0, 50)
        oled.show()
        TIMEOUT = False
        
        


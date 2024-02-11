from machine import Pin, UART, I2C, ADC
from ssd1306 import SSD1306_I2C
import os, sdcard
import time

##prepare oled display
i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

##prepare GPS module
gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
print(gpsModule)
buff = bytearray(255)

##prepare sd card
cs = machine.Pin(14, machine.Pin.OUT)
spi = machine.SPI(1,
    baudrate=1000000,
    polarity=0,
    phase=0,
    bits=8,
    firstbit=machine.SPI.MSB,
    sck=machine.Pin(10),
    mosi=machine.Pin(11),
    miso=machine.Pin(12))
sd = sdcard.SDCard(spi, cs)
os.mount(sd, '/sd')

##battery charge
vsys = ADC(29)                      # reads the system input voltage
charging = Pin(24, Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535
full_battery = 3.7                  # reference voltages for a full/empty battery, in volts
empty_battery = 2.0
 
 
led = Pin(25, Pin.OUT) 
 
TIMEOUT = False
FIX_STATUS = False

latitude = ""
longitude = ""
altitude = ""
satellites = ""
GPSdate = ""
GPStime = ""

def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, altitude, satellites,GPSdate, GPStime
    
    timeout = time.time() + 8 
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parts = buff.split(',')
         
        ##get the date
        if (parts[0] == "b'$GPRMC" and len(parts) > 9):
            if(parts[9]):
                GPSdate = parts[9]                   
        ##get time, lat, long, sats
        if (parts[0] == "b'$GPGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                latitude = convertToDegree(parts[2])
                if (parts[3] == 'S'):
                    latitude = '-'+latitude
                longitude = convertToDegree(parts[4])
                if (parts[5] == 'W'):
                     longitude = '-'+longitude
                satellites = parts[7]
                GPStime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                FIX_STATUS = True
                altitude = parts[9]
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        time.sleep(0.5)
        
def convertToDegree(RawDegrees):
    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)
    
 ##============ MAIN ====================================   
oled.fill(0)##show signs of life before main program starts
oled.hline(0,20,128,20)
oled.text("Waiting for GPS",2,30,1)
oled.hline(0,45,128,45)
oled.show()
while True:
    led.off()
    getGPS(gpsModule)

    if(FIX_STATUS == True):
        ##print to console
        print("----------------------")
#         print(str(buff, 'utf-8'))
#         print("Latitude: "+latitude)
#         print("Longitude: "+longitude)
#         print("Satellites: " +satellites)
#         print("Time: "+GPStime)
        
        ts = "TimeStamp=\"" + GPSdate + " " + GPStime + "\" "
        lat = "Lat=\"" + latitude + "\" "
        lon = "Lon=\"" + longitude + "\" "
        alt = "Alt=\"" + altitude + "\" "
        print(ts+lat+lon+alt)
        
        ##print to oled
        oled.fill(0)
        oled.text("Lat: "+latitude, 0, 0)
        oled.text("Lng: "+longitude, 0, 10)
        oled.text("Sats: "+satellites, 0, 20)
        oled.text("Time: "+GPStime, 0, 30)
        oled.show()
        
        ##save to sd card
        led.on()
        file = open('/sd/test.txt', 'a')
        file.write(ts+lat+lon+alt + "\r\n")
        file.close()
        
        ##signal end of GPS line
        FIX_STATUS = False
        
    if(TIMEOUT == True):
        print("----------------------")
        print("No GPS data is found.")
        #oled.fill(0)
        oled.text("No GPS data.", 0, 40)
        oled.show()
        TIMEOUT = False
    
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.read_u16() * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100
    oled.text("Batt: " + str(percentage) + "%",50,57,1)
    oled.show()
    
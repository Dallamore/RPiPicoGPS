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

sdCardReady = False
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
try:
    sd = sdcard.SDCard(spi, cs)
    os.mount(sd, '/sd')
    sdCardReady = True
    print("SD Card Ready")
except OSError:
    sdCardReady = False
    
##battery charge
vsys = ADC(29)                      # reads the system input voltage
charging = Pin(24, Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535
full_battery = 3.7                  # reference voltages for a full/empty battery, in volts
empty_battery = 2.0

StepTime = const(2)
FilterRatio = const(0.1)
LongRangeFilter = const(0.2)
avgLat = 0
avgLon = 0
# newAvg = ((1.0-FilterRatio) * previousAvg) + (filterRatio * newestGPSpoint)
 
led = Pin(25, Pin.OUT) 
 
TIMEOUT = False
FIX_STATUS = False

latitude = ""
longitude = ""
altitude = ""
satellites = ""
GPSdate = ""
GPStime = ""
GPStime_ns = ""
filePath = ""
fixCount = 0

def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, altitude, satellites, GPSdate, GPStime, GPStime_ns
    
    timeout = time.time() + StepTime
    while True:
        gpsModule.readline()
        buff = str(gpsModule.readline())
        parts = buff.split(',')
         
        ##get the date
        if (parts[0] == "b'$GPRMC" and len(parts) > 9):
            if(parts[9]):
                GPSdate = "20" + parts[9][4:6] + "-" + parts[9][2:4] + "-" + parts[9][0:2]
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
                GPStime_ns = parts[1][0:6]
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

def SetupNewFile():
    print("New file " + filePath)
    fileSetupStr =  "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n"
    fileSetupStr += "<gpx creator=\"Dallamore PicoGPS\" version=\"1.1\"\r\n"
    fileSetupStr += "  xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/11.xsd\"\r\n"
    fileSetupStr += "  xmlns:ns3=\"http://www.garmin.com/xmlschemas/TrackPointExtension/v1\"\r\n"
    fileSetupStr += "  xmlns=\"http://www.topografix.com/GPX/1/1\"\r\n"
    fileSetupStr += "  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:ns2=\"http://www.garmin.com/xmlschemas/GpxExtensions/v3\">\r\n"
    fileSetupStr += "  <metadata>\r\n"
    fileSetupStr += "    <link href=\"connect.garmin.com\">\r\n"
    fileSetupStr += "    <text>Dallamore PicoGPS</text>\r\n"
    fileSetupStr += "    </link>\r\n"
    fileSetupStr += "    <time>" + GPSdate + "T" + GPStime + ".000Z</time>\r\n"
    fileSetupStr += "  </metadata>\r\n"
    fileSetupStr += "  <trk>\r\n"
    fileSetupStr += "    <name>" + GPSdate + "T" + GPStime + "</name>\r\n"
    fileSetupStr += "    <type>walking</type>\r\n"
    fileSetupStr += "    <trkseg>\r\n"
    file = open(filePath, 'a')
    file.write(fileSetupStr)
    file.close()

def AddToFile():
    file = open(filePath, 'a')
    trackPoint  = "      <trkpt lat=\"" + latitude + "\" lon=\"" + longitude + "\">\r\n"
    trackPoint += "        <ele>" + altitude + "</ele>\r\n"
    trackPoint += "        <time>" + GPSdate + "T" + GPStime + ".000Z</time>\r\n"
    trackPoint += "      </trkpt>\r\n"
    file.write(trackPoint)
    file.close()
    print("Written to " + filePath)
    
def CompleteFiles():
    for entry in os.ilistdir("/sd"):
        # print(entry)
        if entry[1] == 0x8000:
            fn = entry[0]
            if fn.startswith("incomplete_") and fn.endswith(".gpx"):
                            
                fileEndStr  = "    </trkseg>\r\n"
                fileEndStr += "  </trk>\r\n"
                fileEndStr += "</gpx>" 
                
                file = open('/sd/' + fn, 'a')
                file.write(fileEndStr)
                file.close()
                
                newFn = fn[11:] #remove incomplete_ from filename
                
                os.rename('/sd/' + fn, '/sd/' + newFn)
                
                print(fn + " -> " + newFn + " Done")
    time.sleep(2)
    
def DisplayPower():
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.read_u16() * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if (percentage < 0.0 or percentage > 100.0):
        percentage = 100
    oled.text("Batt: " + str(percentage) + "%",45,57,1)
    oled.show()    
    
 ##============ MAIN ====================================
oled.fill(0)##show signs of life before main program starts
oled.text("Completing files",0,30,1)
oled.show()
if(sdCardReady):
    CompleteFiles()
    
oled.fill(0)##show signs of life before main program starts
oled.hline(0,20,128,20)
oled.text("Waiting for GPS",2,30,1)
oled.hline(0,45,128,45)
oled.show()
print("Staring main control loop")
while True:
    DisplayPower()
    led.off()
    if(sdCardReady):
        getGPS(gpsModule)
        if(FIX_STATUS == True):
            ##print GPS data to console
            print("----------------------")
            ts = "TimeStamp=\"" + GPSdate + " " + GPStime + "\" "
            lat = "Lat=\"" + latitude + "\" "
            lon = "Lon=\"" + longitude + "\" "
            alt = "Alt=\"" + altitude + "\" "
            print(ts+lat+lon+alt)
            
            
#             if(latitude):
#             avgLat = ((1.0-FilterRatio) * avgLat) + (filterRatio * latitude)
#             avgLon = ((1.0-FilterRatio) * avgLon) + (filterRatio * longitude)
            
            
#USE LONGRANGE FILTER TO GET RID OF THE BIGGEST MISTAKES, AND MOVING AVERAGE TO SMOOTH OUT SMALLER MISTAKES
#BOTH NEED A SEMI-ACCURATE AVERAGE AS BASE, HOW DO I ESTABLISH THIS BASE FIRST
            print(fixCount)
            avgLat = ((1.0-FilterRatio) * avgLat) + (FilterRatio * float(latitude))
            avgLon = ((1.0-FilterRatio) * avgLon) + (FilterRatio * float(longitude))
        
            
            ##print GPS data to oled
            oled.fill(0)
            oled.text("Time: "+ GPStime, 0, 0)
            oled.text("Lat: " + latitude, 0, 10)
            oled.text("Lng: " + longitude, 0, 20)
            oled.text("Sats: " + satellites, 0, 30)
            oled.show()
            
            ##save to sd card
            led.on()
            if (filePath == "" and GPSdate != ""):                
                filePath = "/sd/incomplete_" + GPSdate + GPStime_ns + ".gpx"
                SetupNewFile()
            else:
                if(filePath != ""):
                    AddToFile()
            
            ##signal end of GPS line
            FIX_STATUS = False
            if (fixCount < 10): #no point counting more than first 10
                fixCount += 1
                
            if(fixCount == 0):
                Print("No GPS yet")
                
            print('avglat: ' + str(avgLat) + ' avglon: ' + str(avgLon))            
            
        if(TIMEOUT == True and fixCount > 0):
            print("----------------------")
            print("No GPS data is found.")
            oled.text("No GPS data.", 0, 40)
            oled.show()
            TIMEOUT = False    
    else:
        oled.fill(0)
        oled.text("No SD Card",25,15,1)
        oled.text("Restart required",0,35,1)
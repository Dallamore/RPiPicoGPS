
from machine import Pin, UART, I2C
import utime
from ssd1306 import SSD1306_I2C
from micropyGPS import MicropyGPS

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)


# Initialize GPS module
gps_module = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
time_zone = -3
gps = MicropyGPS(time_zone)
 
def convert_coordinates(sections):
    if sections[0] == 0:  # sections[0] contains the degrees
        return None
 
    # sections[1] contains the minutes
    data = sections[0] + (sections[1] / 60.0)
 
    # sections[2] contains 'E', 'W', 'N', 'S'
    if sections[2] == 'S':
        data = -data
    if sections[2] == 'W':
        data = -data
 
    data = '{0:.6f}'.format(data)  # 6 decimal places
    return str(data)
 
 
while True:
    length = gps_module.any()
    if length > 0:
        data = gps_module.read(length)
        for byte in data:
            message = gps.update(chr(byte))
 
    latitude = convert_coordinates(gps.latitude)
    longitude = convert_coordinates(gps.longitude)
 
    if latitude is None or longitude is None:
        oled.fill(0)
        oled.text("Data unavailable", 0, 0)
        oled.text("No coordinates", 22, 40)
        oled.show()
        continue
 
    
    oled.fill(0)
    oled.text('Satellites: ' + str(gps.satellites_in_use), 10, 0)
    oled.text('Lat: ' + latitude, 0, 18)
    print('Lat: ' + latitude)
    oled.text('Lon: ' + longitude, 0, 36)
    print('Lon: ' + longitude)
 
    oled.show()
    utime.sleep(3)


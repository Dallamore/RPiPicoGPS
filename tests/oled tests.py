from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
import framebuf
import utime
WIDTH =128 
HEIGHT= 64
i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

oled.text("Batt: 100%",49,57,1)
oled.show()

# oled.hline(0,63,128,1)
# while True:
#     for i in range(0,64,8): # Draws a spike
#         oled.line(63,64-i,127-i,63,1)
#         oled.line(63,64-i,i,63,1)
#         oled.vline(63,64-i,i,1)
#         oled.hline(0,63,128,1)
#         oled.show()
#         time.sleep(0.06)
#         
#     for i in range(0,64,8): # Draws a spike
#         oled.line(63,64-i,127-i,63,0)
#         oled.line(63,64-i,i,63,0)
#         oled.vline(63,64-i,i,0)
#         oled.hline(0,63,128,1)
#         oled.show()
#         time.sleep(0.06)
#     
#     
# oled.show()
# time.sleep(delay)



# while True:
#     oled.vline(120,0,HEIGHT,1)
#     for i in range (WIDTH):
#         oled.scroll(-1,0)
#         oled.show()

# oled.vline(64,0,HEIGHT,1)
# oled.hline(0,32,WIDTH,1)
# oled.show()
# 
# oled.fill_rect(0, 0, 32, 32, 1)
# oled.fill_rect(2, 2, 28, 28, 0)
# oled.vline(9, 8, 22, 1)
# oled.vline(16, 2, 22, 1)
# oled.vline(23, 8, 22, 1)
# oled.fill_rect(26, 24, 2, 4, 1)
# oled.text('MicroPython', 40, 0, 1)
# oled.text('SSD1306', 40, 12, 1)
# oled.text('OLED 128x64', 40, 24, 1)
# oled.show()

# while True:
#     oled.fill(1)
#     oled.show()
#     time.sleep_ms(500)
# 
#     oled.fill(0)
#     oled.show()
#     time.sleep_ms(500)
# 
#     oled.fill(1)
#     oled.show()
#     time.sleep_ms(500)
# 
#     oled.fill(0)
#     oled.show()
#     time.sleep_ms(500)




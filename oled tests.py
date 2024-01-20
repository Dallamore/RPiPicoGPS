from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time
WIDTH =128 
HEIGHT= 64
i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# while True:
#     oled.vline(120,0,HEIGHT,1)
#     for i in range (WIDTH):
#         oled.scroll(-1,0)
#         oled.show()

oled.vline(64,0,HEIGHT,1)
oled.hline(0,32,WIDTH,1)
oled.show()
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




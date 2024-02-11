# This example reads the voltage from a LiPo battery connected to Pimoroni Pico LiPo
# and uses this reading to calculate how much charge is left in the battery.
# It then displays the info on the screen of Pico Display (or Pico Display 2.0).
# With Pimoroni Pico LiPo, you can read the battery percentage while it's charging.
# Save this code as main.py on your Pico if you want it to run automatically!

from machine import ADC, Pin
import time
# change to DISPLAY_PICO_DISPLAY_2 for Pico Display 2.0

vsys = ADC(29)                      # reads the system input voltage
charging = Pin(24, Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535

full_battery = 3.7                  # reference voltages for a full/empty battery, in volts
empty_battery = 2.0                 # the values could vary by battery size/manufacturer so you might need to adjust them


while True:
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.read_u16() * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100
        
    print('voltage: ' + str(voltage) + ' / ' + str(percentage) + '%')
    time.sleep(10)
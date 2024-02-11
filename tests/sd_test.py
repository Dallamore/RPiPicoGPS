import machine, os, sdcard

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(14, machine.Pin.OUT)
# Intialize SPI peripheral (start with 1 MHz)
spi = machine.SPI(1,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(10),
                  mosi=machine.Pin(11),
                  miso=machine.Pin(12))
# Initialize SD card
sd = sdcard.SDCard(spi, cs)

os.mount(sd, '/sd')


# try some standard file operations
file = open('/sd/test.txt', 'w')
file.write('Testing SD card on Maker Pi Pico')
file.close()
file = open('/sd/test.txt', 'r')
data = file.read()
print(data + ' yo')
file.close()

# loopCount = 0
# while True:
#     file = open('/sd/test.txt', 'a')
#     file.write(str(loopCount) + '\n')
#     file.close()
#     loopCount +=1




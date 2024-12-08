import spidev
import time

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, device 0
spi.max_speed_hz = 1350000

def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

try:
    while True:
        value = read_adc(0)  # Replace 0 with your sensor's channel
        print(f"Raw ADC Value: {value}")
        time.sleep(1)
except KeyboardInterrupt:
    spi.close()
    print("Stopped.")


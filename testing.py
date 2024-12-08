import spidev
import time

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Function to read from MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

# Test soil moisture sensor
try:
    while True:
        raw_value = read_adc(1)  # Change to the correct channel you're using
        print(f"Raw Sensor Value: {raw_value}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    spi.close()


import spidev  # For SPI communication with MCP3008
import time

# Create SPI connection
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000  # Set maximum SPI speed

# Function to read from MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])  # Send the SPI command
    raw_value = ((adc[1] & 3) << 8) + adc[2]  # Combine two bytes to get ADC value
    return raw_value

# Continuously read and print ADC value for moisture sensor
try:
    while True:
        # Replace 0 with the correct channel number where your moisture sensor is connected
        raw_value = read_adc(0)  
        print(f"ADC Value: {raw_value}")
        time.sleep(1)  # Wait for 1 second before reading again
except KeyboardInterrupt:
    print("Exiting program.")
    spi.close()  # Close SPI connection when the program is interrupted


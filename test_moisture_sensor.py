import spidev
import json

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000  # Set SPI speed

def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    raw_value = ((adc[1] & 3) << 8) + adc[2]
    return raw_value

# Load calibration config
with open('cap_config.json') as json_data_file:
    config_data = json.load(json_data_file)

def percent_translation(raw_val):
    return round(abs((raw_val - config_data["zero_saturation"]) /
                     (config_data["full_saturation"] - config_data["zero_saturation"])) * 100, 3)

# Test soil moisture
raw_value = read_adc(1)
percent_moisture = percent_translation(raw_value)
print(f"Raw Value: {raw_value}, Translated Moisture: {percent_moisture}%")


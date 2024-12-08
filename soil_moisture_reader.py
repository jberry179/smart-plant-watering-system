import spidev
import time
import requests  # For sending data to ThingSpeak
import RPi.GPIO as GPIO

# Initialize SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Define relay GPIO pin
RELAY_PIN = 17  # Update if needed
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Start with relay off

# ThingSpeak configuration
THINGSPEAK_API_KEY = "USOXO0ZYDETACGIJ"  # Using your Write API Key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Define moisture threshold
MOISTURE_THRESHOLD = 500

def read_channel(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def send_to_thingspeak(moisture_level):
    # Prepare payload
    payload = {
        'api_key': THINGSPEAK_API_KEY,
        'field1': moisture_level  # Assuming field1 is for moisture
    }
    # Send request
    try:
        response = requests.get(THINGSPEAK_URL, params=payload)
        if response.status_code == 200:
            print("Data sent to ThingSpeak successfully.")
        else:
            print("Failed to send data to ThingSpeak. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error sending data to ThingSpeak:", e)

try:
    while True:
        # Read moisture level
        moisture_level = read_channel(0)
        print("Soil Moisture Level:", moisture_level)

        # Check if moisture is below threshold
        if moisture_level > MOISTURE_THRESHOLD:
            print("Soil is dry, activating water pump.")
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn on pump
        else:
            print("Soil is wet enough, turning off water pump.")
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn off pump

        # Send data to ThingSpeak every loop iteration (adjust timing as needed)
        send_to_thingspeak(moisture_level)

        time.sleep(15)  # Send data every 15 seconds (adjust interval as needed)
except KeyboardInterrupt:
    print("Program stopped by the user.")
finally:
    spi.close()
    GPIO.cleanup()


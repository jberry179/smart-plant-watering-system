from RPi.GPIO import setmode, BCM, setup, output, HIGH, LOW, OUT
import time

RELAY_PIN = 17  # Your relay GPIO pin

setmode(BCM)
setup(RELAY_PIN, OUT)

print("Turning ON (relay LOW)...")
output(RELAY_PIN, LOW)  # Turn ON the pump
time.sleep(5)

print("Turning OFF (relay HIGH)...")
output(RELAY_PIN, HIGH)  # Turn OFF the pump
time.sleep(5)


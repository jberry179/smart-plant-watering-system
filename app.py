from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from bcrypt import hashpw, gensalt, checkpw
from cryptography.fernet import Fernet
import spidev
import RPi.GPIO as GPIO
import time
import requests  # For ThingSpeak API

# Initialize Flask app
app = Flask(__name__)

# Flask secret key
app.secret_key = '59d2ddb4a8c059266fdea90dcc7aa5ae78b69cf198ef2752'

# Fernet encryption key
ENCRYPTION_KEY = b'2GCEcewxUP9BexYRbkNVmh6XszEFNyZRTpz4qzbCcNc='
cipher = Fernet(ENCRYPTION_KEY)

# ThingSpeak API Keys
THINGSPEAK_WRITE_API_KEY = "USOXO0ZYDETACGIJ"

# GPIO setup
RELAY_PIN = 17

# Moisture threshold
MOISTURE_THRESHOLD = 480

def initialize_gpio():
    """Initialize GPIO settings."""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Start with pump off

initialize_gpio()

# Encryption functions
def encrypt_data(data):
    """Encrypt the data using Fernet symmetric encryption."""
    return cipher.encrypt(str(data).encode())

def decrypt_data(encrypted_data):
    """Decrypt the data using Fernet symmetric encryption."""
    return cipher.decrypt(encrypted_data).decode()

# Send data to ThingSpeak
def send_to_thingspeak(moisture_level, pump_status):
    """Send data to ThingSpeak."""
    url = f"https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_API_KEY}"
    data = {
        "field1": moisture_level,
        "field2": "ON" if pump_status else "OFF"
    }
    response = requests.get(url, params=data)
    if response.status_code == 200:
        print("Data sent to ThingSpeak successfully.")
    else:
        print(f"Failed to send data to ThingSpeak: {response.status_code}")

# Read moisture level
def read_moisture_level():
    """Read and encrypt moisture level."""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1, (8 + 1) << 4, 0])  # Channel 1
    data = ((adc[1] & 3) << 8) + adc[2]
    spi.close()
    encrypted_data = encrypt_data(data)
    return encrypted_data

# Flask-WTF forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in session:
            return "User already exists!", 400
        hashed_pw = hashpw(password.encode(), gensalt())
        session[username] = hashed_pw
        print(f"Password entered: {password}")
        print(f"Hashed Password: {hashed_pw}")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in session and checkpw(password.encode(), session[username]):
            session['user'] = username
            print(f"Password entered: {password}")
            print(f"Stored Hashed Password: {session[username]}")
            print("Password verification successful!")
            return redirect(url_for('index'))
        return "Invalid credentials!", 400
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    initialize_gpio()

    encrypted_moisture = read_moisture_level()
    decrypted_moisture = int(decrypt_data(encrypted_moisture))

    print(f"Encrypted Moisture Value Received: {encrypted_moisture}")
    print(f"Decrypted Moisture Value: {decrypted_moisture}")

    pump_status = GPIO.input(RELAY_PIN) == GPIO.LOW
    send_to_thingspeak(decrypted_moisture, pump_status)

    moisture_message = (
        "Soil is moist." if decrypted_moisture < 450 else
        "Soil is dry, needs watering." if decrypted_moisture > 550 else
        "Soil moisture is adequate."
    )

    return render_template(
        'index.html',
        moisture_message=moisture_message,
        moisture_level=decrypted_moisture,
        pump_status=pump_status
    )

@app.route('/toggle_pump', methods=['POST'])
def toggle_pump():
    if 'user' not in session:
        return redirect(url_for('login'))
    initialize_gpio()
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn on the pump
    print("Turning ON the pump (relay LOW)...")
    time.sleep(5)  # Run the pump for 5 seconds
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn off the pump
    print("Turning OFF the pump (relay HIGH)...")
    return redirect(url_for('index'))

@app.route('/auto_water', methods=['POST'])
def auto_water():
    if 'user' not in session:
        return redirect(url_for('login'))

    initialize_gpio()
    max_runtime = 15
    elapsed_time = 0

    while elapsed_time < max_runtime:
        encrypted_moisture = read_moisture_level()
        decrypted_moisture = int(decrypt_data(encrypted_moisture))

        print(f"Moisture Level: {decrypted_moisture} (Threshold: {MOISTURE_THRESHOLD})")

        if decrypted_moisture > MOISTURE_THRESHOLD:
            print("Soil moisture is sufficient. Stopping automation.")
            break

        GPIO.output(RELAY_PIN, GPIO.LOW)
        print("Turning ON the pump (relay LOW)...")
        time.sleep(5)
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        print("Turning OFF the pump (relay HIGH)...")
        send_to_thingspeak(decrypted_moisture, GPIO.input(RELAY_PIN) == GPIO.LOW)

        time.sleep(60)
        elapsed_time += 5 + 60

    GPIO.output(RELAY_PIN, GPIO.HIGH)
    print("Automation complete. Pump turned OFF.")
    return redirect(url_for('index'))

@app.teardown_appcontext
def cleanup(exception=None):
    GPIO.cleanup()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


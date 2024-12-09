from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from cryptography.fernet import Fernet
from bcrypt import hashpw, gensalt, checkpw
import RPi.GPIO as GPIO
import spidev
import time
import requests

# Initialize Flask app
app = Flask(__name__)
app.secret_key = '59d2ddb4a8c059266fdea90dcc7aa5ae78b69cf198ef2752'

# Encryption Key
ENCRYPTION_KEY = b'9pBJJSGbF9Q8S2vixDl_N144APQ2xi0vxVizbbehg3g='
cipher = Fernet(ENCRYPTION_KEY)

# GPIO Setup
RELAY_PIN = 17
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)

# Moisture Threshold
MOISTURE_THRESHOLD = 450

# Flask-WTF Forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Functions
def encrypt_data(data):
    return cipher.encrypt(str(data).encode())

def decrypt_data(encrypted_data):
    return cipher.decrypt(encrypted_data).decode()

def read_moisture():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1, (8 + 1) << 4, 0])  # Reading channel 1 on MCP3008
    value = ((adc[1] & 3) << 8) + adc[2]
    spi.close()
    return value

def send_to_thingspeak(moisture, pump_status):
    url = "https://api.thingspeak.com/update"
    data = {
        "api_key": "USOXO0ZYDETACGIJ",
        "field1": moisture,
        "field2": "ON" if pump_status else "OFF"
    }
    response = requests.get(url, params=data)
    if response.status_code == 200:
        print("Data sent to ThingSpeak successfully.")
    else:
        print(f"Error sending data to ThingSpeak: {response.status_code}")

# Routes
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    GPIO.setmode(GPIO.BCM)  # Ensure mode is set
    GPIO.setup(RELAY_PIN, GPIO.OUT)  # Ensure pin is configured as OUTPUT

    moisture_raw = read_moisture()
    encrypted_moisture = encrypt_data(moisture_raw)
    print(f"Encrypted Moisture Value: {encrypted_moisture}")

    decrypted_moisture = int(decrypt_data(encrypted_moisture))
    pump_status = GPIO.input(RELAY_PIN) == GPIO.LOW

    moisture_message = "Soil is dry. It needs to be watered!" if decrypted_moisture > 550 else \
                       "Soil is moist. No watering needed." if decrypted_moisture <= 450 else \
                       "Soil is moderately moist. Monitor closely."

    send_to_thingspeak(decrypted_moisture, pump_status)

    return render_template(
        'index.html', 
        moisture_level=decrypted_moisture, 
        pump_status=pump_status, 
        moisture_message=moisture_message, 
        user=session['user']
    )

@app.route('/toggle_pump', methods=['POST'])
def toggle_pump():
    if 'user' not in session:
        return redirect(url_for('login'))

    GPIO.setmode(GPIO.BCM)  # Ensure mode is set
    GPIO.setup(RELAY_PIN, GPIO.OUT)  # Ensure pin is configured as OUTPUT

    GPIO.output(RELAY_PIN, GPIO.LOW)
    time.sleep(5)
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    return redirect(url_for('index'))

@app.route('/auto_water', methods=['POST'])
def auto_water():
    if 'user' not in session:
        return redirect(url_for('login'))

    GPIO.setmode(GPIO.BCM)  # Ensure mode is set
    GPIO.setup(RELAY_PIN, GPIO.OUT)  # Ensure pin is configured as OUTPUT

    start_time = time.time()
    while time.time() - start_time < 15:
        moisture = read_moisture()
        if moisture > MOISTURE_THRESHOLD:
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(5)
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            break
        time.sleep(60)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in session and checkpw(password.encode(), session[username]):
            session['user'] = username
            return redirect(url_for('index'))
        return "Invalid credentials!"
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in session:
            return "User already exists!"
        session[username] = hashpw(password.encode(), gensalt())
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Cleanup GPIO
@app.teardown_appcontext
def cleanup(exception=None):
    GPIO.cleanup()

# Run Flask app with HTTPS
if __name__ == '__main__':
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=5000)


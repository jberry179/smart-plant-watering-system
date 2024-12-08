# Smart Watering System Project

A Flask-based IoT project designed to monitor soil moisture and automate plant watering. The system integrates ThingSpeak for data logging and visualization and incorporates user authentication and encryption for enhanced security.

---

## Features
- **Soil Moisture Monitoring**: Continuously monitors and logs soil moisture levels.
- **Automatic Watering**: Automatically waters the plant when moisture falls below a threshold.
- **Manual Watering**: Allows users to manually water the plant via a web interface.
- **Data Security**: Passwords and moisture data are encrypted before storage and transmission.
- **ThingSpeak Integration**: Sends real-time moisture data to ThingSpeak for visualization.
- **Authentication**: User login system with secure password storage.

---

## Getting Started

### Prerequisites
- Raspberry Pi (tested on Raspberry Pi 4)
- MCP3008 ADC
- Soil moisture sensor
- Relay module and water pump
- Python 3.9+ installed on your system
- ThingSpeak API keys (free account required)

### Installation Steps
1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd smart_watering_project
2. **Set up virtural environment**
python3 -m venv venv
source venv/bin/activate
3. **Install Depnedencies**
pip install - r requirements.txt
4. **Run the Flask application**
python app.py
5.**Access the app via your browser**

**Project Structure**
smart_watering_project/
├── app.py                  # Main application file
├── templates/              # HTML templates for Flask
│   ├── index.html
│   ├── login.html
│   ├── register.html
├── static/                 # Static files (CSS, JS, images)
├── requirements.txt        # List of Python dependencies
├── README.md               # Documentation file
├── cap_config.json         # Configuration file for soil moisture calibration
├── watering_log.txt        # Log file for watering events
├── .gitignore              # Git ignore file


##License
This project is inended for educational purposes only


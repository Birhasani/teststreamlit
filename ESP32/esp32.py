import time
import board
import busio
from adafruit_pca9685 import PCA9685
import network
from micropython import const
from microdot import Microdot, Response

# Set up Wi-Fi
ssid = "Kost Gebang Kidul(Atas)"
password = "kostgebangkidul40"

# Set up the web server using Microdot
app = Microdot()

# Set up PCA9685 (8 servos connected to the ESP32)
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 60  # Frequency for PWM signal

# Function to move a servo
def move_servo(servo_num, position):
    """Move servo to a specific position (0-180 degrees)."""
    pulse = int(position * 4095 / 180)  # Convert position to PWM value (0-4095)
    pca.channels[servo_num].duty_cycle = pulse

# Function to convert Braille character (e.g., 101010) to servo movements
def braille_to_servo_commands(braille):
    """Move servos based on Braille character input."""
    for i, char in enumerate(braille):
        if char == '1':  # If Braille character is "1", move the corresponding servo
            move_servo(i, 90)  # Raise the servo (90 degrees)
        else:
            move_servo(i, 0)  # Lower the servo (0 degrees)

# Wi-Fi connection function
def connect_wifi():
    """Connect the ESP32 to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)

    print('Connected to Wi-Fi, IP:', wlan.ifconfig()[0])

# Route to handle Braille requests
@app.route('/braille')
def braille(request):
    """Receive Braille string via HTTP request and move servos."""
    braille_input = request.args.get('braille', '')
    if braille_input:
        braille_to_servo_commands(braille_input)
        return Response('Braille processed and sent to servos')
    return Response('Invalid Braille input')

# Start Wi-Fi connection
connect_wifi()

# Start the web server on ESP32
print("Starting server...")
app.run(debug=True, host='0.0.0.0', port=80)  # Run the server on port 80


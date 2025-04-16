import time
import machine
import uasyncio as asyncio
import usocket as socket
from adafruit_pca9685 import PCA9685

# Set up Wi-Fi
ssid = "Kost Gebang Kidul(Atas)"
password = "kostgebangkidul40"

# Set up I2C using machine
scl_pin = machine.Pin(22)  # Replace with the correct SCL pin for your setup
sda_pin = machine.Pin(21)  # Replace with the correct SDA pin for your setup

# Create I2C instance using machine module
i2c = machine.I2C(scl=scl_pin, sda=sda_pin, freq=400000)  # 400kHz is a common frequency for I2C
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
    wlan = machine.WLAN(machine.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)

    print('Connected to Wi-Fi, IP:', wlan.ifconfig()[0])

# Handle client request and serve Braille input
async def handle_client(client_socket):
    request = await client_socket.recv(1024)
    print('Request received:', request)

    # Simple GET request handler to fetch Braille input from the query parameter
    request_str = str(request)
    if 'GET /braille?braille=' in request_str:
        start_index = request_str.find('braille=') + len('braille=')
        end_index = request_str.find(' ', start_index)
        braille_input = request_str[start_index:end_index]

        if braille_input:
            # Process Braille input and move servos
            braille_to_servo_commands(braille_input)
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += "Connection: close\r\n\r\n"
            response += f"<html><body><h1>Braille '{braille_input}' processed successfully!</h1></body></html>"
        else:
            response = "HTTP/1.1 400 Bad Request\r\n"
            response += "Content-Type: text/html\r\n"
            response += "Connection: close\r\n\r\n"
            response += "<html><body><h1>Invalid Braille input</h1></body></html>"

    else:
        # Default response for unrecognized request
        response = "HTTP/1.1 404 Not Found\r\n"
        response += "Content-Type: text/html\r\n"
        response += "Connection: close\r\n\r\n"
        response += "<html><body><h1>Page Not Found</h1></body></html>"

    await client_socket.send(response)
    await client_socket.close()

# Web server running on the ESP32
async def web_server():
    # Set up a socket server listening on port 80
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(1)
    print("Server listening on port 80...")
    
    while True:
        client_socket, _ = await server_socket.accept()
        asyncio.create_task(handle_client(client_socket))

# Start Wi-Fi connection
connect_wifi()

# Start the web server on ESP32
print("Starting server...")
asyncio.run(web_server())  # Run the server on port 80

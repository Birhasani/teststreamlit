import time
import machine
import uasyncio as asyncio
import usocket as socket
from adafruit_pca9685 import PCA9685

ssid = "Kost Gebang Kidul(Atas)"
password = "kostgebangkidul40"

scl_pin = machine.Pin(22)
sda_pin = machine.Pin(21)

i2c = machine.I2C(scl=scl_pin, sda=sda_pin, freq=400000)
pca = PCA9685(i2c)
pca.frequency = 60

def move_servo(servo_num, position):
    pulse = int(position * 4095 / 180)
    pca.channels[servo_num].duty_cycle = pulse

def braille_to_servo_commands(braille):
    for i, char in enumerate(braille):
        if char == '1':
            move_servo(i, 90)
        else:
            move_servo(i, 0)

def connect_wifi():
    wlan = machine.WLAN(machine.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to Wi-Fi, IP:', wlan.ifconfig()[0])

async def handle_client(client_socket):
    request = await client_socket.recv(1024)
    print('Request received:', request)

    request_str = str(request)
    if 'GET /braille?braille=' in request_str:
        start_index = request_str.find('braille=') + len('braille=')
        end_index = request_str.find(' ', start_index)
        braille_input = request_str[start_index:end_index]

        if braille_input:
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
        response = "HTTP/1.1 404 Not Found\r\n"
        response += "Content-Type: text/html\r\n"
        response += "Connection: close\r\n\r\n"
        response += "<html><body><h1>Page Not Found</h1></body></html>"

    await client_socket.send(response)
    await client_socket.close()

async def web_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(1)
    print("Server listening on port 80...")
    
    while True:
        client_socket, _ = await server_socket.accept()
        asyncio.create_task(handle_client(client_socket))

connect_wifi()

print("Starting server...")
asyncio.run(web_server())

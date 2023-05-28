import network
import ujson
from machine import Pin, ADC
import socket

# Wi-Fi credentials
wifi_ssid = "SSID"
wifi_password = "PWD"

# Set up Wi-Fi connection
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(wifi_ssid, wifi_password)

# Wait until Wi-Fi connection is established
while not sta_if.isconnected():
    pass

# Analog sensor pins
sensor_pins = [26, 27, 28]

# Create ADC objects for each sensor pin
adc = [ADC(Pin(pin)) for pin in sensor_pins]


def read_sensor_values():
    # Read the analog sensor values
    sensor_values = [adc.read_u16() * 3.3 / 65536 for adc in adc]
    return sensor_values


def handle_request(client_sock):
    # Receive the request data
    request_data = client_sock.recv(1024)
    request_data = request_data.decode()
    # Extract the GET path from the request
    path = request_data.split()[1]
    # Check if it's a valid request
    if path == '/sensor-data':
        # Read the sensor values
        sensor_values = read_sensor_values()
        # Create a dictionary with sensor readings
        sensor_data = {
            "sensor1": sensor_values[0],
            "sensor2": sensor_values[1],
            "sensor3": sensor_values[2]
        }
        # Convert the dictionary to JSON
        json_data = ujson.dumps(sensor_data)
        # Send the JSON response
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + json_data
    else:
        # Send a 404 Not Found response for other paths
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
    # Send the response back to the client
    client_sock.send(response)
    # Close the client socket
    client_sock.close()


def run_web_server():
    # Set up a socket and bind it to the server address
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('0.0.0.0', 80))
    # Listen for incoming connections
    server_sock.listen(1)
    print("Web server is running")
    while True:
        # Accept a client connection
        client_sock, client_addr = server_sock.accept()
        print("Client connected:", client_addr)
        # Handle the client request
        handle_request(client_sock)


# Main program
run_web_server()
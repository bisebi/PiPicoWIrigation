import network
import ujson
from machine import Pin, Timer
import socket

# Wi-Fi credentials
wifi_ssid = "Your_WiFi_SSID"
wifi_password = "Your_WiFi_Password"

# Set up Wi-Fi connection
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(wifi_ssid, wifi_password)

# Wait until Wi-Fi connection is established
while not sta_if.isconnected():
    pass

# GPIO pins for water pumps
pump_pins = [26, 27, 28]

# Create Pin objects for each pump pin
pumps = [Pin(pin, Pin.OUT) for pin in pump_pins]

# Timer objects for each pump
pump_timers = [None] * len(pump_pins)


def control_pump(pump_index, state):
    # Control the water pump state
    pumps[pump_index].value(state)


def stop_pump(pump_index):
    # Stop the water pump
    control_pump(pump_index, 0)


def handle_request(client_sock):
    # Receive the request data
    request_data = client_sock.recv(1024)
    request_data = request_data.decode()
    # Extract the POST data
    post_match = ure.search("POST / HTTP/1.1\r\nContent-Length: (\d+)", request_data)
    if post_match:
        content_length = int(post_match.group(1))
        body_start = request_data.find(b"\r\n\r\n") + 4
        post_data = request_data[body_start:body_start + content_length]
        # Parse the JSON data
        try:
            json_data = ujson.loads(post_data)
            # Check if the 'pump' field is present
            if 'pump' in json_data:
                pump_index = json_data['pump']
                # Check if the 'state' field is present
                if 'state' in json_data:
                    pump_state = json_data['state']
                    # Check if the 'duration' field is present
                    if 'duration' in json_data:
                        pump_duration = json_data['duration']
                        # Turn on the water pump
                        control_pump(pump_index, pump_state)
                        if pump_state:
                            # Create a timer to stop the pump after the specified duration
                            if pump_timers[pump_index] is not None:
                                pump_timers[pump_index].deinit()
                            pump_timers[pump_index] = Timer()
                            pump_timers[pump_index].init(mode=Timer.ONE_SHOT, period=pump_duration * 1000, callback=lambda t: stop_pump(pump_index))
                        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nPump state updated"
                    else:
                        response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid request: 'duration' field missing"
                else:
                    response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid request: 'state' field missing"
            else:
                response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid request: 'pump' field missing"
        except ujson.JSONDecodeError:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid JSON data"
    else:
        response = "HTTP/1.1 400 Bad Request\r\n\r\nInvalid POST request"
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
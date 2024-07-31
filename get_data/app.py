import threading
import time
import os
import socket
import requests

# Initial Tcp connection setting
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

SensorIP = '192.168.1.186'
SensorPort = 25555
Frequency = 0.5
api_address = "http://127.0.0.1:5000/api/add_data"

## Check connection to sensors
def check_socket_connection(tcp_socket, host, port):
    try:
        # Attempt to connect to the server
        tcp_socket.connect((host, port))
        # tcp_socket.close()
        return True
    except socket.error as e:
        print(f"Socket error: {e}")
        return False

## Connect to Sensor Data
def ReadSensor(tcp_socket):
    try:
        tcp_socket.settimeout(5.0)  # Set a timeout of 5 seconds
        sensorData = tcp_socket.recv(1024)
        
        decoded_data = sensorData.decode('utf-8').split(' ')
        data = decoded_data[1].split("\r\n") 
        temperature = float(data[0][1:])
        resistance = float(data[1][1:])

        return {"temperature": temperature, "resistance": resistance}
    except socket.timeout:
        print("Timeout error: The read operation timed out")
        return None


# Check the connection before reading data
if check_socket_connection(tcp_socket, SensorIP, SensorPort):
    while True:
        time.sleep(1/Frequency)
        data = ReadSensor(tcp_socket)
        if data:
            # posting the data to the api
            response = requests.post(api_address, json=data)
            if not response.ok:
                print(f"Failed to post data to the API. Error: {response.status_code}")
        else:
            print("Unable to read data from the sensor.")
else:
    print("Unable to connect to the sensor.")
    
  
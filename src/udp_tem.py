import socket
import struct
import time
import random

# IP y puerto del ESP32 receptor
UDP_IP = "192.168.128.26"
UDP_PORT = 4210

# ID del sensor y valor de temperatura (float)
sensor_id = 2

# Empaquetar datos: 1 byte (uint8) + 4 bytes (float)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    temperature = random.randint(20,28)  # supera el umbral
    data = struct.pack('Bf', sensor_id, temperature)
    sock.sendto(data, (UDP_IP, UDP_PORT))
    print(f"Enviado -> ID: {sensor_id} | Temperatura: {temperature}")
    time.sleep(2)

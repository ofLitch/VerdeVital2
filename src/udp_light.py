import socket
import struct
import time
import random
# IP y puerto del ESP32 receptor
UDP_IP = "192.168.128.26"
UDP_PORT = 4210

# ID del sensor y valor de temperatura (float)
sensor_id = 3

# Empaquetar datos: 1 byte (uint8) + 4 bytes (float)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    light = random.randint(10, 600)  # supera el umbral
    data = struct.pack('Bf', sensor_id, light)
    sock.sendto(data, (UDP_IP, UDP_PORT))
    print(f"Enviado -> ID: {sensor_id} | Iluminación: {light}")
    time.sleep(1)

import socket
import struct
import time

# IP y puerto del ESP32 receptor
UDP_IP = "192.168.1.11"
UDP_PORT = 4210
# ID del sensor y valor de temperatura (float)
sensor_id = 1
humidity = 70  # supera el umbral

# Empaquetar datos: 1 byte (uint8) + 4 bytes (float)
data = struct.pack('Bf', sensor_id, humidity)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    sock.sendto(data, (UDP_IP, UDP_PORT))
    print(f"Enviado -> ID: {sensor_id} | Humedad: {humidity}")
    time.sleep(2)

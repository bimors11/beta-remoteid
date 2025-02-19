import paho.mqtt.client as mqtt
import json
import math
import time

# Konfigurasi MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "drone/telemetry"
DRONE_ID = "drone_01"

# Konfigurasi Orbit Drone
latitude_center = -6.914744  # Contoh: Bandung, Indonesia
longitude_center = 107.609810
radius = 0.0009  # Radius ~100 meter dalam koordinat geografis
altitude = 50  # Ketinggian 50 meter
speed = 5  # Kecepatan konstan 5 m/s

# Fungsi untuk menghitung posisi drone
def calculate_position(angle):
    # Konversi angle ke radian
    rad = math.radians(angle)
    latitude = latitude_center + (radius * math.cos(rad))
    longitude = longitude_center + (radius * math.sin(rad))
    return latitude, longitude

# Fungsi untuk mengirim data telemetri ke broker MQTT
def send_telemetry(client, latitude, longitude, altitude, speed):
    data = {
        "id": DRONE_ID,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "barometer_altitude": altitude,
        "speed": speed
    }
    client.publish(MQTT_TOPIC, json.dumps(data))
    print(f"Data sent: {data}")

# Callback untuk koneksi MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

# Setup MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Simulasi pergerakan drone mengelilingi titik pusat
angle = 0
while True:
    # Hitung posisi drone berdasarkan sudut
    latitude, longitude = calculate_position(angle)
    
    # Kirim data telemetri
    send_telemetry(mqtt_client, latitude, longitude, altitude, speed)
    
    # Ubah sudut untuk simulasi pergerakan melingkar
    angle += 10
    if angle >= 360:
        angle = 0
    
    # Delay untuk pengiriman data (sesuaikan sesuai kebutuhan)
    time.sleep(1)

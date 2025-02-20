import paho.mqtt.client as mqtt
import json
import time
import random
import math

# **Konfigurasi MQTT Broker**
MQTT_BROKER = "192.168.67.114"  # IP Server Database
MQTT_PORT = 1883
MQTT_TOPIC = "drone/telemetry"

# **Identitas Drone & Pilot**
DRONE_ID = "drone2"
PILOT_ID = "pilot1"

# **Pusat orbit (Koordinat simulasi)**
CENTER_LAT = -6.200000  # Latitude Jakarta
CENTER_LON = 106.700000  # Longitude Jakarta
RADIUS = 0.0009  # 100 meter dalam satuan derajat

# MQTT Setup
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
    else:
        print(f"⚠️ Failed to connect, return code {rc}")

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# **Fungsi untuk menghitung titik koordinat orbit**
def get_orbit_point(angle):
    lat = CENTER_LAT + (RADIUS * math.cos(math.radians(angle)))
    lon = CENTER_LON + (RADIUS * math.sin(math.radians(angle)))
    return lat, lon

# **Loop utama simulasi**
angle = 0  # Memulai dari 0 derajat

while True:
    angle = (angle + 10) % 360  # Memutar 10 derajat setiap iterasi
    latitude, longitude = get_orbit_point(angle)

    altitude = round(50 + random.uniform(-2, 2), 2)
    barometer_altitude = round(101.3 + random.uniform(-1, 1), 2)
    speed = round(5 + random.uniform(-1, 1), 2)

    payload = {
        "id": DRONE_ID,
        "pilot_id": PILOT_ID,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "barometer_altitude": barometer_altitude,
        "speed": speed
    }

    payload_json = json.dumps(payload)
    client.publish(MQTT_TOPIC, payload_json)

    print(f"📡 Sent: {payload_json}")
    time.sleep(3)  # Kirim data setiap 3 detik

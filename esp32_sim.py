import paho.mqtt.client as mqtt
import time
import math
import json

# Konfigurasi MQTT
BROKER = "localhost"  # Alamat broker MQTT
TOPIC = "drone/telemetry"  # Topik untuk mengirim data
DRONE_ID = "drone1"  # ID drone

# Konfigurasi jalur lingkaran
CENTER_LAT = -6.200  # Latitude pusat lingkaran
CENTER_LON = 106.800  # Longitude pusat lingkaran
RADIUS = 0.001  # Radius lingkaran (dalam derajat ~ 111m)
SPEED = 10  # Kecepatan drone dalam m/s
ALTITUDE = 100  # Ketinggian tetap drone
POINTS = 36  # Jumlah titik pada lingkaran

# Hitung interval waktu antar titik
CIRCUMFERENCE = 2 * math.pi * RADIUS * 111000  # Keliling lingkaran (m)
TIME_PER_CYCLE = CIRCUMFERENCE / SPEED  # Waktu untuk satu putaran (s)
INTERVAL = TIME_PER_CYCLE / POINTS  # Waktu antar titik (s)

# Fungsi untuk menghitung koordinat pada lingkaran
def calculate_flight_path():
    path = []
    for i in range(POINTS):
        angle = 2 * math.pi * i / POINTS
        lat = CENTER_LAT + RADIUS * math.cos(angle)
        lon = CENTER_LON + RADIUS * math.sin(angle)
        path.append((lat, lon))
    return path

# Fungsi untuk mengirim data ke broker MQTT
def send_data(client, latitude, longitude, altitude, speed):
    payload = {
        "id": DRONE_ID,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "barometer_altitude": altitude - 10,  # Simulasi ketinggian barometer
        "speed": speed
    }
    client.publish(TOPIC, json.dumps(payload))
    print(f"Sent: {payload}")

# Fungsi utama
def main():
    # Koneksi ke broker MQTT
    client = mqtt.Client()
    client.connect(BROKER, 1883, 60)

    # Hitung jalur penerbangan
    flight_path = calculate_flight_path()

    print("Starting flight path simulation...")
    while True:
        for lat, lon in flight_path:
            send_data(client, lat, lon, ALTITUDE, SPEED)
            time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

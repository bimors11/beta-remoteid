import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import datetime
import threading
import time

# Flask setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drone_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Drone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drone_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="inactive")  # Tambahkan kolom status
    data = db.relationship('DroneData', backref='drone', lazy=True)

class DroneData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=False)
    barometer_altitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    drone_id = db.Column(db.Integer, db.ForeignKey('drone.id'), nullable=False)

# MQTT setup
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "drone/telemetry"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        drone_id = data.get('id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        altitude = data.get('altitude')
        barometer_altitude = data.get('barometer_altitude')
        speed = data.get('speed')

        with app.app_context():  # Tambahkan konteks aplikasi Flask
            # Find or create the drone
            drone = Drone.query.filter_by(drone_id=drone_id).first()
            if not drone:
                drone = Drone(drone_id=drone_id, status="active")
                db.session.add(drone)
            else:
                drone.status = "active"

            # Store telemetry data
            telemetry = DroneData(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                barometer_altitude=barometer_altitude,
                speed=speed,
                drone=drone
            )
            db.session.add(telemetry)
            db.session.commit()

            print(f"Data saved: {data}")
    except Exception as e:
        print(f"Error processing message: {e}")


# Fungsi untuk menonaktifkan drone yang tidak aktif
def deactivate_inactive_drones():
    """
    Periksa drone yang tidak mengirim data dalam 10 detik terakhir dan ubah statusnya menjadi 'inactive'.
    """
    while True:
        with app.app_context():
            now = datetime.datetime.utcnow()
            drones = Drone.query.all()
            for drone in drones:
                # Ambil data terbaru drone
                latest_data = DroneData.query.filter_by(drone_id=drone.id).order_by(DroneData.timestamp.desc()).first()
                if latest_data and (now - latest_data.timestamp).total_seconds() > 10:
                    drone.status = "inactive"
                    db.session.commit()
        time.sleep(10)  # Periksa setiap 10 detik

# REST API
@app.route('/api/data/<drone_id>', methods=['GET'])
def get_drone_logs(drone_id):
    """
    Mengambil semua data telemetri drone berdasarkan ID.
    """
    drone = Drone.query.filter_by(drone_id=drone_id).first()
    if not drone:
        return jsonify({"message": "Drone not found"}), 404

    data = [
        {
            "latitude": d.latitude,
            "longitude": d.longitude,
            "altitude": d.altitude,
            "barometer_altitude": d.barometer_altitude,
            "speed": d.speed,
            "timestamp": d.timestamp
        }
        for d in drone.data
    ]
    return jsonify({"drone_id": drone_id, "data": data}), 200

@app.route('/api/active_drones', methods=['GET'])
def get_active_drones():
    """
    Mengambil semua drone yang sedang aktif (status: 'active').
    """
    drones = Drone.query.filter_by(status="active").all()
    active_drones = [
        {
            "id": drone.drone_id,
            "latitude": latest_data.latitude,
            "longitude": latest_data.longitude,
            "altitude": latest_data.altitude,
            "speed": latest_data.speed
        }
        for drone in drones
        if (latest_data := DroneData.query.filter_by(drone_id=drone.id).order_by(DroneData.timestamp.desc()).first())
    ]
    return jsonify(active_drones)

if __name__ == "__main__":
    # Initialize the database
    with app.app_context():
        db.create_all()

    # Start thread untuk memonitor status drone
    thread = threading.Thread(target=deactivate_inactive_drones, daemon=True)
    thread.start()

    # Start MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=True)

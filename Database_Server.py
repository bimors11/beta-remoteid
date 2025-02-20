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

# Database Models
class Pilot(db.Model):
    id = db.Column(db.String(50), primary_key=True) 
    name = db.Column(db.String(100), nullable=False)
    drones = db.relationship('Drone', backref='pilot', lazy=True)

class Drone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drone_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="inactive")
    last_active = db.Column(db.DateTime, nullable=True)
    pilot_id = db.Column(db.Integer, db.ForeignKey('pilot.id'), nullable=False)
    flight_sessions = db.relationship('FlightSession', backref='drone', lazy=True)

class FlightSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drone_id = db.Column(db.Integer, db.ForeignKey('drone.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=db.func.now())
    end_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    telemetry_data = db.relationship('DroneData', backref='flight_session', lazy=True)

class DroneData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_session_id = db.Column(db.Integer, db.ForeignKey('flight_session.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=False)
    barometer_altitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

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
        pilot_id = data.get('pilot_id')  # Ambil pilot ID
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        altitude = data.get('altitude')
        barometer_altitude = data.get('barometer_altitude')
        speed = data.get('speed')

        if not drone_id or not pilot_id or latitude is None or longitude is None or altitude is None:
            print(f"[ERROR] Incomplete data for drone {drone_id}. Skipping...")
            return

        with app.app_context():
            # **Cek apakah pilot sudah ada**
            pilot = Pilot.query.filter_by(id=pilot_id).first()
            if not pilot:
                print(f"[INFO] Pilot {pilot_id} not found. Creating new pilot entry...")
                pilot = Pilot(id=pilot_id, name=f"{pilot_id}")
                db.session.add(pilot)
                db.session.commit()

            # **Cek apakah drone sudah ada di database**
            drone = Drone.query.filter_by(drone_id=drone_id).first()
            if not drone:
                print(f"[INFO] Drone {drone_id} not found. Creating new drone entry...")
                drone = Drone(drone_id=drone_id, status="active", pilot_id=pilot.id)
                db.session.add(drone)
                db.session.commit()
            else:
                drone.status = "active"
                drone.last_active = datetime.datetime.utcnow()
                drone.pilot_id = pilot.id  # Update jika pilot berubah

            # **Cek apakah ada sesi penerbangan yang aktif**
            flight_session = FlightSession.query.filter_by(drone_id=drone.id, is_active=True).first()
            if not flight_session:
                flight_session = FlightSession(drone_id=drone.id)
                db.session.add(flight_session)
                db.session.commit()

            # **Simpan data telemetri**
            telemetry = DroneData(
                flight_session_id=flight_session.id,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                barometer_altitude=barometer_altitude,
                speed=speed
            )
            db.session.add(telemetry)
            db.session.commit()

            print(f"[SUCCESS] Data saved: {data}")

    except json.JSONDecodeError:
        print("[ERROR] Received invalid JSON data. Skipping...")
    except Exception as e:
        print(f"[ERROR] Processing message: {e}")


def deactivate_inactive_drones():
    while True:
        with app.app_context():
            now = datetime.datetime.utcnow()
            drones = Drone.query.all()
            for drone in drones:
                if drone.last_active and (now - drone.last_active).total_seconds() > 10:
                    print(f"[INFO] Marking {drone.drone_id} as inactive.")
                    drone.status = "inactive"
                    
                    # Menutup sesi penerbangan jika drone tidak aktif
                    flight_session = FlightSession.query.filter_by(drone_id=drone.id, is_active=True).first()
                    if flight_session:
                        flight_session.end_time = now
                        flight_session.is_active = False
                        db.session.commit()
            db.session.commit()
        time.sleep(10)


# REST API
@app.route('/api/active_drones', methods=['GET'])
def get_active_drones():
    drones = Drone.query.filter_by(status="active").all()
    active_drones = [
        {
            "id": drone.drone_id,
            "pilot": drone.pilot.name if drone.pilot else "Unknown",
            "latitude": latest_data.latitude,
            "longitude": latest_data.longitude,
            "altitude": latest_data.altitude,
            "speed": latest_data.speed
        }
        for drone in drones
        if (latest_data := DroneData.query.join(FlightSession).filter(
            FlightSession.drone_id == drone.id, FlightSession.is_active == True
        ).order_by(DroneData.timestamp.desc()).first())
    ]
    return jsonify(active_drones)

@app.route('/api/history/<drone_id>', methods=['GET'])
def get_flight_history(drone_id):
    drone = Drone.query.filter_by(drone_id=drone_id).first()
    if not drone:
        return jsonify({"message": "Drone not found"}), 404

    sessions = FlightSession.query.filter_by(drone_id=drone.id).all()
    history = []
    for session in sessions:
        data = DroneData.query.filter_by(flight_session_id=session.id).all()
        session_data = {
            "start_time": session.start_time,
            "end_time": session.end_time,
            "data": [
                {
                    "latitude": d.latitude,
                    "longitude": d.longitude,
                    "altitude": d.altitude,
                    "barometer_altitude": d.barometer_altitude,
                    "speed": d.speed,
                    "timestamp": d.timestamp
                }
                for d in data
            ]
        }
        history.append(session_data)

    return jsonify({"drone_id": drone_id, "history": history}), 200

@app.route('/api/search', methods=['GET'])
def search_drones():
    query = request.args.get('q', '')
    results = Drone.query.join(Pilot).filter(
        (Drone.drone_id.ilike(f"%{query}%")) | (Pilot.name.ilike(f"%{query}%"))
    ).all()

    response = [
        {"drone_id": drone.drone_id, "pilot": drone.pilot.name, "status": drone.status}
        for drone in results
    ]
    
    return jsonify(response)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    thread = threading.Thread(target=deactivate_inactive_drones, daemon=True)
    thread.start()

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    app.run(host="0.0.0.0", port=5000, debug=True)

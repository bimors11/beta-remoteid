from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# URL server database
DATABASE_API_URL = "http://localhost:5000"  # Ganti dengan URL server database Anda

# Halaman utama (live map)
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint untuk mengambil drone aktif
@app.route('/api/active_drones', methods=['GET'])
def get_active_drones():
    """
    Mengambil drone yang sedang aktif (berdasarkan API database).
    """
    try:
        response = requests.get(f"{DATABASE_API_URL}/api/active_drones")
        if response.status_code != 200:
            return jsonify({"message": "Failed to fetch active drones"}), 500
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"message": "Error fetching active drones", "error": str(e)}), 500

# Endpoint untuk log penerbangan drone tertentu
@app.route('/api/drone_logs/<drone_id>', methods=['GET'])
def get_drone_logs(drone_id):
    """
    Mengambil log penerbangan drone tertentu dari server database.
    """
    try:
        response = requests.get(f"{DATABASE_API_URL}/api/data/{drone_id}")
        if response.status_code != 200:
            return jsonify({"message": "Failed to fetch drone logs"}), 500
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"message": "Error fetching drone logs", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

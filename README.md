- **Database_Server.py** : Kode untuk Server Database
- **Livestream_Server.py** : Kode Backend untuk Livestream Localhost
- **templates/index.html** : Kode Frontend untuk Livestream
- **remoteid.cpp** : Kode pada ESP32

---------------------------------------------------------------------------------------------------------------------------


Fitur
  1. Monitoring Real-Time:
    - Menampilkan posisi drone yang sedang aktif di peta interaktif.
    - Memperbarui posisi drone secara berkala (setiap 3 detik).

 2. Informasi Detail Drone:
    - Menampilkan data seperti ID drone, posisi GPS (latitude, longitude), ketinggian, dan kecepatan drone yang sedang terbang.

 3. Log Penerbangan:
    - Menyediakan log lengkap penerbangan drone, termasuk posisi, ketinggian, kecepatan, dan waktu penerbangan.

 4. Pencarian Drone:
    - Memungkinkan pencarian drone berdasarkan ID untuk melihat log penerbangan sebelumnya.


Komponen Sistem
1. Server Database
    Menerima data telemetri drone melalui protokol MQTT.
    Menyimpan data ke dalam database SQLite.
    Menyediakan API untuk mengambil data drone yang sedang aktif atau log penerbangan drone tertentu.
2. Server Livestream
    Mengambil data dari server database menggunakan API HTTP.
    Menyediakan antarmuka berbasis web untuk menampilkan drone aktif dan log penerbangan.
   
Library
1. Flask: Framework untuk server web.
2. Flask-SQLAlchemy: ORM untuk pengelolaan database.
3. paho-mqtt: Untuk komunikasi dengan broker MQTT.
4. requests: Untuk melakukan permintaan HTTP ke server API.

Broker MQTT:
1. Mosquitto (atau broker MQTT lain).

Database:
1. SQLite (sudah terintegrasi dengan Python).

Server Lokal:
1. Server database untuk menerima data telemetri melalui MQTT.
1. Server livestream untuk menampilkan data real-time di web.

Frontend:
HTML, CSS, dan Leaflet.js untuk peta interaktif pada antarmuka web.

Alat Pendukung:
Mosquitto CLI untuk menguji pengiriman data MQTT.
Browser untuk mengakses antarmuka web livestream.

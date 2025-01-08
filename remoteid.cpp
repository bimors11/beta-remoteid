#include <WiFi.h>
#include <PubSubClient.h>
#include <mavlink.h>
#include <SPIFFS.h>

// Konfigurasi WiFi
const char* ssid = "SSID_WIFI";
const char* password = "PASSWORD_WIFI";

// Konfigurasi MQTT
const char* mqtt_server = "192.168.1.93"; // IP server MQTT
const char* mqtt_topic = "drone/telemetry";
const char* device_id = "drone1"; // ID unik untuk ESP ini

WiFiClient espClient;
PubSubClient client(espClient);

// Konfigurasi Serial
#define SERIAL_RX 16  // Pin RX ESP32
#define SERIAL_TX 17  // Pin TX ESP32
#define SERIAL_BAUD 57600

HardwareSerial mavSerial(1);

// Variabel untuk data MAVLink
float latitude = 0.0;
float longitude = 0.0;
float altitude = 0.0;
float barometer_altitude = 0.0;
float speed = 0.0;

// Fungsi untuk koneksi ke WiFi
void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// Callback MQTT (tidak digunakan dalam kasus ini)
void callback(char* topic, byte* payload, unsigned int length) {}

// Fungsi untuk menyimpan data ke file
void save_to_flash(const String& payload) {
  File file = SPIFFS.open("/data.txt", FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open file for appending");
    return;
  }
  file.println(payload);
  file.close();
  Serial.println("Data saved to flash: " + payload);
}

// Fungsi untuk mengirim data yang tersimpan ke server
void resend_from_flash() {
  if (!SPIFFS.exists("/data.txt")) return;

  File file = SPIFFS.open("/data.txt", FILE_READ);
  if (!file) {
    Serial.println("Failed to open file for reading");
    return;
  }

  String line;
  while (file.available()) {
    line = file.readStringUntil('\n');
    if (client.publish(mqtt_topic, line.c_str())) {
      Serial.println("Resent data to MQTT: " + line);
    } else {
      Serial.println("Failed to resend data");
      file.close();
      return; // Jika gagal, jangan hapus data
    }
  }
  file.close();

  // Hapus file setelah semua data dikirim
  SPIFFS.remove("/data.txt");
  Serial.println("All data resent and flash cleared");
}

// Fungsi untuk mengirim data ke MQTT
void send_to_mqtt() {
  String payload = "{\"id\":\"" + String(device_id) +
                   "\",\"latitude\":" + String(latitude, 6) +
                   ",\"longitude\":" + String(longitude, 6) +
                   ",\"altitude\":" + String(altitude, 2) +
                   ",\"barometer_altitude\":" + String(barometer_altitude, 2) +
                   ",\"speed\":" + String(speed, 2) + "}";

  if (client.publish(mqtt_topic, payload.c_str())) {
    Serial.println("Data sent to MQTT: " + payload);
  } else {
    Serial.println("Failed to send data to MQTT. Saving to flash...");
    save_to_flash(payload);
  }
}

// Fungsi untuk membaca data MAVLink
void read_mavlink() {
  mavlink_message_t msg;
  mavlink_status_t status;

  while (mavSerial.available()) {
    uint8_t c = mavSerial.read();

    if (mavlink_parse_char(MAVLINK_COMM_0, c, &msg, &status)) {
      switch (msg.msgid) {
        case MAVLINK_MSG_ID_GLOBAL_POSITION_INT: {
          mavlink_global_position_int_t global_position;
          mavlink_msg_global_position_int_decode(&msg, &global_position);

          latitude = global_position.lat / 1e7;
          longitude = global_position.lon / 1e7;
          altitude = global_position.alt / 1000.0;
          barometer_altitude = global_position.relative_alt / 1000.0;
          speed = sqrt(sq(global_position.vx) + sq(global_position.vy)) / 100.0;
          break;
        }
      }
    }
  }
}

void setup() {
  // Serial untuk debug
  Serial.begin(115200);
  
  // Serial MAVLink
  mavSerial.begin(SERIAL_BAUD, SERIAL_8N1, SERIAL_RX, SERIAL_TX);

  // Inisialisasi SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("Failed to mount file system");
    return;
  }

  // Koneksi WiFi
  setup_wifi();

  // Koneksi MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect(device_id)) {
      Serial.println("Connected to MQTT");
    } else {
      Serial.print("Failed MQTT connection, rc=");
      Serial.print(client.state());
      Serial.println(" Retry in 5 seconds...");
      delay(5000);
    }
  }
}

void loop() {
  // Pastikan koneksi MQTT tetap aktif
  if (!client.connected()) {
    while (!client.connected()) {
      Serial.println("Reconnecting to MQTT...");
      if (client.connect(device_id)) {
        Serial.println("Reconnected to MQTT");
        resend_from_flash(); // Kirim ulang data yang tersimpan
      } else {
        delay(5000);
      }
    }
  }
  client.loop();

  // Baca data MAVLink
  read_mavlink();

  // Kirim data ke MQTT setiap 3 detik
  static unsigned long last_sent = 0;
  if (millis() - last_sent > 3000) {
    last_sent = millis();
    send_to_mqtt();
  }
}

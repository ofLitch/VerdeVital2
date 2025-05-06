/**
 * @file main.cpp
 * @brief Sistema embebido para monitoreo y control ambiental en invernadero de cannabis medicinal.
 * 
 * @details Este sistema basado en ESP32 se conecta a una red WiFi y recibe datos vía UDP desde sensores distribuidos.
 * Cuando los valores superan los umbrales definidos, o si un sensor deja de responder, se notifica al usuario mediante Telegram.
 * 
 * @authors
 *     Valentina Muñoz Arcos  
 *     Luis Miguel Gómez Muñoz  
 *     David Alejandro Ortega Flórez  
 * 
 * @version 1.2
 * @date 2025-05-06
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>
#include <ArduinoJson.h>
#include <math.h>

// === Configuración de red y Telegram ===
#define SSID "El pocas"
#define PASSWORD "nosequeponer"
#define BOT_TOKEN "7836875521:AAGTRDghaQIzQcjYiftXSKeHS17xkPnClLs"
#define CHAT_ID "1559018507"

// === Puerto de escucha UDP ===
const int LOCAL_PORT = 4210;
WiFiUDP udp;

// === Cliente seguro y bot de Telegram ===
WiFiClientSecure client;
UniversalTelegramBot bot(BOT_TOKEN, client);

// === Umbrales de alerta para sensores ===
constexpr float THRESHOLD_LIGHT = 500.0;
constexpr float THRESHOLD_TEMP  = 24.0;
constexpr float THRESHOLD_HUM   = 80.0;

// === Tiempos máximos sin recibir datos (en milisegundos) ===
constexpr unsigned long SENSOR_TIMEOUT_MS = 20000;

// === Estructura para datos de sensor ===
struct SensorData {
  uint8_t id;   ///< 1 = humedad, 2 = temperatura, 3 = luz
  float data;
};

struct SensorValues {
  float light = 0.0;
  float temperature = 0.0;
  float humidity = 0.0;
} sensors;

// === Último tiempo de recepción de datos por sensor ===
unsigned long lastHumidityUpdate = 0;
unsigned long lastTemperatureUpdate = 0;
unsigned long lastLightUpdate = 0;

// === Estados de alerta por sensor para evitar spam ===
bool alertHumidityTimeoutSent = false;
bool alertTemperatureTimeoutSent = false;
bool alertLightTimeoutSent = false;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\n✅ Conectado a WiFi");
  Serial.print("IP: "); Serial.println(WiFi.localIP());
  Serial.print("RSSI: "); Serial.println(WiFi.RSSI());
}

void initTelegramBot() {
  client.setCACert(TELEGRAM_CERTIFICATE_ROOT);
  bot.sendMessage(CHAT_ID, "🤖 *Sistema de monitoreo iniciado correctamente*", "Markdown");
  Serial.println("✅ Bot de Telegram inicializado");
}

void initUDPListener() {
  udp.begin(LOCAL_PORT);
  Serial.printf("📡 Escuchando en puerto UDP %d\n", LOCAL_PORT);
}

void updateSensorValue(const SensorData& received) {
  unsigned long now = millis();

  if (received.data < 0 || received.data > 1000) {
    Serial.println("⚠️ Dato de sensor fuera de rango. Ignorado.");
    return;
  }

  switch (received.id) {
    case 1:
      if (fabs(received.data - sensors.humidity) < 0.1) return;
      sensors.humidity = received.data;
      lastHumidityUpdate = now;
      alertHumidityTimeoutSent = false;
      break;
    case 2:
      if (fabs(received.data - sensors.temperature) < 0.1) return;
      sensors.temperature = received.data;
      lastTemperatureUpdate = now;
      alertTemperatureTimeoutSent = false;
      break;
    case 3:
      if (fabs(received.data - sensors.light) < 0.1) return;
      sensors.light = received.data;
      lastLightUpdate = now;
      alertLightTimeoutSent = false;
      break;
    default:
      Serial.println("❌ ID de sensor desconocido");
      return;
  }

  Serial.printf("✅ Sensor %d actualizado: %.2f\n", received.id, received.data);
  Serial.printf("📊 Humedad: %.2f %% | Temperatura: %.2f °C | Luz: %.2f lx\n",
                sensors.humidity, sensors.temperature, sensors.light);
}

void verifyThresholdsAndNotify() {
  char alert[256] = {0};

  if (sensors.light > THRESHOLD_LIGHT) {
    snprintf(alert + strlen(alert), sizeof(alert) - strlen(alert), "🔆 Alta luz: %.2f lx\n", sensors.light);
  }
  if (sensors.temperature > THRESHOLD_TEMP) {
    snprintf(alert + strlen(alert), sizeof(alert) - strlen(alert), "🌡 Alta temperatura: %.2f °C\n", sensors.temperature);
  }
  if (sensors.humidity > THRESHOLD_HUM) {
    snprintf(alert + strlen(alert), sizeof(alert) - strlen(alert), "💧 Alta humedad: %.2f %%\n", sensors.humidity);
  }

  if (alert[0] != '\0') {
    char message[300];
    snprintf(message, sizeof(message), "🚨 *Alerta de sensores:*\n\n%s", alert);
    bot.sendMessage(CHAT_ID, message, "Markdown");
    Serial.println("📨 Alerta enviada a Telegram");
  }
}

void checkTimeout(unsigned long lastUpdate, bool &alertSent, const char* sensorName) {
  if (millis() - lastUpdate > SENSOR_TIMEOUT_MS && !alertSent) {
    char msg[100];
    snprintf(msg, sizeof(msg), "⚠️ El sensor de *%s* ha dejado de responder.", sensorName);
    bot.sendMessage(CHAT_ID, msg, "Markdown");
    alertSent = true;
    Serial.printf("🚨 Sensor de %s inactivo\n", sensorName);
  }
}

void checkSensorTimeouts() {
  checkTimeout(lastHumidityUpdate, alertHumidityTimeoutSent, "humedad");
  checkTimeout(lastTemperatureUpdate, alertTemperatureTimeoutSent, "temperatura");
  checkTimeout(lastLightUpdate, alertLightTimeoutSent, "luz");
}

void listenUDP() {
  while (udp.parsePacket()) {
    if (udp.available() == sizeof(SensorData)) {
      SensorData received;
      udp.read((uint8_t*)&received, sizeof(SensorData));
      updateSensorValue(received);
    } else {
      Serial.println("⚠️ Paquete UDP con tamaño inesperado. Ignorado.");
      udp.flush();
    }
  }
  verifyThresholdsAndNotify(); // Llamada una vez después de procesar todos los paquetes
}


void setup() {
  Serial.begin(115200);
  connectWiFi();
  initTelegramBot();
  initUDPListener();
}

void loop() {
  listenUDP();
  checkSensorTimeouts();
}

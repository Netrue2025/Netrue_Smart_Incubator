#include "storage.h"

#include <ArduinoJson.h>
#include <Preferences.h>
#include <SPIFFS.h>

namespace {
Preferences prefs;
const char* HISTORY_PATH = "/history.jsonl";
const char* QUEUE_PATH = "/queue.jsonl";

String readingToJson(const Reading& reading) {
  JsonDocument doc;
  doc["temperature"] = reading.temperature;
  doc["humidity"] = reading.humidity;
  doc["heat_index"] = reading.heatIndex;
  doc["relay"] = reading.relay;
  doc["fan_relay"] = reading.fanRelay;
  doc["wifi"] = reading.wifi;
  doc["sync_status"] = reading.syncStatus;
  if (reading.timestamp.length() > 0) {
    doc["timestamp"] = reading.timestamp;
  }
  String out;
  serializeJson(doc, out);
  return out;
}
}

void storageBegin() {
  SPIFFS.begin(true);
  prefs.begin("incubator", false);
}

void saveConfig(const IncubatorConfig& config) {
  prefs.putFloat("targetTemp", config.targetTemp);
  prefs.putFloat("targetHum", config.targetHumidity);
  prefs.putFloat("tolerance", config.tolerance);
  prefs.putFloat("hysteresis", config.hysteresis);
  prefs.putFloat("tempOffset", config.tempOffset);
  prefs.putFloat("humOffset", config.humidityOffset);
  prefs.putBool("manualRelay", config.manualRelay);
  prefs.putBool("emergencyOff", config.emergencyOff);
  prefs.putBool("trayServoEn", config.trayServoEnabled);
  prefs.putInt("trayServoAng", config.trayServoAngle);
  prefs.putInt("trayServoInt", config.trayServoIntervalMinutes);
  prefs.putInt("trayServoSpd", config.trayServoSpeedDps);
  prefs.putString("relayMode", config.relayMode);
  prefs.putString("updatedAt", config.updatedAt);
}

IncubatorConfig loadConfig() {
  IncubatorConfig config;
  config.targetTemp = prefs.getFloat("targetTemp", config.targetTemp);
  config.targetHumidity = prefs.getFloat("targetHum", config.targetHumidity);
  config.tolerance = prefs.getFloat("tolerance", config.tolerance);
  config.hysteresis = prefs.getFloat("hysteresis", config.hysteresis);
  config.tempOffset = prefs.getFloat("tempOffset", config.tempOffset);
  config.humidityOffset = prefs.getFloat("humOffset", config.humidityOffset);
  config.manualRelay = prefs.getBool("manualRelay", config.manualRelay);
  config.emergencyOff = prefs.getBool("emergencyOff", config.emergencyOff);
  config.trayServoEnabled = prefs.getBool("trayServoEn", config.trayServoEnabled);
  config.trayServoAngle = prefs.getInt("trayServoAng", config.trayServoAngle);
  config.trayServoIntervalMinutes = prefs.getInt("trayServoInt", config.trayServoIntervalMinutes);
  config.trayServoSpeedDps = prefs.getInt("trayServoSpd", config.trayServoSpeedDps);
  config.relayMode = prefs.getString("relayMode", config.relayMode);
  config.updatedAt = prefs.getString("updatedAt", config.updatedAt);
  return config;
}

void appendReading(const Reading& reading) {
  File file = SPIFFS.open(HISTORY_PATH, FILE_APPEND);
  if (!file) return;
  file.println(readingToJson(reading));
  file.close();
  trimFile(HISTORY_PATH, MAX_QUEUE_BYTES);
}

void enqueueReading(const Reading& reading) {
  File file = SPIFFS.open(QUEUE_PATH, FILE_APPEND);
  if (!file) return;
  file.println(readingToJson(reading));
  file.close();
  trimFile(QUEUE_PATH, MAX_QUEUE_BYTES);
}

bool peekQueuedReading(String& jsonLine) {
  File file = SPIFFS.open(QUEUE_PATH, FILE_READ);
  if (!file || !file.available()) {
    if (file) file.close();
    return false;
  }
  jsonLine = file.readStringUntil('\n');
  file.close();
  jsonLine.trim();
  return jsonLine.length() > 0;
}

void popQueuedReading() {
  File file = SPIFFS.open(QUEUE_PATH, FILE_READ);
  if (!file) return;
  file.readStringUntil('\n');
  String remaining = file.readString();
  file.close();
  File out = SPIFFS.open(QUEUE_PATH, FILE_WRITE);
  if (!out) return;
  out.print(remaining);
  out.close();
}

size_t queueSize() {
  File file = SPIFFS.open(QUEUE_PATH, FILE_READ);
  if (!file) return 0;
  size_t lines = 0;
  while (file.available()) {
    file.readStringUntil('\n');
    lines++;
  }
  file.close();
  return lines;
}

int loadTrayServoPosition() {
  return prefs.getInt("trayServoPos", SERVO_HOME_ANGLE);
}

void saveTrayServoPosition(int angle) {
  prefs.putInt("trayServoPos", constrain(angle, -180, 180));
}

void trimFile(const char* path, size_t maxBytes) {
  File file = SPIFFS.open(path, FILE_READ);
  if (!file) return;
  if (file.size() <= maxBytes) {
    file.close();
    return;
  }
  file.seek(file.size() / 2);
  file.readStringUntil('\n');
  String remaining = file.readString();
  file.close();
  File out = SPIFFS.open(path, FILE_WRITE);
  if (!out) return;
  out.print(remaining);
  out.close();
}

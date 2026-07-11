#include <Arduino.h>
#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#endif
#include <ArduinoJson.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <U8g2lib.h>
#include <WiFi.h>
#include <esp_idf_version.h>
#include <esp_task_wdt.h>
#include <time.h>
#include <Wire.h>

#include "config.h"
#include "storage.h"

DHT dht(PIN_DHT22, DHT_TYPE);
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

SemaphoreHandle_t stateMutex;
IncubatorConfig config;
Reading latestReading;
Reading pendingUpload;
bool pendingUploadReady = false;
uint8_t sensorFailures = 0;
uint32_t relayOnSince = 0;
uint32_t lastWifiAttempt = 0;
uint32_t lastWifiLog = 0;
uint32_t lastHistoryAppend = 0;
bool displayReady = false;
uint8_t activeOledAddress = OLED_I2C_ADDRESS;
int trayServoCurrentAngle = SERVO_HOME_ANGLE;
int trayServoTargetAngle = SERVO_HOME_ANGLE;
bool trayServoWasEnabled = false;
bool trayServoPwmAttached = false;
int trayServoLastSide = 0;
volatile bool trayServoFault = false;
bool buzzerPwmAttached = false;
bool heaterWarmupFault = false;
bool criticalHeatFault = false;
bool criticalLowTempFault = false;
bool heaterRelayWasOn = false;
float heaterRelayStartTemp = NAN;
float previousTemperature = NAN;
uint32_t heaterRelayStartedAt = 0;

enum FaultCode : uint8_t {
  FAULT_NONE = 0,
  FAULT_SENSOR,
  FAULT_CRITICAL_HEAT,
  FAULT_CRITICAL_COLD,
  FAULT_HEATER_WARMUP,
  FAULT_SERVO,
  FAULT_EMERGENCY_OFF,
};

FaultCode currentFaultCode(const IncubatorConfig& localConfig, uint8_t failures, bool servoFault, bool heatFault, bool coldFault, bool warmupFault) {
  if (failures >= MAX_SENSOR_FAILURES) return FAULT_SENSOR;
  if (heatFault) return FAULT_CRITICAL_HEAT;
  if (coldFault) return FAULT_CRITICAL_COLD;
  if (warmupFault) return FAULT_HEATER_WARMUP;
  if (servoFault) return FAULT_SERVO;
  if (localConfig.emergencyOff || localConfig.relayMode == "EMERGENCY_OFF") return FAULT_EMERGENCY_OFF;
  return FAULT_NONE;
}

const char* faultTitle(FaultCode fault) {
  switch (fault) {
    case FAULT_SENSOR: return "CHECK SENSOR";
    case FAULT_CRITICAL_HEAT: return "CHECK RELAY";
    case FAULT_CRITICAL_COLD: return "CRITICAL TEMP";
    case FAULT_HEATER_WARMUP: return "CHECK HEATER";
    case FAULT_SERVO: return "CHECK SERVO";
    case FAULT_EMERGENCY_OFF: return "EMERGENCY OFF";
    default: return "SYSTEM NORMAL";
  }
}

const char* faultDetail(FaultCode fault) {
  switch (fault) {
    case FAULT_SENSOR: return "DHT22 GPIO4";
    case FAULT_CRITICAL_HEAT: return "TEMP ABOVE 39C";
    case FAULT_CRITICAL_COLD: return "TEMP BELOW 33C";
    case FAULT_HEATER_WARMUP: return "NO TEMP RISE";
    case FAULT_SERVO: return "SERVO GPIO18";
    case FAULT_EMERGENCY_OFF: return "HEAT/FAN OFF";
    default: return "";
  }
}

void setRelay(bool on) {
  if (latestReading.relay != on) {
    Serial.printf("Relay %s\n", on ? "ON" : "OFF");
  }
  digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? on : !on);
  if (on && relayOnSince == 0) relayOnSince = millis();
  if (!on) relayOnSince = 0;
  latestReading.relay = on;
}

void setFanRelay(bool on) {
  if (latestReading.fanRelay != on) {
    Serial.printf("Fan relay %s\n", on ? "ON" : "OFF");
  }
  digitalWrite(PIN_FAN_RELAY, FAN_RELAY_ACTIVE_HIGH ? on : !on);
  latestReading.fanRelay = on;
}

uint16_t trayServoPulseUs(int angle) {
  angle = constrain(angle, -180, 180);
  int pulse = SERVO_MIN_US + ((int32_t)angle * (SERVO_MAX_US - SERVO_MIN_US)) / 180;
  return constrain(pulse, SERVO_NEGATIVE_LIMIT_US, SERVO_MAX_US);
}

uint32_t trayServoDuty(uint16_t pulseUs) {
  const uint32_t maxDuty = (1UL << SERVO_PWM_BITS) - 1;
  return (uint32_t)pulseUs * maxDuty / 20000UL;
}

bool writeTrayServoAngle(int angle) {
  angle = constrain(angle, -180, 180);
  const uint32_t duty = trayServoDuty(trayServoPulseUs(angle));
  if (!trayServoPwmAttached) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    if (!ledcAttachChannel(PIN_TRAY_SERVO, SERVO_PWM_HZ, SERVO_PWM_BITS, SERVO_PWM_CHANNEL)) {
      trayServoFault = true;
      Serial.printf("Tray servo PWM attach failed on GPIO%d\n", PIN_TRAY_SERVO);
      return false;
    }
#else
    ledcSetup(SERVO_PWM_CHANNEL, SERVO_PWM_HZ, SERVO_PWM_BITS);
    ledcAttachPin(PIN_TRAY_SERVO, SERVO_PWM_CHANNEL);
#endif
    trayServoPwmAttached = true;
  }
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_TRAY_SERVO, duty);
#else
  ledcWrite(SERVO_PWM_CHANNEL, duty);
#endif
  trayServoFault = false;
  return true;
}

void releaseTrayServo() {
  if (!trayServoPwmAttached) return;
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcDetach(PIN_TRAY_SERVO);
#else
  ledcDetachPin(PIN_TRAY_SERVO);
#endif
  pinMode(PIN_TRAY_SERVO, OUTPUT);
  digitalWrite(PIN_TRAY_SERVO, LOW);
  trayServoPwmAttached = false;
}

void setupTrayServo() {
  pinMode(PIN_TRAY_SERVO, OUTPUT);
  digitalWrite(PIN_TRAY_SERVO, LOW);
  trayServoPwmAttached = false;
  trayServoFault = false;
  Serial.printf("Tray servo signal idle on GPIO%d; no boot move command sent\n", PIN_TRAY_SERVO);
}

void setupBuzzer() {
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  buzzerPwmAttached = ledcAttachChannel(PIN_BUZZER, BUZZER_PWM_HZ, BUZZER_PWM_BITS, BUZZER_PWM_CHANNEL);
  if (!buzzerPwmAttached) {
    Serial.printf("Buzzer PWM attach failed on GPIO%d\n", PIN_BUZZER);
  }
#else
  ledcSetup(BUZZER_PWM_CHANNEL, BUZZER_PWM_HZ, BUZZER_PWM_BITS);
  ledcAttachPin(PIN_BUZZER, BUZZER_PWM_CHANNEL);
  buzzerPwmAttached = true;
#endif
}

void setBuzzer(bool on) {
  if (!buzzerPwmAttached) {
    digitalWrite(PIN_BUZZER, on ? HIGH : LOW);
    return;
  }
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_BUZZER, on ? BUZZER_MEDIUM_DUTY : 0);
#else
  ledcWrite(BUZZER_PWM_CHANNEL, on ? BUZZER_MEDIUM_DUTY : 0);
#endif
}

String isoTimestamp() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo, 25)) {
    char buffer[25];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buffer);
  }
  return "";
}

float heatIndexC(float temperature, float humidity) {
  return dht.computeHeatIndex(temperature, humidity, false);
}

bool oledAddressResponds(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

bool initDisplay() {
  if (oledAddressResponds(OLED_I2C_ADDRESS)) {
    activeOledAddress = OLED_I2C_ADDRESS;
  } else if (oledAddressResponds(OLED_I2C_FALLBACK_ADDRESS)) {
    activeOledAddress = OLED_I2C_FALLBACK_ADDRESS;
  } else {
    Serial.println("No I2C OLED found at 0x3C or 0x3D; continuing without display.");
    return false;
  }
  u8g2.setI2CAddress(activeOledAddress << 1);
  u8g2.begin();
  u8g2.setPowerSave(0);
  Serial.printf("OLED ready at 0x%02X on SDA=%u SCL=%u\n", activeOledAddress, PIN_DISPLAY_SDA, PIN_DISPLAY_SCL);
  return true;
}

void drawCenteredText(const char* text, uint8_t y, const uint8_t* font) {
  u8g2.setFont(font);
  int16_t width = u8g2.getStrWidth(text);
  int16_t x = max(0, (128 - width) / 2);
  u8g2.drawStr(x, y, text);
}

void drawBootSplash() {
  for (uint8_t frame = 0; frame <= 48; frame += 2) {
    u8g2.clearBuffer();
    u8g2.drawFrame(4, 4, 120, 56);
    u8g2.drawRFrame(8, 8, 112, 48, 4);
    drawCenteredText("SMART INCUBATOR", 20, u8g2_font_6x10_tf);
    u8g2.setFont(u8g2_font_logisoso18_tf);
    const char* brand = "NETRUE LTD";
    int16_t brandWidth = u8g2.getStrWidth(brand);
    int16_t brandX = max(0, (128 - brandWidth) / 2);
    u8g2.drawStr(brandX, 43, brand);
    u8g2.drawFrame(20, 51, 88, 6);
    u8g2.drawBox(22, 53, frame * 84 / 48, 2);
    u8g2.sendBuffer();
    delay(45);
  }
  for (uint8_t pulse = 0; pulse < 3; pulse++) {
    u8g2.clearBuffer();
    drawCenteredText("NETRUE LTD", 36, u8g2_font_logisoso20_tf);
    u8g2.sendBuffer();
    delay(170);
    u8g2.clearBuffer();
    drawCenteredText("NETRUE LTD", 36, u8g2_font_logisoso18_tf);
    u8g2.sendBuffer();
    delay(120);
  }
}

void applyRelayControl() {
  bool relay = latestReading.relay;
  if (criticalHeatFault) {
    setRelay(false);
    return;
  }
  if (config.emergencyOff || config.relayMode == "EMERGENCY_OFF") {
    setRelay(false);
    return;
  }
  if (sensorFailures >= MAX_SENSOR_FAILURES) {
    setRelay(false);
    return;
  }
  if (config.relayMode == "MANUAL") {
    setRelay(config.manualRelay);
    return;
  }
  if (!isnan(latestReading.temperature)) {
    const float lower = config.targetTemp - config.tolerance;
    const float upper = config.targetTemp + config.tolerance;
    if (latestReading.temperature < lower) {
      relay = true;
    } else if (latestReading.temperature > upper) {
      relay = false;
    }
  }
  setRelay(relay);
}

void applyFanControl() {
  if (criticalHeatFault) {
    setFanRelay(true);
    return;
  }
  if (config.emergencyOff || config.relayMode == "EMERGENCY_OFF" || sensorFailures >= MAX_SENSOR_FAILURES || isnan(latestReading.humidity)) {
    setFanRelay(false);
    return;
  }
  if (latestReading.humidity > config.targetHumidity) {
    setFanRelay(true);
    return;
  }
  setFanRelay(latestReading.relay);
}

void updateHeatingFaults(float temperature) {
  if (isnan(temperature)) return;

  const uint32_t now = millis();
  const bool relayOn = latestReading.relay;
  if (relayOn && !heaterRelayWasOn) {
    heaterRelayStartedAt = now;
    heaterRelayStartTemp = temperature;
    heaterWarmupFault = false;
  } else if (!relayOn) {
    heaterRelayStartedAt = 0;
    heaterRelayStartTemp = NAN;
    heaterWarmupFault = false;
  }
  heaterRelayWasOn = relayOn;

  if (temperature <= CRITICAL_LOW_TEMP_C) {
    criticalLowTempFault = true;
  } else if (temperature >= CRITICAL_LOW_TEMP_RESET_C) {
    criticalLowTempFault = false;
  }

  if (relayOn && heaterRelayStartedAt > 0 && now - heaterRelayStartedAt >= HEATER_WARMUP_CHECK_MS) {
    const bool stillFalling = !isnan(previousTemperature) && temperature <= previousTemperature - HEATER_FALLING_DELTA_C;
    heaterWarmupFault = temperature <= HEATER_LOW_ALARM_TEMP_C && stillFalling;
  }

  if (!isnan(previousTemperature)) {
    const bool stillRisingHot = temperature >= CRITICAL_TEMP_C && temperature >= previousTemperature + CRITICAL_TEMP_RISE_C;
    if (stillRisingHot) {
      criticalHeatFault = true;
      setRelay(false);
      setFanRelay(true);
    } else if (temperature < CRITICAL_TEMP_RESET_C) {
      criticalHeatFault = false;
    }
  } else if (temperature < CRITICAL_TEMP_RESET_C) {
    criticalHeatFault = false;
  }
  previousTemperature = temperature;
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED || millis() - lastWifiAttempt < WIFI_RETRY_INTERVAL_MS) return;
  lastWifiAttempt = millis();
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting WiFi SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

int postJson(const String& endpoint, const String& payload) {
  if (WiFi.status() != WL_CONNECTED) return -1;
  HTTPClient http;
  http.begin(String(BACKEND_URL) + endpoint);
  http.setTimeout(1500);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);
  Serial.printf("POST %s -> HTTP %d\n", endpoint.c_str(), code);
  http.end();
  return code;
}

bool httpSuccess(int code) {
  return code >= 200 && code < 300;
}

void applyRemoteConfig(JsonDocument& doc) {
  String updatedAt = doc["updated_at"] | "";
  if (updatedAt.length() && config.updatedAt.length() && updatedAt <= config.updatedAt) return;
  config.targetTemp = doc["target_temperature"] | config.targetTemp;
  config.targetHumidity = doc["target_humidity"] | config.targetHumidity;
  config.tolerance = doc["tolerance"] | config.tolerance;
  config.hysteresis = doc["hysteresis"] | config.hysteresis;
  config.tempOffset = doc["temperature_offset"] | config.tempOffset;
  config.humidityOffset = doc["humidity_offset"] | config.humidityOffset;
  config.manualRelay = doc["manual_relay"] | config.manualRelay;
  config.emergencyOff = doc["emergency_off"] | config.emergencyOff;
  config.trayServoEnabled = doc["tray_servo_enabled"] | config.trayServoEnabled;
  config.trayServoAngle = constrain((int)(doc["tray_servo_angle"] | config.trayServoAngle), 0, 180);
  config.trayServoIntervalMinutes = constrain((int)(doc["tray_servo_interval_minutes"] | config.trayServoIntervalMinutes), 1, 720);
  config.trayServoSpeedDps = constrain((int)(doc["tray_servo_speed_dps"] | config.trayServoSpeedDps), 1, 30);
  config.relayMode = String((const char*)(doc["relay_mode"] | config.relayMode.c_str()));
  config.relayMode.trim();
  config.relayMode.toUpperCase();
  config.updatedAt = updatedAt;
  saveConfig(config);
}

void fetchCommands() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String(BACKEND_URL) + "/api/settings");
  http.setTimeout(1500);
  int code = http.GET();
  Serial.printf("GET /api/settings -> HTTP %d\n", code);
  if (code == 200) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, http.getString());
    if (!error) applyRemoteConfig(doc);
  }
  http.end();
}

String readingJson(const Reading& reading) {
  JsonDocument doc;
  doc["temperature"] = reading.temperature;
  doc["humidity"] = reading.humidity;
  doc["heat_index"] = reading.heatIndex;
  doc["relay"] = reading.relay;
  doc["fan_relay"] = reading.fanRelay;
  doc["wifi"] = WiFi.status() == WL_CONNECTED;
  doc["sync_status"] = reading.syncStatus;
  if (reading.timestamp.length() > 0) {
    doc["timestamp"] = reading.timestamp;
  }
  String out;
  serializeJson(doc, out);
  return out;
}

void sensorTask(void*) {
  for (;;) {
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    Reading sampledReading;
    bool shouldSaveHistory = false;
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    if (isnan(humidity) || isnan(temperature)) {
      sensorFailures++;
      if (sensorFailures >= MAX_SENSOR_FAILURES) {
        setRelay(false);
        setFanRelay(false);
      }
    } else {
      sensorFailures = 0;
      latestReading.temperature = temperature + config.tempOffset;
      latestReading.humidity = humidity + config.humidityOffset;
      latestReading.heatIndex = heatIndexC(latestReading.temperature, latestReading.humidity);
      latestReading.timestamp = isoTimestamp();
      latestReading.wifi = WiFi.status() == WL_CONNECTED;
      latestReading.syncStatus = latestReading.wifi ? "synced" : "queued";
      applyRelayControl();
      applyFanControl();
      updateHeatingFaults(latestReading.temperature);
      sampledReading = latestReading;
      pendingUpload = latestReading;
      pendingUploadReady = true;
      if (millis() - lastHistoryAppend >= HISTORY_INTERVAL_MS) {
        lastHistoryAppend = millis();
        shouldSaveHistory = true;
      }
    }
    xSemaphoreGive(stateMutex);
    if (!isnan(humidity) && !isnan(temperature)) {
      Serial.printf(
        "DHT22 %.1f C %.1f%% heat=%s fan=%s\n",
        sampledReading.temperature,
        sampledReading.humidity,
        sampledReading.relay ? "ON" : "OFF",
        sampledReading.fanRelay ? "ON" : "OFF"
      );
      if (shouldSaveHistory) appendReading(sampledReading);
    }
    vTaskDelay(pdMS_TO_TICKS(SENSOR_INTERVAL_MS));
  }
}

void displayTask(void*) {
  uint8_t page = 0;
  uint32_t pageShownAt = millis();
  uint32_t lastRenderAt = 0;
  uint32_t lastButtonChangeAt = 0;
  bool lastButtonRaw = digitalRead(PIN_PAGE_BUTTON) == LOW;
  bool buttonPressed = lastButtonRaw;
  FaultCode lastRenderedFault = FAULT_NONE;
  uint8_t lastRenderedPage = 255;
  char line[32];
  for (;;) {
    if (!displayReady) {
      vTaskDelay(pdMS_TO_TICKS(DISPLAY_TASK_INTERVAL_MS));
      continue;
    }

    const uint32_t now = millis();
    bool needsRedraw = false;
    bool buttonRaw = digitalRead(PIN_PAGE_BUTTON) == LOW;
    if (buttonRaw != lastButtonRaw) {
      lastButtonRaw = buttonRaw;
      lastButtonChangeAt = now;
    }
    if (now - lastButtonChangeAt >= BUTTON_DEBOUNCE_MS && buttonRaw != buttonPressed) {
      buttonPressed = buttonRaw;
      if (buttonPressed) {
        page = (page + 1) % 4;
        pageShownAt = now;
        needsRedraw = true;
      }
    }
    if (page != 0 && now - pageShownAt >= DISPLAY_RETURN_TIMEOUT_MS) {
      page = 0;
      needsRedraw = true;
    }

    xSemaphoreTake(stateMutex, portMAX_DELAY);
    Reading reading = latestReading;
    IncubatorConfig localConfig = config;
    uint8_t failures = sensorFailures;
    xSemaphoreGive(stateMutex);
    FaultCode fault = currentFaultCode(localConfig, failures, trayServoFault, criticalHeatFault, criticalLowTempFault, heaterWarmupFault);

    if (page != lastRenderedPage || fault != lastRenderedFault || now - lastRenderAt >= DISPLAY_REFRESH_MS) {
      needsRedraw = true;
    }
    if (!needsRedraw) {
      vTaskDelay(pdMS_TO_TICKS(DISPLAY_TASK_INTERVAL_MS));
      continue;
    }

    u8g2.clearBuffer();
    if (fault != FAULT_NONE) {
      drawCenteredText(faultTitle(fault), 14, u8g2_font_7x14B_tf);
      u8g2.setFont(u8g2_font_logisoso16_tf);
      drawCenteredText("FAULT", 39, u8g2_font_logisoso16_tf);
      drawCenteredText(faultDetail(fault), 60, u8g2_font_7x14B_tf);
    } else if (page == 0) {
      drawCenteredText("INCUBATOR LIVE", 10, u8g2_font_6x10_tf);
      u8g2.setFont(u8g2_font_logisoso22_tf);
      snprintf(line, sizeof(line), "%.1f C", reading.temperature);
      u8g2.drawStr(11, 39, isnan(reading.temperature) ? "--.- C" : line);
      u8g2.setFont(u8g2_font_7x14B_tf);
      snprintf(line, sizeof(line), "Humidity %.0f%%", reading.humidity);
      u8g2.drawStr(16, 60, isnan(reading.humidity) ? "Humidity --%" : line);
    } else if (page == 1) {
      drawCenteredText("SYSTEM", 10, u8g2_font_6x10_tf);
      u8g2.setFont(u8g2_font_7x14B_tf);
      snprintf(line, sizeof(line), "Heat:%s Fan:%s", reading.relay ? "ON" : "OFF", reading.fanRelay ? "ON" : "OFF");
      u8g2.drawStr(0, 28, line);
      snprintf(line, sizeof(line), "WiFi: %s", WiFi.status() == WL_CONNECTED ? "OK" : "OFFLINE");
      u8g2.drawStr(0, 43, line);
      String ip = WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "No IP";
      u8g2.drawStr(0, 60, ip.c_str());
    } else if (page == 2) {
      drawCenteredText("CONTROL", 10, u8g2_font_6x10_tf);
      u8g2.setFont(u8g2_font_7x14B_tf);
      snprintf(line, sizeof(line), "Target: %.1f C", localConfig.targetTemp);
      u8g2.drawStr(0, 28, line);
      snprintf(line, sizeof(line), "Mode: %s", localConfig.relayMode.c_str());
      u8g2.drawStr(0, 43, line);
      u8g2.drawStr(0, 60, failures >= MAX_SENSOR_FAILURES ? "SENSOR FAIL" : "System Normal");
    } else {
      drawCenteredText("TRAY SERVO", 10, u8g2_font_6x10_tf);
      u8g2.setFont(u8g2_font_7x14B_tf);
      snprintf(line, sizeof(line), "GPIO18: %s", localConfig.trayServoEnabled ? "ON" : "OFF");
      u8g2.drawStr(0, 28, line);
      snprintf(line, sizeof(line), "-%d 0 +%d", localConfig.trayServoAngle, localConfig.trayServoAngle);
      u8g2.drawStr(0, 43, line);
      snprintf(line, sizeof(line), "Every: %d min", localConfig.trayServoIntervalMinutes);
      u8g2.drawStr(0, 60, line);
    }
    u8g2.sendBuffer();
    lastRenderAt = now;
    lastRenderedPage = page;
    lastRenderedFault = fault;
    vTaskDelay(pdMS_TO_TICKS(DISPLAY_TASK_INTERVAL_MS));
  }
}

void trayServoTask(void*) {
  uint32_t endpointReachedAt = 0;
  uint32_t lastStepAt = 0;
  int lastConfiguredAngle = -1;
  for (;;) {
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    IncubatorConfig localConfig = config;
    xSemaphoreGive(stateMutex);

    const uint32_t now = millis();
    const bool enabled = localConfig.trayServoEnabled;
    const int configuredAngle = constrain(localConfig.trayServoAngle, 0, 180);
    const uint32_t intervalMs = max(60000UL, (uint32_t)localConfig.trayServoIntervalMinutes * 60000UL);
    const uint32_t stepMs = max(33UL, 1000UL / (uint32_t)max(1, localConfig.trayServoSpeedDps));

    if (!enabled) {
      trayServoWasEnabled = false;
      releaseTrayServo();
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }

    if (!trayServoWasEnabled || configuredAngle != lastConfiguredAngle) {
      trayServoTargetAngle = trayServoCurrentAngle;
      trayServoLastSide = trayServoCurrentAngle > 0 ? 1 : (trayServoCurrentAngle < 0 ? -1 : 0);
      lastConfiguredAngle = configuredAngle;
      endpointReachedAt = now;
      trayServoWasEnabled = true;
      Serial.printf(
        "Tray servo enabled: -%d/0/+%d degrees, interval=%d min, speed=%d dps\n",
        configuredAngle,
        configuredAngle,
        localConfig.trayServoIntervalMinutes,
        localConfig.trayServoSpeedDps
      );
    }

    if (trayServoCurrentAngle != trayServoTargetAngle && now - lastStepAt >= stepMs) {
      trayServoCurrentAngle += trayServoCurrentAngle < trayServoTargetAngle ? 1 : -1;
      if (!writeTrayServoAngle(trayServoCurrentAngle)) {
        vTaskDelay(pdMS_TO_TICKS(500));
        continue;
      }
      lastStepAt = now;
      if (trayServoCurrentAngle == trayServoTargetAngle) {
        endpointReachedAt = now;
        saveTrayServoPosition(trayServoCurrentAngle);
        Serial.printf("Tray servo reached %d degrees\n", trayServoCurrentAngle);
      }
    } else if (trayServoCurrentAngle == trayServoTargetAngle) {
      if (endpointReachedAt == 0) endpointReachedAt = now;
      if (trayServoPwmAttached && now - lastStepAt >= SERVO_RELEASE_DELAY_MS) {
        releaseTrayServo();
      }
      if (trayServoTargetAngle == SERVO_HOME_ANGLE) {
        if (trayServoLastSide == 0) {
          if (now - endpointReachedAt >= intervalMs) {
            trayServoTargetAngle = configuredAngle;
            endpointReachedAt = 0;
            Serial.printf("Tray servo target %d degrees\n", trayServoTargetAngle);
          }
        } else {
          trayServoTargetAngle = trayServoLastSide > 0 ? -configuredAngle : configuredAngle;
          endpointReachedAt = 0;
          Serial.printf("Tray servo target %d degrees\n", trayServoTargetAngle);
        }
      } else if (now - endpointReachedAt >= intervalMs) {
        trayServoLastSide = trayServoTargetAngle > 0 ? 1 : -1;
        trayServoTargetAngle = SERVO_HOME_ANGLE;
        endpointReachedAt = 0;
        Serial.printf("Tray servo target %d degrees\n", trayServoTargetAngle);
      }
    }

    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void alarmTask(void*) {
  FaultCode activeAlarmFault = FAULT_NONE;
  uint32_t alarmStartedAt = 0;
  for (;;) {
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    IncubatorConfig localConfig = config;
    uint8_t failures = sensorFailures;
    xSemaphoreGive(stateMutex);

    const FaultCode fault = currentFaultCode(localConfig, failures, trayServoFault, criticalHeatFault, criticalLowTempFault, heaterWarmupFault);
    const uint32_t now = millis();
    const bool holdingCriticalColdAlarm =
      fault == FAULT_NONE &&
      activeAlarmFault == FAULT_CRITICAL_COLD &&
      now - alarmStartedAt < CRITICAL_TEMP_ALARM_DURATION_MS;
    if (fault == FAULT_NONE && !holdingCriticalColdAlarm) {
      activeAlarmFault = FAULT_NONE;
      setBuzzer(false);
      digitalWrite(PIN_STATUS_LED, HIGH);
      vTaskDelay(pdMS_TO_TICKS(50));
      continue;
    }

    const FaultCode soundFault = holdingCriticalColdAlarm ? activeAlarmFault : fault;
    if (soundFault != activeAlarmFault) {
      activeAlarmFault = soundFault;
      alarmStartedAt = now;
      Serial.printf("Alarm started: %s\n", faultTitle(soundFault));
    }

    const bool ledOn = ((now / STATUS_LED_BLINK_MS) % 2) == 0;
    digitalWrite(PIN_STATUS_LED, ledOn ? HIGH : LOW);

    const uint32_t alarmDuration = activeAlarmFault == FAULT_CRITICAL_COLD ? CRITICAL_TEMP_ALARM_DURATION_MS : ALARM_DURATION_MS;
    const bool criticalColdStillActive = activeAlarmFault == FAULT_CRITICAL_COLD && fault == FAULT_CRITICAL_COLD;
    const bool alarmWindowActive = criticalColdStillActive || now - alarmStartedAt < alarmDuration;
    if (alarmWindowActive) {
      const uint32_t phase = (now - alarmStartedAt) % (ALARM_BEEP_ON_MS + ALARM_BEEP_OFF_MS);
      setBuzzer(phase < ALARM_BEEP_ON_MS);
    } else {
      setBuzzer(false);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void syncTask(void*) {
  for (;;) {
    connectWifi();
    if (WiFi.status() == WL_CONNECTED && millis() - lastWifiLog > 10000) {
      lastWifiLog = millis();
      Serial.print("WiFi connected. IP: ");
      Serial.println(WiFi.localIP());
      Serial.print("Backend URL: ");
      Serial.println(BACKEND_URL);
    }
    Reading uploadReading;
    bool hasUpload = false;
    xSemaphoreTake(stateMutex, portMAX_DELAY);
    if (pendingUploadReady) {
      uploadReading = pendingUpload;
      pendingUploadReady = false;
      hasUpload = true;
    }
    xSemaphoreGive(stateMutex);

    if (hasUpload) {
      uploadReading.wifi = WiFi.status() == WL_CONNECTED;
      uploadReading.syncStatus = uploadReading.wifi ? "synced" : "queued";
      if (WiFi.status() == WL_CONNECTED) {
        if (!httpSuccess(postJson("/api/environment", readingJson(uploadReading)))) {
          uploadReading.syncStatus = "queued";
          enqueueReading(uploadReading);
        }
      } else {
        enqueueReading(uploadReading);
      }
    }

    if (WiFi.status() == WL_CONNECTED) {
      configTime(0, 0, "pool.ntp.org", "time.nist.gov");
      fetchCommands();
      String line;
      uint8_t sent = 0;
      while (sent < 8 && peekQueuedReading(line)) {
        int code = postJson("/api/environment", line);
        if (httpSuccess(code)) {
          popQueuedReading();
          sent++;
        } else if (code >= 400 && code < 500) {
          Serial.printf("Dropping invalid queued reading after HTTP %d\n", code);
          popQueuedReading();
          sent++;
        } else {
          break;
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(SYNC_INTERVAL_MS));
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_PAGE_BUTTON, INPUT_PULLUP);
  digitalWrite(PIN_STATUS_LED, HIGH);
  setupBuzzer();
  setBuzzer(false);
  setRelay(false);
  setFanRelay(false);
  storageBegin();
  config = loadConfig();
  trayServoCurrentAngle = constrain(loadTrayServoPosition(), -180, 180);
  trayServoTargetAngle = trayServoCurrentAngle;
  setupTrayServo();
  Wire.begin(PIN_DISPLAY_SDA, PIN_DISPLAY_SCL);
  Wire.setClock(OLED_I2C_CLOCK_HZ);
  displayReady = initDisplay();
  if (displayReady) {
    drawBootSplash();
  }
  dht.begin();
  stateMutex = xSemaphoreCreateMutex();
#if ESP_IDF_VERSION_MAJOR >= 5
  const esp_task_wdt_config_t wdtConfig = {
    .timeout_ms = 12000,
    .idle_core_mask = (1 << portNUM_PROCESSORS) - 1,
    .trigger_panic = true,
  };
  esp_task_wdt_init(&wdtConfig);
#else
  esp_task_wdt_init(12, true);
#endif
  connectWifi();
  xTaskCreatePinnedToCore(sensorTask, "sensor", 4096, nullptr, 2, nullptr, 1);
  xTaskCreatePinnedToCore(syncTask, "sync", 8192, nullptr, 1, nullptr, 0);
  xTaskCreatePinnedToCore(displayTask, "display", 4096, nullptr, 1, nullptr, 1);
  xTaskCreatePinnedToCore(trayServoTask, "tray-servo", 3072, nullptr, 1, nullptr, 1);
  xTaskCreatePinnedToCore(alarmTask, "alarm", 2048, nullptr, 1, nullptr, 1);
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}

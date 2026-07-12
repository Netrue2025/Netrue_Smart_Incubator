#pragma once

#include <Arduino.h>
#include <DHT.h>

#if __has_include("secrets.h")
#include "secrets.h"
#elif __has_include("../secrets.h")
#include "../secrets.h"
#else
#include "secrets.example.h"
#endif

constexpr uint8_t PIN_DISPLAY_SDA = 21;
constexpr uint8_t PIN_DISPLAY_SCL = 22;
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;
constexpr uint8_t OLED_I2C_FALLBACK_ADDRESS = 0x3D;
constexpr uint32_t OLED_I2C_CLOCK_HZ = 100000;
constexpr uint8_t PIN_DHT22 = 4;
constexpr uint8_t PIN_RELAY = 15;
constexpr uint8_t PIN_FAN_RELAY = 23;
constexpr uint8_t PIN_TRAY_SERVO = 18;
constexpr uint8_t PIN_BUZZER = 25;
constexpr uint8_t PIN_STATUS_LED = 26;
constexpr uint8_t PIN_PAGE_BUTTON = 27;

constexpr uint8_t DHT_TYPE = DHT22;
constexpr bool RELAY_ACTIVE_HIGH = false;
constexpr bool FAN_RELAY_ACTIVE_HIGH = false;
constexpr uint8_t SERVO_PWM_CHANNEL = 7;
constexpr uint8_t BUZZER_PWM_CHANNEL = 6;
constexpr uint16_t SERVO_PWM_HZ = 50;
constexpr uint8_t SERVO_PWM_BITS = 16;
constexpr uint16_t BUZZER_PWM_HZ = 1800;
constexpr uint8_t BUZZER_PWM_BITS = 8;
constexpr uint8_t BUZZER_MEDIUM_DUTY = 80;
constexpr uint16_t SERVO_MIN_US = 1000;
constexpr uint16_t SERVO_MAX_US = 2000;
constexpr uint16_t SERVO_NEGATIVE_LIMIT_US = 700;
constexpr uint8_t SERVO_HOME_ANGLE = 0;
constexpr uint32_t SERVO_RELEASE_DELAY_MS = 700;
constexpr uint32_t SENSOR_INTERVAL_MS = 2500;
constexpr uint32_t DISPLAY_REFRESH_MS = 1000;
constexpr uint32_t DISPLAY_TASK_INTERVAL_MS = 50;
constexpr uint32_t DISPLAY_RETURN_TIMEOUT_MS = 5000;
constexpr uint32_t BUTTON_DEBOUNCE_MS = 50;
constexpr uint32_t ALARM_DURATION_MS = 30000;
constexpr uint32_t CRITICAL_TEMP_ALARM_DURATION_MS = 120000;
constexpr uint32_t ALARM_BEEP_ON_MS = 350;
constexpr uint32_t ALARM_BEEP_OFF_MS = 650;
constexpr uint32_t STATUS_LED_BLINK_MS = 250;
constexpr uint32_t HEATER_WARMUP_CHECK_MS = 30000;
constexpr float HEATER_MIN_RISE_C = 0.1f;
constexpr float HEATER_TEMP_DROP_C = 0.2f;
constexpr float HEATER_LOW_ALARM_TEMP_C = 36.9f;
constexpr float HEATER_FALLING_DELTA_C = 0.05f;
constexpr float CRITICAL_TEMP_C = 39.0f;
constexpr float CRITICAL_TEMP_RISE_C = 0.1f;
constexpr float CRITICAL_TEMP_RESET_C = 38.5f;
constexpr float CRITICAL_LOW_TEMP_C = 33.0f;
constexpr float CRITICAL_LOW_TEMP_RESET_C = 34.0f;
constexpr uint32_t SYNC_INTERVAL_MS = 5000;
constexpr uint32_t HTTP_TIMEOUT_MS = 8000;
constexpr uint32_t HISTORY_INTERVAL_MS = 30000;
constexpr uint32_t WIFI_RETRY_INTERVAL_MS = 10000;
constexpr uint8_t MAX_SENSOR_FAILURES = 3;
constexpr uint32_t RELAY_TIMEOUT_MS = 15UL * 60UL * 1000UL;
constexpr size_t MAX_QUEUE_BYTES = 196000;

struct IncubatorConfig {
  float targetTemp = 37.5f;
  float targetHumidity = 60.0f;
  float tolerance = 0.3f;
  float hysteresis = 0.2f;
  float tempOffset = 0.0f;
  float humidityOffset = 0.0f;
  bool manualRelay = false;
  bool emergencyOff = false;
  bool trayServoEnabled = false;
  int trayServoAngle = 45;
  int trayServoIntervalMinutes = 120;
  int trayServoSpeedDps = 6;
  String wifiSsid = "";
  String wifiPassword = "";
  bool wifiScanRequested = false;
  bool wifiConnectRequested = false;
  String relayMode = "AUTO";
  String updatedAt = "";
};

struct Reading {
  float temperature = NAN;
  float humidity = NAN;
  float heatIndex = NAN;
  bool relay = false;
  bool fanRelay = false;
  bool wifi = false;
  String syncStatus = "queued";
  String timestamp = "";
};

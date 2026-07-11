# Firmware Flash Guide

## Arduino IDE

### OLED-Only Test

If the screen is not coming up, flash this simple test first:

```text
firmware/arduino/OledSsd1306Test/OledSsd1306Test.ino
```

It is configured for common 0.95/0.96/1.3 inch 128x64 I2C OLED modules:

- SDA: GPIO21
- SCL: GPIO22
- Address: `0x3C`, with `0x3D` fallback
- I2C clock: `100kHz`
- Drivers tested: `SSD1306` and `SH1106`

Open Serial Monitor at `115200` baud. If it says no OLED was found, check VCC, GND, SDA, and SCL. Do not wire the OLED to GPIO12 on a classic ESP32 DevKit; GPIO12 is a boot strapping pin and can cause `invalid header: 0xffffffff` boot failures.

### Full Incubator Firmware

Use this sketch:

```text
firmware/arduino/SmartIncubatorV2/SmartIncubatorV2.ino
```

1. Open Arduino IDE.
2. Install the ESP32 board package by Espressif Systems.
3. Install these libraries from Library Manager:
   - `DHT sensor library` by Adafruit
   - `Adafruit Unified Sensor`
   - `U8g2` by olikraus
   - `ArduinoJson` version 7.x
4. Open `firmware/arduino/SmartIncubatorV2/SmartIncubatorV2.ino`.
5. Copy `firmware/arduino/SmartIncubatorV2/secrets.example.h` to `firmware/arduino/SmartIncubatorV2/secrets.h`, or keep one shared file at `firmware/arduino/secrets.h`.
6. Edit `secrets.h` with WiFi credentials and backend URL.
7. Select your ESP32 Dev Module board and upload.

## PlatformIO

1. Install PlatformIO.
2. Connect the ESP32 DevKit over USB.
3. Copy `include/secrets.example.h` to `include/secrets.h`.
4. Set WiFi credentials and backend URL.
5. Flash:

```powershell
cd firmware
pio run -t upload
pio device monitor
```

The serial monitor runs at `115200` baud.

## Expected Boot

- OLED plays the animated `NETRUE LTD` splash, then stays on the main temperature/humidity page.
- GPIO27 page button advances through system, control, and tray servo pages; they return to the main page after 5 seconds.
- GPIO26 status LED stays ON while powered and blinks during detected faults.
- GPIO25 buzzer beeps for 30 seconds when a firmware-detectable fault starts.
- Heater trend faults show `CHECK HEATER` when relay-on heating does not raise temperature after 30 seconds, and `CHECK RELAY` when temperature reaches 39.0 C and keeps rising.
- Relay starts OFF.
- DHT22 readings begin every 2.5 seconds.
- If WiFi is unavailable, readings are stored in SPIFFS and replayed after reconnect.

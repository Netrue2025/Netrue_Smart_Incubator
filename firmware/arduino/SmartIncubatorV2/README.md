# SmartIncubatorV2 Arduino IDE Sketch

Open `SmartIncubatorV2.ino` in Arduino IDE.

## Required Libraries

Install these from Arduino IDE Library Manager:

- `DHT sensor library` by Adafruit
- `Adafruit Unified Sensor`
- `U8g2` by olikraus
- `ArduinoJson` version 7.x

## Board Setup

1. Install the ESP32 board package by Espressif Systems.
2. Select your ESP32 Dev Module board.
3. Copy `secrets.example.h` to `secrets.h` inside this same `SmartIncubatorV2` sketch folder, or keep one shared file at `firmware/arduino/secrets.h`.
4. Edit `secrets.h` with your WiFi credentials and backend URL.
5. Upload `SmartIncubatorV2.ino`.

## Pins

- OLED SDA: GPIO21
- OLED SCL: GPIO22
- DHT22 DATA: GPIO4
- Heater relay IN: GPIO15
- Tray servo signal: GPIO18
- Fan relay IN: GPIO23
- Buzzer signal: GPIO25
- Status LED: GPIO26
- Page button: GPIO27 to GND

The GPIO27 button uses the ESP32 internal pull-up. Each press advances the OLED through system, control, and tray servo pages; any non-main page returns to the main temperature/humidity page after 5 seconds.

The GPIO26 LED stays ON while powered and blinks during a detected fault. The GPIO25 buzzer beeps for 30 seconds after repeated DHT22 failure, heater temperature-trend errors, servo PWM attach failure, or emergency-off mode. A critical low-temperature warning at 33.0 C sounds for at least 2 minutes. Faults display on the OLED with messages such as `CHECK HEATER`, `CHECK RELAY`, `CRITICAL TEMP`, or `CHECK SERVO`.

`CHECK HEATER` appears only after the heater relay has been ON for 30 seconds and temperature is at or below 36.9 C while still falling. `CHECK RELAY` appears if temperature reaches 39.0 C and is still rising; the firmware commands the heater relay OFF and the fan relay ON. `CRITICAL TEMP` appears if temperature reaches 33.0 C and clears after recovery to 34.0 C.

Do not wire the OLED to GPIO12 on a classic ESP32 DevKit. GPIO12 is a boot strapping pin and can cause `invalid header: 0xffffffff` boot failures if the display pulls it during reset.

# Smart AI Incubator V2 Firmware

PlatformIO firmware for an ESP32 DevKit using DHT22, SSD1306 128x64 OLED with U8g2, relay-controlled heating, offline local storage, and automatic sync to the FastAPI backend.

## Pinout

| Function | Pin |
| --- | --- |
| SSD1306 OLED SDA | GPIO21 |
| SSD1306 OLED SCL | GPIO22 |
| DHT22 Data | GPIO4 |
| Relay Signal | GPIO15 |
| Tray Servo Signal | GPIO18 |
| Fan Relay Signal | GPIO23 |
| Buzzer Signal | GPIO25 |
| Status LED | GPIO26 |
| Page Button | GPIO27 to GND |

## Setup

### Arduino IDE

For OLED hardware testing only, open:

```text
firmware/arduino/OledSsd1306Test/OledSsd1306Test.ino
```

The OLED diagnostic targets common 0.95/0.96/1.3 inch 128x64 I2C OLED modules on SDA `GPIO21` and SCL `GPIO22`, checks `0x3C`/`0x3D`, and alternates SSD1306/SH1106 pages. Use the driver that appears correctly on the screen in the full incubator firmware.

Open:

```text
firmware/arduino/SmartIncubatorV2/SmartIncubatorV2.ino
```

Install `DHT sensor library`, `Adafruit Unified Sensor`, `U8g2`, and `ArduinoJson` 7.x from Library Manager. Copy `firmware/arduino/SmartIncubatorV2/secrets.example.h` to `firmware/arduino/SmartIncubatorV2/secrets.h` before uploading.

### PlatformIO

1. Copy `include/secrets.example.h` to `include/secrets.h`.
2. Set WiFi credentials and `BACKEND_URL`.
3. Flash:

```powershell
pio run -t upload
pio device monitor
```

## Safety

- DHT22 is sampled every 2.5 seconds.
- Relay AUTO mode turns ON below `target temperature - tolerance` and turns OFF above `target temperature + tolerance`.
- Emergency OFF and repeated DHT22 failures force the relay OFF.
- Repeated DHT22 failures, heater temperature-trend errors, servo PWM attach failure, or emergency-off mode show a fault message on the OLED and start the buzzer/LED alarm.
- If the heater relay is ON for 30 seconds, the OLED waits until temperature is at or below 36.9 C and still falling before showing `CHECK HEATER`.
- If temperature reaches 39.0 C and is still rising, the OLED shows `CHECK RELAY`, the heater relay is commanded OFF, the fan relay is commanded ON, and the alarm starts.
- If temperature reaches 33.0 C, the OLED shows `CRITICAL TEMP`; the buzzer sounds for at least 2 minutes and continues longer while temperature remains critically low.
- A watchdog is enabled.
- Telemetry is stored in SPIFFS and queued when WiFi/backend is unavailable.

## Display

The firmware uses the working driver form:

```cpp
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
```

On power-up the OLED plays an animated `NETRUE LTD` splash before showing the main temperature/humidity page. Press the GPIO27 page button to show system, control, and tray servo pages. Any non-main page returns to temperature/humidity after 5 seconds. If a detected fault occurs, the OLED shows a message such as `CHECK HEATER`, `CHECK RELAY`, or `CHECK SERVO` until the fault clears. If no OLED is detected at `0x3C` or `0x3D`, the firmware continues running without the display.

## Alarm Outputs

The GPIO26 status LED stays ON while the system is powered. During a detected fault it blinks repeatedly. The GPIO25 buzzer beeps for 30 seconds using a medium PWM duty setting, except the 33.0 C critical low-temperature warning which sounds for at least 2 minutes. Passive buzzers respond best to this. Active buzzer modules may need a resistor, transistor driver, or onboard trim pot for volume control.

Heater and relay faults are inferred from temperature trend. For direct proof of physical fan, relay, or servo movement, add feedback hardware such as current sensing, limit switches, or tachometer feedback.

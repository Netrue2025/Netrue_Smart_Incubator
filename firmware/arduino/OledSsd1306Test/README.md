# 128x64 OLED Diagnostic Sketch

Open `OledSsd1306Test.ino` in Arduino IDE to test 0.95, 0.96, and 1.3 inch 128x64 I2C OLED modules. The sketch is diagnostic: it scans the I2C bus and alternates between SSD1306 and SH1106 drivers. Many 1.3 inch 128x64 OLED modules use SH1106.

## Libraries

Install `U8g2` by olikraus from Arduino IDE Library Manager.

## Default Wiring

- OLED VCC: 3V3 unless your module label specifically supports 5V
- OLED GND: GND
- OLED SDA: GPIO21
- OLED SCL: GPIO22

The sketch checks both common OLED I2C addresses: `0x3C` and `0x3D`.

## Serial Monitor

Open Serial Monitor at `115200` baud after flashing.

- If it prints `I2C device found at 0x3C` or `0x3D`, the wiring is alive.
- If one of the alternating pages appears, note whether it says `SSD1306` or `SH1106`. Use that driver in the full incubator firmware.
- If it prints `No I2C devices found`, check power, ground, SDA, and SCL first.
- If an I2C device appears at another address, send that address back before changing the main firmware.

The sketch uses the ESP32 default I2C pins. Do not use GPIO12 for this OLED on a classic ESP32 DevKit; GPIO12 is a boot strapping pin and can cause `invalid header: 0xffffffff` boot failures if pulled at reset.

```cpp
constexpr uint8_t OLED_SDA = 21;
constexpr uint8_t OLED_SCL = 22;
```

# Pinout Diagram

```text
ESP32 DevKit

GPIO21  -> 0.95/0.96/1.3 inch 128x64 I2C OLED SDA
GPIO22  -> 0.95/0.96/1.3 inch 128x64 I2C OLED SCL
GPIO4   -> DHT22 DATA
GPIO15  -> Heater relay IN
GPIO18  -> Futaba S3003 servo signal
GPIO23  -> Fan relay IN
GPIO25  -> Buzzer signal
GPIO26  -> Status LED anode through 220-330 ohm resistor
GPIO27  -> Page push button, other leg to GND
3V3     -> DHT22 VCC, OLED VCC
GND     -> DHT22 GND, OLED GND, relay GND, Servo GND, buzzer GND, LED cathode, button GND
5V/VIN  -> Relay module VCC if your modules require 5V
5V      -> Servo VCC from a separate regulated 5V supply
```

The GPIO15 relay controls the heating element. The GPIO23 relay controls the fan. Use opto-isolated relay modules and keep mains wiring enclosed and fused.

Fan rule in firmware: if humidity is above target humidity, the fan relay stays ON continuously. If humidity is equal to or below target humidity, the fan relay only turns ON while the heater relay is ON. Emergency OFF and repeated sensor failure force both relays OFF.

Power the Futaba S3003 from a separate 5V supply rated for servo current. Connect that supply ground to ESP32 GND so the GPIO18 signal has a common reference.

The tray servo cycle is balanced around tray level: it moves from `0` degrees to the dashboard angle, waits for the configured interval, returns through `0` degrees to the negative side, waits again, and repeats. For example, `45` cycles `0 -> +45 -> 0 -> -45`. The firmware sends no servo move command during boot, remembers the last reached tray endpoint, waits one configured interval before the first post-boot move, keeps the working `0` level pulse, allows a limited lower pulse for the negative side, and releases the servo PWM after each move to reduce holding current and avoid disturbing the heater relay control.

The page button on GPIO27 uses the ESP32 internal pull-up, so wire the button between GPIO27 and GND. Each press advances the OLED from the main temperature/humidity page to system, control, and tray servo pages. Any non-main page returns to the main temperature/humidity page after 5 seconds.

The status LED on GPIO26 stays ON while the system is powered and blinks during a detected fault. The buzzer on GPIO25 uses PWM for a medium-volume beep pattern for 30 seconds after a fault starts. With an active buzzer module, volume may not be adjustable from GPIO alone; use a resistor, transistor driver, or module trim pot if you need quieter output.

Current firmware-detectable faults are repeated DHT22 read failure, heater relay ON with no temperature rise after 30 seconds, temperature at 39.0 C and still rising, servo PWM attach failure, and emergency-off mode. The heater and relay faults are inferred from temperature trend. Physical fan and servo movement failures still need extra feedback hardware, such as current sensing, limit switches, or tachometer feedback, before firmware can prove those parts are not working.

Most 0.95/0.96 inch SSD1306 I2C OLED modules use address `0x3C`; many 1.3 inch 128x64 OLED modules use SH1106 at `0x3C`. The Arduino OLED test sketch checks `0x3C` and `0x3D` and alternates SSD1306/SH1106 test pages. Use `3V3` for OLED VCC unless the module label specifically says it supports 5V.

Do not wire the OLED to GPIO12 on a classic ESP32 DevKit. GPIO12 is a boot strapping pin and can cause `invalid header: 0xffffffff` boot failures if pulled during reset.

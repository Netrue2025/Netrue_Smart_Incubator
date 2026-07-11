#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

// 0.95/0.96/1.3 inch 128x64 I2C OLED diagnostic test.
// GM009605v4.3 is a PCB/module marking, so this sketch scans I2C
// and tries the two common 128x64 OLED controllers: SSD1306 and SH1106.
constexpr uint8_t OLED_SDA = 21;
constexpr uint8_t OLED_SCL = 22;
constexpr uint8_t OLED_ADDRESS_PRIMARY = 0x3C;
constexpr uint8_t OLED_ADDRESS_FALLBACK = 0x3D;
constexpr uint32_t OLED_CLOCK_HZ = 100000;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C ssd1306(U8G2_R0, U8X8_PIN_NONE);
U8G2_SH1106_128X64_NONAME_F_HW_I2C sh1106(U8G2_R0, U8X8_PIN_NONE);

uint8_t activeAddress = OLED_ADDRESS_PRIMARY;
bool foundDisplay = false;
bool useSh1106 = false;

bool addressResponds(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

void scanI2cBus() {
  Serial.println("Scanning I2C bus...");
  uint8_t found = 0;
  for (uint8_t address = 1; address < 127; address++) {
    if (addressResponds(address)) {
      found++;
      Serial.printf("I2C device found at 0x%02X\n", address);
      if (address == OLED_ADDRESS_PRIMARY || address == OLED_ADDRESS_FALLBACK) {
        activeAddress = address;
        foundDisplay = true;
      }
    }
  }
  if (found == 0) {
    Serial.println("No I2C devices found. Check VCC, GND, SDA, and SCL.");
  } else if (!foundDisplay) {
    Serial.println("I2C device found, but not at OLED addresses 0x3C/0x3D.");
  }
}

void drawCentered(U8G2& display, const char* text, uint8_t y, const uint8_t* font) {
  display.setFont(font);
  int16_t width = display.getStrWidth(text);
  int16_t x = max(0, (128 - width) / 2);
  display.drawStr(x, y, text);
}

void drawTestScreen(U8G2& display, const char* driverName, uint8_t frame) {
  display.clearBuffer();
  display.drawFrame(0, 0, 128, 64);
  drawCentered(display, "128x64 OLED TEST", 12, u8g2_font_6x10_tf);
  drawCentered(display, "NETRUE LTD", 35, u8g2_font_logisoso18_tf);
  char line[28];
  snprintf(line, sizeof(line), "%s 0x%02X", driverName, activeAddress);
  drawCentered(display, line, 53, u8g2_font_6x10_tf);
  display.drawBox(8, 58, 8 + (frame % 96), 3);
  display.sendBuffer();
}

void beginDisplays() {
  ssd1306.setI2CAddress(activeAddress << 1);
  ssd1306.begin();
  ssd1306.setPowerSave(0);

  sh1106.setI2CAddress(activeAddress << 1);
  sh1106.begin();
  sh1106.setPowerSave(0);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("0.95/0.96/1.3 inch 128x64 I2C OLED diagnostic starting...");
  Serial.println("PCB marking noted by user: GM009605v4.3");
  Serial.printf("SDA=%u SCL=%u\n", OLED_SDA, OLED_SCL);

  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(OLED_CLOCK_HZ);
  scanI2cBus();

  if (!foundDisplay) {
    Serial.println("Trying 0x3C anyway so a misbehaving scanner does not block testing.");
    activeAddress = OLED_ADDRESS_PRIMARY;
  }

  Serial.printf("Testing OLED address 0x%02X\n", activeAddress);
  beginDisplays();
}

void loop() {
  static uint8_t frame = 0;
  static uint32_t lastSwitch = 0;
  const uint32_t now = millis();

  if (now - lastSwitch >= 3500) {
    useSh1106 = !useSh1106;
    lastSwitch = now;
    Serial.printf("Trying %s driver at 0x%02X\n", useSh1106 ? "SH1106" : "SSD1306", activeAddress);
  }

  if (useSh1106) {
    drawTestScreen(sh1106, "SH1106", frame++);
  } else {
    drawTestScreen(ssd1306, "SSD1306", frame++);
  }
  delay(150);
}

#pragma once

#include "config.h"

void storageBegin();
void saveConfig(const IncubatorConfig& config);
IncubatorConfig loadConfig();
void appendReading(const Reading& reading);
void enqueueReading(const Reading& reading);
bool peekQueuedReading(String& jsonLine);
void popQueuedReading();
size_t queueSize();
void trimFile(const char* path, size_t maxBytes);
int loadTrayServoPosition();
void saveTrayServoPosition(int angle);

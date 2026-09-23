/*
 * ESP32 LED Controller Web Server with PWM Brightness Support
 * 
 * Class Assignment MVP: Hand Gesture Detection & LED Control System
 * Hardware Target: ESP32 Microcontroller + 10 LED Channels
 * Protocol: HTTP GET Server over Wi-Fi
 *
 * Endpoints:
 *   - GET /health                  : System health check
 *   - GET /status                  : Current LED state array, brightness %, & network status
 *   - GET /leds?count=N&brightness=B: Set first N LEDs ON (N in 0..10) with brightness B (0..100%)
 */

#include <WiFi.h>
#include <WebServer.h>

// ======================= CONFIGURATION =======================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const int HTTP_PORT = 80;
WebServer server(HTTP_PORT);

// Physical ESP32 GPIO Pin definitions for 10 LED Channels
const int NUM_LEDS = 10;
const int LED_PINS[NUM_LEDS] = {13, 12, 14, 27, 26, 25, 33, 32, 15, 4};

// System State
int currentLedCount = 0;
int currentBrightness = 100; // Percentage 0..100
bool currentLedStates[NUM_LEDS] = {false};

// ======================= HELPER FUNCTIONS =======================
void updateLedHardware(int count, int brightnessPct) {
  currentLedCount = count;
  currentBrightness = brightnessPct;

  // Convert 0..100% brightness to 0..255 PWM duty cycle
  int pwmValue = (brightnessPct * 255) / 100;

  for (int i = 0; i < NUM_LEDS; i++) {
    bool state = (i < count);
    currentLedStates[i] = state;
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
    analogWrite(LED_PINS[i], state ? pwmValue : 0);
#else
    // Fallback digital write or analog write depending on core version
    digitalWrite(LED_PINS[i], state ? (pwmValue > 128 ? HIGH : LOW) : LOW);
#endif
  }
}

String buildJsonStatus(bool ok, int count, int brightness, const String& extraMsg = "") {
  String json = "{";
  json += "\"ok\":" + String(ok ? "true" : "false") + ",";
  json += "\"count\":" + String(count) + ",";
  json += "\"brightness\":" + String(brightness) + ",";
  json += "\"leds\":[";
  for (int i = 0; i < NUM_LEDS; i++) {
    json += String(currentLedStates[i] ? "1" : "0");
    if (i < NUM_LEDS - 1) json += ",";
  }
  json += "]";
  if (extraMsg.length() > 0) {
    json += ",\"message\":\"" + extraMsg + "\"";
  }
  json += "}";
  return json;
}

// ======================= HTTP HANDLERS =======================
void handleHealth() {
  String json = "{\"status\":\"ok\",\"uptime_ms\":" + String(millis()) + "}";
  server.send(200, "application/json", json);
}

void handleStatus() {
  String json = buildJsonStatus(true, currentLedCount, currentBrightness);
  server.send(200, "application/json", json);
}

void handleLeds() {
  if (!server.hasArg("count")) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Missing 'count' query parameter\"}");
    return;
  }

  String countStr = server.arg("count");
  int countVal = countStr.toInt();

  int brightnessVal = 100;
  if (server.hasArg("brightness")) {
    brightnessVal = server.arg("brightness").toInt();
  }

  if (countVal < 0 || countVal > NUM_LEDS) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Count must be between 0 and 10\"}");
    return;
  }

  if (brightnessVal < 0 || brightnessVal > 100) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Brightness must be between 0 and 100\"}");
    return;
  }

  // Update physical GPIO PWM outputs
  updateLedHardware(countVal, brightnessVal);

  String json = buildJsonStatus(true, countVal, brightnessVal);
  server.send(200, "application/json", json);
}

void handleNotFound() {
  server.send(404, "application/json", "{\"ok\":false,\"error\":\"Route not found\"}");
}

// ======================= SETUP & LOOP =======================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=== ESP32 Hand Gesture 10-LED & Brightness Controller ===");

  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }

  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi Connected!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/health", HTTP_GET, handleHealth);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/leds", HTTP_GET, handleLeds);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP Web Server started on port 80.");
}

void loop() {
  server.handleClient();
}

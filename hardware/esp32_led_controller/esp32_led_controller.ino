/*
 * ESP32 LED Controller Web Server
 * 
 * Class Assignment MVP: Hand Gesture Detection & LED Control System
 * Hardware Target: ESP32 Microcontroller + 6 LED Channels
 * Protocol: HTTP GET Server over Wi-Fi
 *
 * Endpoints:
 *   - GET /health      : System health check
 *   - GET /status      : Current LED state and Wi-Fi network status
 *   - GET /leds?count=N: Set first N LEDs ON (N in 0..6), remaining OFF
 */

#include <WiFi.h>
#include <WebServer.h>

// ======================= CONFIGURATION =======================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const int HTTP_PORT = 80;
WebServer server(HTTP_PORT);

// Physical ESP32 GPIO Pin definitions for 6 LED Channels
const int NUM_LEDS = 6;
const int LED_PINS[NUM_LEDS] = {13, 12, 14, 27, 26, 25};

// System State
int currentLedCount = 0;
bool currentLedStates[NUM_LEDS] = {false, false, false, false, false, false};

// ======================= HELPER FUNCTIONS =======================
void updateLedHardware(int count) {
  currentLedCount = count;
  for (int i = 0; i < NUM_LEDS; i++) {
    bool state = (i < count);
    currentLedStates[i] = state;
    digitalWrite(LED_PINS[i], state ? HIGH : LOW);
  }
}

String buildJsonStatus(bool ok, int count, const String& extraMsg = "") {
  String json = "{";
  json += "\"ok\":" + String(ok ? "true" : "false") + ",";
  json += "\"count\":" + String(count) + ",";
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
  String json = buildJsonStatus(true, currentLedCount);
  server.send(200, "application/json", json);
}

void handleLeds() {
  if (!server.hasArg("count")) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Missing 'count' query parameter\"}");
    return;
  }

  String countStr = server.arg("count");
  int countVal = countStr.toInt();

  // Validate integer string conversion & range
  if (countStr != "0" && countVal == 0) { // Handles invalid non-numeric string
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Parameter 'count' must be a valid integer\"}");
    return;
  }

  if (countVal < 0 || countVal > NUM_LEDS) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Count must be between 0 and 6\"}");
    return;
  }

  // Update physical GPIO outputs
  updateLedHardware(countVal);

  String json = buildJsonStatus(true, countVal);
  server.send(200, "application/json", json);
}

void handleNotFound() {
  server.send(404, "application/json", "{\"ok\":false,\"error\":\"Route not found\"}");
}

// ======================= SETUP & LOOP =======================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=== ESP32 Hand Gesture LED Controller ===");

  // Initialize LED GPIO pins as outputs
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }

  // Connect to Wi-Fi
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

  // Register Web Server URI Handlers
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

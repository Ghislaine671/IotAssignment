# Hand Gesture Detection and LED Control System

Class Assignment MVP | Reuse-first computer vision implementation using Python, MediaPipe, OpenCV, and ESP32.

---

## Overview

This project implements a computer vision system where a webcam observes one or two hands, a pretrained MediaPipe Hand Landmarker model detects and tracks 21 hand landmarks per hand, a geometry-based module counts raised fingers, a 5-frame stabilizer filters frame jitter, and a Python HTTP client sends stable counts (0..6) to an ESP32 microcontroller controlling six physical LED channels over Wi-Fi.

```
Webcam -> CameraManager -> MediaPipe (VIDEO mode) -> FingerCounter -> GestureStabilizer -> LedMapper -> HTTP Client -> ESP32 -> 6 LEDs
```

---

## License Traceability & Open-Source Components

| Component / Model Asset | Project / Source | Version / Tag | License | Role in System |
|---|---|---|---|---|
| **MediaPipe Core Library** | [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) | `>=0.10.9` | **Apache-2.0** | Hand landmark detection & tracking engine |
| **Hand Landmarker Model Asset** | `hand_landmarker.task` (Google AI Edge) | `float16/1` | **Apache-2.0 / Google Terms** | Bundled pretrained palm & landmark model file |
| **OpenCV** | [opencv/opencv-python](https://github.com/opencv/opencv-python) | `>=4.8.0` | **Apache-2.0** | Camera I/O, frame rendering, HUD display |
| **Arduino-ESP32 Core** | [espressif/arduino-esp32](https://github.com/espressif/arduino-esp32) | `>=2.0.0` | **Apache-2.0** | ESP32 Wi-Fi & WebServer HTTP API |

---

## Hardware Configuration (ESP32 + 6 LEDs)

### GPIO Pin Mapping

| LED Channel | ESP32 GPIO Pin | Physical Position / Function |
|---|---|---|
| LED 1 | GPIO 13 | Channel 1 |
| LED 2 | GPIO 12 | Channel 2 |
| LED 3 | GPIO 14 | Channel 3 |
| LED 4 | GPIO 27 | Channel 4 |
| LED 5 | GPIO 26 | Channel 5 |
| LED 6 | GPIO 25 | Channel 6 |

### ESP32 Web Server API

| Endpoint | Method | Query Param | Example | Description |
|---|---|---|---|---|
| `/health` | `GET` | None | `http://192.168.1.50/health` | Health check endpoint |
| `/status` | `GET` | None | `http://192.168.1.50/status` | Returns LED state array & IP status |
| `/leds` | `GET` | `count=0..6` | `http://192.168.1.50/leds?count=4` | Sets first N LEDs ON, rest OFF |

---

## Quick Start Guide

### 1. Installation

Clone repository and install requirements:
```bash
pip install -r requirements.txt
```

### 2. Download MediaPipe Hand Landmarker Model

The application automatically downloads `hand_landmarker.task` on first run into `assets/models/`. You can also manually download it:
```bash
mkdir -p assets/models
curl -o assets/models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

### 3. ESP32 Flashing
1. Open `hardware/esp32_led_controller/esp32_led_controller.ino` in Arduino IDE.
2. Update `WIFI_SSID` and `WIFI_PASSWORD` with your local Wi-Fi credentials.
3. Flash to ESP32 board and open Serial Monitor at 115200 baud to view its IP address (e.g., `http://192.168.1.50`).

### 4. Running the Application

**Camera Baseline Test Mode** (verify webcam preview without ML):
```bash
python app.py --test-camera
```

**Run Full Gesture Detection Loop**:
```bash
python app.py --esp32-url http://192.168.1.50
```

### 5. Running Automated Unit Tests
```bash
pytest tests/ -v
```

---

## Operating Rules & Safety Features

1. **Request De-duplication**: HTTP GET requests are dispatched ONLY when the stable finger count changes (`stable_count != last_sent_count`).
2. **Shutdown Safety Rule**: On exit (pressing `q`), the application issues a best-effort `/leds?count=0` HTTP GET request before closing resources.
3. **Offline Resilience**: If the ESP32 is offline or disconnected, the camera vision system continues running smoothly, showing `MCU: OFFLINE` on the HUD.

# LOW-LEVEL DESIGN (LLD)
## Hand Gesture Detection and LED Control System

### System Overview
Class Assignment MVP software system that captures webcam video, detects and tracks up to 2 hands using MediaPipe HandLandmarker (`RunningMode.VIDEO`), counts raised fingers using deterministic joint geometry rules, stabilizes the count over a 5-frame sliding window, clamps the result to 0..6, and dispatches HTTP GET commands (`/leds?count=N`) to an ESP32 microcontroller controlling 6 physical LED channels.

### Architecture & Data Flow

```
Webcam Frame Capture (CameraManager with Mirroring)
         │
         ▼
MediaPipe Hand Landmarker (RunningMode.VIDEO, MAX_HANDS=2)
         │
         ▼
Deterministic Finger Counter (0..10 raw fingers across 2 hands)
         │
         ▼
Hardware Limit Clamping (Clamp 0..10 to 0..6)
         │
         ▼
Sliding Window Stabilizer (5-frame history, >=3 consensus)
         │
         ▼
LedMapper (N -> binary state array [1]*N + [0]*(6-N))
         │
         ▼
HTTP Client (GET /leds?count=N, de-duplication & offline safety)
         │ (Wi-Fi)
         ▼
ESP32 Web Server -> GPIO Outputs -> 6 LED Channels
```

### Module Responsibilities

1. `config.py`: Centralized system parameters (Camera index, thresholds, ESP32 base URL, model path).
2. `vision/camera_manager.py`: Controls OpenCV capture device and applies single horizontal flip rule before processing.
3. `vision/hand_detector.py`: Adapter wrapping MediaPipe HandLandmarker in VIDEO mode. Returns clean Python data structures.
4. `vision/finger_counter.py`: Deterministic joint landmark rules for fingers (Index 8/6, Middle 12/10, Ring 16/14, Pinky 20/18, Thumb 4/3/2/1 + handedness). Sums raw count and clamps to 0..6.
5. `control/stabilizer.py`: 5-frame sliding window requiring 3 matching frames. Eliminates single-frame jitter.
6. `control/led_mapper.py`: Converts count $N \in [0, 6]$ to `[1]*N + [0]*(6-N)`.
7. `control/microcontroller_client.py`: Issues `/leds?count=N`, `/health`, `/status` HTTP GET requests. Suppresses duplicate requests when count has not changed.
8. `ui/overlay.py`: Draws MediaPipe landmarks, skeleton lines, per-hand counts, raw total, stable count, MCU status, and command log on camera preview.
9. `hardware/esp32_led_controller/esp32_led_controller.ino`: ESP32 web server managing 6 GPIO outputs.
10. `app.py`: Main runtime loop with graceful teardown (`/leds?count=0` on shutdown).

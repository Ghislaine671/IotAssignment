# Hand Gesture Detection and LED Control System - Implementation Plan

## Objective
Build a reuse-first computer vision system that observes 1 or 2 hands, detects 21 landmarks via MediaPipe HandLandmarker, counts raised fingers using deterministic joint geometry, stabilizes the count over 5 frames, clamps to 0..6, and updates an ESP32 microcontroller controlling 6 physical LEDs via HTTP GET requests.

## Key Design Principles
1. **Reuse-First AI Strategy**: Use Google MediaPipe pretrained HandLandmarker (`hand_landmarker.task`) instead of training a custom detector.
2. **Synchronous Video Mode**: Use `RunningMode.VIDEO` with timestamps for predictable sequential frame processing.
3. **Single Mirroring Rule**: Horizontal flip applied in `CameraManager` before passing frames to MediaPipe.
4. **Deterministic Finger Counting & Clamping**:
   - Index (Tip 8 vs PIP 6)
   - Middle (Tip 12 vs PIP 10)
   - Ring (Tip 16 vs PIP 14)
   - Pinky (Tip 20 vs PIP 18)
   - Thumb (Tip 4, IP 3, MCP 2, CMC 1 + handedness)
   - Raw total across 2 hands (0..10) clamped to 0..6 for the 6 LED hardware limit.
5. **Hardware Safety & Network Efficiency**:
   - Send HTTP GET `/leds?count=N` ONLY when `stable_count != last_sent_count`.
   - On application shutdown or exit, execute best-effort `/leds?count=0` to turn off LEDs.
   - Non-blocking timeout handling ensures vision loop continues even if ESP32 is offline.

## Repository Structure
```
hand-led-control/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── vision/
│   ├── camera_manager.py
│   ├── hand_detector.py
│   └── finger_counter.py
├── control/
│   ├── stabilizer.py
│   ├── led_mapper.py
│   └── microcontroller_client.py
├── ui/
│   └── overlay.py
├── hardware/esp32_led_controller/
│   └── esp32_led_controller.ino
├── tests/
│   ├── test_finger_counter.py
│   ├── test_stabilizer.py
│   ├── test_led_mapper.py
│   └── test_microcontroller_client.py
├── assets/models/
│   └── hand_landmarker.task
└── docs/
    ├── LLD.md
    └── IMPLEMENTATION_PLAN.md
```

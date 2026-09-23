"""Central Configuration for Hand Gesture Detection & LED Control System.

All parameters (thresholds, hardware URLs, camera indices, ML parameters) are centralized here.
"""

import os
from pathlib import Path

# Repository Root Directory
BASE_DIR = Path(__file__).resolve().parent

# Camera Configuration
CAMERA_INDEX = 0
MIRROR_FLIP = True  # Apply horizontal flip in CameraManager before ML processing

# MediaPipe Hand Landmarker Configuration
MODEL_PATH = os.path.join(BASE_DIR, "assets", "models", "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.5
HAND_PRESENCE_CONFIDENCE = 0.5
TRACKING_CONFIDENCE = 0.5

# Gesture Stabilization Configuration
STABILIZER_WINDOW_SIZE = 5  # Sliding history window size in frames
STABILIZER_THRESHOLD = 3    # Minimum frame consensus needed to accept count change

# Hardware & LED Mapping Configuration
MAX_LEDS = 10               # Total physical LED channels supported (expanded to 10)
DEFAULT_BRIGHTNESS = 100    # Default brightness percentage (0..100)
ESP32_BASE_URL = "http://192.168.1.50"  # Microcontroller web server base URL
REQUEST_TIMEOUT = 1.0       # HTTP GET request timeout in seconds
MIN_COMMAND_INTERVAL = 0.2  # Minimum seconds between network commands

# 2-Finger Brightness Pinch Distance Parameters (normalized coordinate distance)
MIN_PINCH_DIST = 0.04       # 0% brightness distance
MAX_PINCH_DIST = 0.28       # 100% brightness distance

# Display Overlay Settings
WINDOW_TITLE = "Hand Gesture Detection & LED Control (Class MVP)"
FONT_SCALE = 0.6
THICKNESS = 2

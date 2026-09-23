"""FingerCounter Module.

Determines raised fingers per hand, special gestures (Thumbs Up / Thumbs Down),
and 2-finger pinch distance brightness percentage tracking (0% to 100%).
Supports up to 10 LED channels.
"""

import math
import logging
import config

logger = logging.getLogger(__name__)


def calculate_distance_2d(p1: dict, p2: dict) -> float:
    """Calculates 2D Euclidean distance between two landmark points."""
    return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])


class FingerCounter:
    """Calculates raised finger counts, gestures, and brightness percentage."""

    # Official MediaPipe landmark indices
    WRIST = 0
    THUMB_TIP = 4
    THUMB_IP = 3
    THUMB_MCP = 2
    THUMB_CMC = 1

    INDEX_TIP = 8
    INDEX_PIP = 6
    INDEX_MCP = 5

    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    MIDDLE_MCP = 9

    RING_TIP = 16
    RING_PIP = 14
    RING_MCP = 13

    PINKY_TIP = 20
    PINKY_PIP = 18
    PINKY_MCP = 17

    def __init__(self, max_leds: int = config.MAX_LEDS):
        self.max_leds = max_leds

    def is_thumb_raised(self, landmarks: list, handedness: str = "Right") -> bool:
        """Determines if thumb is extended using joint distance and handedness."""
        if len(landmarks) < 21:
            return False

        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        wrist = landmarks[self.WRIST]

        dist_tip_pinky = calculate_distance_2d(thumb_tip, pinky_mcp)
        dist_ip_pinky = calculate_distance_2d(thumb_ip, pinky_mcp)

        if handedness == "Right":
            is_extended_x = thumb_tip["x"] < thumb_ip["x"]
        else:
            is_extended_x = thumb_tip["x"] > thumb_ip["x"]

        dist_tip_wrist = calculate_distance_2d(thumb_tip, wrist)
        dist_ip_wrist = calculate_distance_2d(thumb_ip, wrist)

        return (dist_tip_pinky > dist_ip_pinky) or (dist_tip_wrist > dist_ip_wrist and is_extended_x)

    def is_finger_raised(self, landmarks: list, tip_idx: int, pip_idx: int) -> bool:
        """Determines if a non-thumb finger is raised."""
        if len(landmarks) < 21:
            return False

        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        wrist = landmarks[self.WRIST]

        upright_raised = tip["y"] < pip["y"]
        dist_tip_wrist = calculate_distance_2d(tip, wrist)
        dist_pip_wrist = calculate_distance_2d(pip, wrist)

        return upright_raised and (dist_tip_wrist > dist_pip_wrist)

    def detect_thumbs_gesture(self, landmarks: list) -> str:
        """Detects explicit Thumbs Up or Thumbs Down gesture.

        Returns:
            str: "THUMBS_UP", "THUMBS_DOWN", or "NONE"
        """
        if len(landmarks) < 21:
            return "NONE"

        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]

        # Other 4 fingers must be folded into a fist
        index_raised = self.is_finger_raised(landmarks, self.INDEX_TIP, self.INDEX_PIP)
        middle_raised = self.is_finger_raised(landmarks, self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring_raised = self.is_finger_raised(landmarks, self.RING_TIP, self.RING_PIP)
        pinky_raised = self.is_finger_raised(landmarks, self.PINKY_TIP, self.PINKY_PIP)

        other_fingers_folded = not (index_raised or middle_raised or ring_raised or pinky_raised)

        if other_fingers_folded:
            # Thumbs Up: Thumb tip is significantly higher (smaller y) than MCP
            if thumb_tip["y"] < thumb_mcp["y"] - 0.04:
                return "THUMBS_UP"
            # Thumbs Down: Thumb tip is significantly lower (larger y) than MCP
            elif thumb_tip["y"] > thumb_mcp["y"] + 0.04:
                return "THUMBS_DOWN"

        return "NONE"

    def calculate_2finger_brightness(self, landmarks: list) -> int:
        """Calculates LED brightness percentage (0..100%) from 2-finger tip distance.

        Args:
            landmarks: 21 landmark dicts.

        Returns:
            int: Brightness percentage 0..100.
        """
        if len(landmarks) < 21:
            return config.DEFAULT_BRIGHTNESS

        # Measure distance between Index tip (8) and Thumb tip (4)
        dist = calculate_distance_2d(landmarks[self.INDEX_TIP], landmarks[self.THUMB_TIP])

        min_d = config.MIN_PINCH_DIST
        max_d = config.MAX_PINCH_DIST

        # Clamp distance and scale to 0..100%
        clamped_dist = max(min_d, min(dist, max_d))
        pct = int(((clamped_dist - min_d) / (max_d - min_d)) * 100)
        return max(0, min(100, pct))

    def count_hand(self, hand_data: dict) -> dict:
        """Counts raised fingers and detects special gestures for a single hand."""
        landmarks = hand_data.get("landmarks", [])
        handedness = hand_data.get("handedness", "Right")

        if len(landmarks) < 21:
            return {
                "count": 0,
                "details": {},
                "handedness": handedness,
                "gesture": "NONE",
                "brightness": config.DEFAULT_BRIGHTNESS,
            }

        thumb = self.is_thumb_raised(landmarks, handedness)
        index = self.is_finger_raised(landmarks, self.INDEX_TIP, self.INDEX_PIP)
        middle = self.is_finger_raised(landmarks, self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring = self.is_finger_raised(landmarks, self.RING_TIP, self.RING_PIP)
        pinky = self.is_finger_raised(landmarks, self.PINKY_TIP, self.PINKY_PIP)

        details = {
            "thumb": thumb,
            "index": index,
            "middle": middle,
            "ring": ring,
            "pinky": pinky,
        }
        count = sum([thumb, index, middle, ring, pinky])

        # Check special Thumbs Up / Thumbs Down gesture
        thumbs_gesture = self.detect_thumbs_gesture(landmarks)

        # Check 2-finger pinch distance brightness if exactly 2 fingers raised
        brightness = config.DEFAULT_BRIGHTNESS
        if count == 2:
            brightness = self.calculate_2finger_brightness(landmarks)

        return {
            "count": count,
            "details": details,
            "handedness": handedness,
            "gesture": thumbs_gesture,
            "brightness": brightness,
        }

    def count_all(self, hands: list) -> tuple:
        """Counts total raised fingers (0..10), evaluates special gestures, and tracks brightness.

        Returns:
            tuple: (clamped_total: int, raw_total: int, hand_results: list, gesture_mode: str, brightness: int)
        """
        hand_results = []
        raw_total = 0
        active_gesture = "NONE"
        detected_brightness = config.DEFAULT_BRIGHTNESS
        has_2finger_brightness = False

        for hand in hands:
            res = self.count_hand(hand)
            hand_results.append(res)
            raw_total += res["count"]

            if res["gesture"] in ["THUMBS_UP", "THUMBS_DOWN"]:
                active_gesture = res["gesture"]

            if res["count"] == 2:
                detected_brightness = res["brightness"]
                has_2finger_brightness = True

        # Mode overrides
        if active_gesture == "THUMBS_UP":
            clamped_total = self.max_leds  # All 10 LEDs ON
            final_brightness = 100
        elif active_gesture == "THUMBS_DOWN":
            clamped_total = 0              # All 10 LEDs OFF
            final_brightness = 0
        else:
            clamped_total = min(raw_total, self.max_leds)
            final_brightness = detected_brightness if has_2finger_brightness else config.DEFAULT_BRIGHTNESS
            if has_2finger_brightness:
                active_gesture = "BRIGHTNESS_CONTROL"

        return clamped_total, raw_total, hand_results, active_gesture, final_brightness

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

    def __init__(self, max_leds: int = config.MAX_LEDS, thumb_sensitivity: float = config.THUMB_SENSITIVITY):
        self.max_leds = max_leds
        self.thumb_sensitivity = thumb_sensitivity

    def is_thumb_raised(self, landmarks: list, handedness: str = "Right") -> bool:
        """Determines if thumb is extended using anatomical palm-center distance ratio."""
        if len(landmarks) < 21:
            return False

        thumb_tip = landmarks[self.THUMB_TIP]    # 4
        thumb_mcp = landmarks[self.THUMB_MCP]    # 2
        middle_mcp = landmarks[self.MIDDLE_MCP]  # 9 (Anatomical Palm Center)
        index_mcp = landmarks[self.INDEX_MCP]    # 5
        wrist = landmarks[self.WRIST]            # 0

        # Distance from Thumb Tip (4) to Palm Center (Middle MCP 9)
        dist_tip_palm = calculate_distance_2d(thumb_tip, middle_mcp)
        # Reference distance from Thumb MCP (2) to Palm Center (Middle MCP 9)
        dist_mcp_palm = calculate_distance_2d(thumb_mcp, middle_mcp)

        if dist_mcp_palm == 0:
            return False

        # Palm-Center Ratio: Extended thumb reaches AWAY from palm center
        ratio = dist_tip_palm / dist_mcp_palm

        # Secondary check: Spread distance relative to palm size
        palm_size = calculate_distance_2d(index_mcp, wrist)
        spread_ratio = calculate_distance_2d(thumb_tip, index_mcp) / palm_size if palm_size > 0 else 0

        return (ratio >= self.thumb_sensitivity) and (spread_ratio >= 0.70)

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
        """Detects explicit Thumbs Up or Thumbs Down gesture."""
        if len(landmarks) < 21:
            return "NONE"

        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]

        index_raised = self.is_finger_raised(landmarks, self.INDEX_TIP, self.INDEX_PIP)
        middle_raised = self.is_finger_raised(landmarks, self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring_raised = self.is_finger_raised(landmarks, self.RING_TIP, self.RING_PIP)
        pinky_raised = self.is_finger_raised(landmarks, self.PINKY_TIP, self.PINKY_PIP)

        other_fingers_folded = not (index_raised or middle_raised or ring_raised or pinky_raised)

        if other_fingers_folded:
            if thumb_tip["y"] < thumb_mcp["y"] - 0.04:
                return "THUMBS_UP"
            elif thumb_tip["y"] > thumb_mcp["y"] + 0.04:
                return "THUMBS_DOWN"

        return "NONE"

    def calculate_2finger_brightness(self, landmarks: list) -> int:
        """Calculates LED brightness percentage (0..100%) from 2-finger tip distance."""
        if len(landmarks) < 21:
            return config.DEFAULT_BRIGHTNESS

        dist = calculate_distance_2d(landmarks[self.INDEX_TIP], landmarks[self.THUMB_TIP])

        min_d = config.MIN_PINCH_DIST
        max_d = config.MAX_PINCH_DIST

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

        thumbs_gesture = self.detect_thumbs_gesture(landmarks)

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
        """Counts total raised fingers (0..10), evaluates special gestures, and tracks brightness."""
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

        if active_gesture == "THUMBS_UP":
            clamped_total = self.max_leds
            final_brightness = 100
        elif active_gesture == "THUMBS_DOWN":
            clamped_total = 0
            final_brightness = 0
        else:
            clamped_total = min(raw_total, self.max_leds)
            final_brightness = detected_brightness if has_2finger_brightness else config.DEFAULT_BRIGHTNESS
            if has_2finger_brightness:
                active_gesture = "BRIGHTNESS_CONTROL"

        return clamped_total, raw_total, hand_results, active_gesture, final_brightness

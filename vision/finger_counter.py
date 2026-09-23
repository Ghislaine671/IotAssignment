"""FingerCounter Module.

Determines raised fingers per hand using deterministic MediaPipe 21-landmark geometry.
Counts raw total across hands (0..10) and clamps the result to MAX_LEDS (0..6).
"""

import math
import logging
import config

logger = logging.getLogger(__name__)


def calculate_distance_2d(p1: dict, p2: dict) -> float:
    """Calculates 2D Euclidean distance between two landmark points."""
    return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])


class FingerCounter:
    """Calculates raised finger counts per hand and total clamped count."""

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
        """Determines if thumb is extended using joint distance and handedness.

        Args:
            landmarks: List of 21 landmark dicts [{"x", "y", "z"}, ...]
            handedness: "Right" or "Left"

        Returns:
            bool: True if thumb is raised/extended.
        """
        if len(landmarks) < 21:
            return False

        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        wrist = landmarks[self.WRIST]

        # Primary rule: Distance from thumb tip to pinky MCP vs thumb IP to pinky MCP
        dist_tip_pinky = calculate_distance_2d(thumb_tip, pinky_mcp)
        dist_ip_pinky = calculate_distance_2d(thumb_ip, pinky_mcp)

        # Secondary rule: Handedness-specific horizontal extension
        if handedness == "Right":
            is_extended_x = thumb_tip["x"] < thumb_ip["x"]
        else:
            is_extended_x = thumb_tip["x"] > thumb_ip["x"]

        # Also check thumb tip height relative to wrist/CMC
        dist_tip_wrist = calculate_distance_2d(thumb_tip, wrist)
        dist_ip_wrist = calculate_distance_2d(thumb_ip, wrist)

        # Thumb is raised if tip is extended away from palm & pinky MCP
        return (dist_tip_pinky > dist_ip_pinky) or (dist_tip_wrist > dist_ip_wrist and is_extended_x)

    def is_finger_raised(self, landmarks: list, tip_idx: int, pip_idx: int) -> bool:
        """Determines if a non-thumb finger is raised.

        Uses deterministic joint rule:
        1. Vertical height comparison (tip.y < pip.y when hand is upright).
        2. Distance from wrist comparison (dist(tip, wrist) > dist(pip, wrist)).

        Args:
            landmarks: List of 21 landmark dicts.
            tip_idx: Index of fingertip landmark (8, 12, 16, 20).
            pip_idx: Index of finger PIP joint landmark (6, 10, 14, 18).

        Returns:
            bool: True if finger is extended.
        """
        if len(landmarks) < 21:
            return False

        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        wrist = landmarks[self.WRIST]

        # Upright check: tip is higher (smaller y) than PIP
        upright_raised = tip["y"] < pip["y"]

        # Distance check: tip is farther from wrist than PIP
        dist_tip_wrist = calculate_distance_2d(tip, wrist)
        dist_pip_wrist = calculate_distance_2d(pip, wrist)
        distance_raised = dist_tip_wrist > dist_pip_wrist

        return upright_raised and distance_raised

    def count_hand(self, hand_data: dict) -> dict:
        """Counts raised fingers for a single detected hand.

        Args:
            hand_data: Dict with "landmarks" and "handedness".

        Returns:
            dict: {
                "count": int (0..5),
                "details": {
                    "thumb": bool, "index": bool, "middle": bool, "ring": bool, "pinky": bool
                },
                "handedness": str
            }
        """
        landmarks = hand_data.get("landmarks", [])
        handedness = hand_data.get("handedness", "Right")

        if len(landmarks) < 21:
            return {"count": 0, "details": {}, "handedness": handedness}

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

        return {
            "count": count,
            "details": details,
            "handedness": handedness,
        }

    def count_all(self, hands: list) -> tuple:
        """Counts total raised fingers across all detected hands and clamps to max_leds.

        Args:
            hands: List of hand dictionaries from HandDetector.

        Returns:
            tuple: (clamped_total: int, raw_total: int, hand_results: list)
        """
        hand_results = []
        raw_total = 0

        for hand in hands:
            res = self.count_hand(hand)
            hand_results.append(res)
            raw_total += res["count"]

        # Clamp raw total (0..10) to max LED channels (0..6)
        clamped_total = min(raw_total, self.max_leds)
        return clamped_total, raw_total, hand_results

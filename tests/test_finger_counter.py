"""Unit tests for FingerCounter module."""

import pytest
from vision.finger_counter import FingerCounter


def create_synthetic_hand(extended_fingers: list, handedness: str = "Right") -> dict:
    """Helper to generate a synthetic 21-landmark list."""
    landmarks = [{"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(21)]
    wrist = {"x": 0.5, "y": 0.8, "z": 0.0}
    landmarks[0] = wrist

    landmarks[5] = {"x": 0.45, "y": 0.5, "z": 0.0}  # Index MCP
    landmarks[9] = {"x": 0.50, "y": 0.5, "z": 0.0}  # Middle MCP
    landmarks[13] = {"x": 0.55, "y": 0.5, "z": 0.0} # Ring MCP
    landmarks[17] = {"x": 0.60, "y": 0.5, "z": 0.0} # Pinky MCP

    fingers_map = {
        "index": (8, 6, 0.2, 0.4),   # tip=8, pip=6
        "middle": (12, 10, 0.15, 0.4), # tip=12, pip=10
        "ring": (16, 14, 0.2, 0.4),   # tip=16, pip=14
        "pinky": (20, 18, 0.25, 0.45), # tip=20, pip=18
    }

    for fname, (tip_idx, pip_idx, ext_y, cur_y) in fingers_map.items():
        if fname in extended_fingers:
            landmarks[pip_idx] = {"x": landmarks[tip_idx-3]["x"], "y": ext_y + 0.1, "z": 0.0}
            landmarks[tip_idx] = {"x": landmarks[tip_idx-3]["x"], "y": ext_y, "z": 0.0}
        else:
            landmarks[pip_idx] = {"x": landmarks[tip_idx-3]["x"], "y": cur_y, "z": 0.0}
            landmarks[tip_idx] = {"x": landmarks[tip_idx-3]["x"], "y": cur_y + 0.2, "z": 0.0}

    # Thumb handling
    if "thumb" in extended_fingers:
        landmarks[2] = {"x": 0.40, "y": 0.6, "z": 0.0}  # Thumb MCP
        landmarks[3] = {"x": 0.35, "y": 0.55, "z": 0.0} # Thumb IP
        landmarks[4] = {"x": 0.20, "y": 0.45, "z": 0.0} # Thumb Tip extended
    else:
        landmarks[2] = {"x": 0.45, "y": 0.6, "z": 0.0}
        landmarks[3] = {"x": 0.48, "y": 0.6, "z": 0.0}
        landmarks[4] = {"x": 0.52, "y": 0.55, "z": 0.0} # Tucked across palm

    return {
        "landmarks": landmarks,
        "handedness": handedness,
    }


def create_thumbs_gesture_hand(gesture_type: str = "THUMBS_UP") -> dict:
    """Helper to generate a hand performing Thumbs Up or Thumbs Down."""
    hand = create_synthetic_hand([])
    landmarks = hand["landmarks"]

    landmarks[2] = {"x": 0.40, "y": 0.60, "z": 0.0}

    if gesture_type == "THUMBS_UP":
        landmarks[4] = {"x": 0.40, "y": 0.40, "z": 0.0}
    else:
        landmarks[4] = {"x": 0.40, "y": 0.75, "z": 0.0}

    return hand


def test_count_fist():
    counter = FingerCounter(max_leds=6)
    fist_hand = create_synthetic_hand([])
    res = counter.count_hand(fist_hand)
    assert res["count"] == 0


def test_count_index_only():
    counter = FingerCounter(max_leds=6)
    hand = create_synthetic_hand(["index"])
    res = counter.count_hand(hand)
    assert res["count"] == 1


def test_count_open_palm():
    counter = FingerCounter(max_leds=6)
    hand = create_synthetic_hand(["thumb", "index", "middle", "ring", "pinky"])
    res = counter.count_hand(hand)
    assert res["count"] == 5


def test_count_two_hands_clamping():
    counter = FingerCounter(max_leds=6)
    hand1 = create_synthetic_hand(["thumb", "index", "middle", "ring", "pinky"], "Right")
    hand2 = create_synthetic_hand(["thumb", "index", "middle", "ring", "pinky"], "Left")

    clamped_total, raw_total, hand_results, gesture_mode, brightness = counter.count_all([hand1, hand2])
    assert raw_total == 10
    assert clamped_total == 6  # Clamped to 6 physical LEDs!


def test_thumbs_up_gesture():
    counter = FingerCounter(max_leds=6)
    hand = create_thumbs_gesture_hand("THUMBS_UP")
    clamped_total, raw_total, hand_results, gesture_mode, brightness = counter.count_all([hand])

    assert gesture_mode == "THUMBS_UP"
    assert clamped_total == 6
    assert brightness == 100


def test_thumbs_down_gesture():
    counter = FingerCounter(max_leds=6)
    hand = create_thumbs_gesture_hand("THUMBS_DOWN")
    clamped_total, raw_total, hand_results, gesture_mode, brightness = counter.count_all([hand])

    assert gesture_mode == "THUMBS_DOWN"
    assert clamped_total == 0
    assert brightness == 0

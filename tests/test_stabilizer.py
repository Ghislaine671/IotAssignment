"""Unit tests for GestureStabilizer module."""

import pytest
from control.stabilizer import GestureStabilizer


def test_stabilizer_initial_state():
    stabilizer = GestureStabilizer(window_size=5, threshold=3)
    assert stabilizer.current_stable_count == 0


def test_stabilizer_reject_single_frame_noise():
    stabilizer = GestureStabilizer(window_size=5, threshold=3)

    # 3 frames of 0
    for _ in range(3):
        assert stabilizer.update(0) == 0

    # 1 frame of noise (5)
    assert stabilizer.update(5) == 0  # Should remain 0!

    # 1 more frame of 0
    assert stabilizer.update(0) == 0


def test_stabilizer_consensus_transition():
    stabilizer = GestureStabilizer(window_size=5, threshold=3)

    # Fill window with 0
    for _ in range(5):
        stabilizer.update(0)
    assert stabilizer.current_stable_count == 0

    # Push 3 frames of count 4
    stabilizer.update(4)
    stabilizer.update(4)
    res = stabilizer.update(4)

    assert res == 4  # 3 of 5 frames are 4, transition should occur!
    assert stabilizer.current_stable_count == 4


def test_stabilizer_reset():
    stabilizer = GestureStabilizer(window_size=5, threshold=3)
    for _ in range(5):
        stabilizer.update(5)
    assert stabilizer.current_stable_count == 5

    stabilizer.reset()
    assert stabilizer.current_stable_count == 0
    assert len(stabilizer.history) == 0

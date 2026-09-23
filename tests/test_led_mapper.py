"""Unit tests for LedMapper module."""

import pytest
from control.led_mapper import LedMapper


def test_led_mapper_valid_counts():
    mapper = LedMapper(max_leds=10)

    assert mapper.map_count(0, 100) == [0] * 10
    assert mapper.map_count(5, 50) == [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    assert mapper.map_count(10, 100) == [1] * 10


def test_led_mapper_invalid_counts():
    mapper = LedMapper(max_leds=10)

    with pytest.raises(ValueError):
        mapper.map_count(-1, 100)

    with pytest.raises(ValueError):
        mapper.map_count(11, 100)

    with pytest.raises(ValueError):
        mapper.map_count(5, 150)

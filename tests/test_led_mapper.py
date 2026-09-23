"""Unit tests for LedMapper module."""

import pytest
from control.led_mapper import LedMapper


def test_led_mapper_valid_counts():
    mapper = LedMapper(max_leds=6)

    assert mapper.map_count(0) == [0, 0, 0, 0, 0, 0]
    assert mapper.map_count(1) == [1, 0, 0, 0, 0, 0]
    assert mapper.map_count(3) == [1, 1, 1, 0, 0, 0]
    assert mapper.map_count(5) == [1, 1, 1, 1, 1, 0]
    assert mapper.map_count(6) == [1, 1, 1, 1, 1, 1]


def test_led_mapper_invalid_counts():
    mapper = LedMapper(max_leds=6)

    with pytest.raises(ValueError):
        mapper.map_count(-1)

    with pytest.raises(ValueError):
        mapper.map_count(7)

    with pytest.raises(ValueError):
        mapper.map_count("3")

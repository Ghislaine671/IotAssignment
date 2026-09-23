"""Unit tests for MicrocontrollerClient module."""

from unittest.mock import patch, MagicMock
import pytest
import requests
from control.microcontroller_client import MicrocontrollerClient


@patch("requests.get")
def test_set_led_count_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "count": 7, "brightness": 85, "leds": [1]*7 + [0]*3}
    mock_get.return_value = mock_resp

    client = MicrocontrollerClient(base_url="http://192.168.1.50")
    res = client.set_led_count(count=7, brightness=85)

    assert res.ok is True
    assert res.count == 7
    assert res.brightness == 85
    assert client.last_sent_count == 7
    assert client.last_sent_brightness == 85
    assert client.is_online is True
    mock_get.assert_called_once_with("http://192.168.1.50/leds?count=7&brightness=85", timeout=1.0)


@patch("requests.get")
def test_duplicate_request_suppression(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "count": 3, "brightness": 100, "leds": [1]*3 + [0]*7}
    mock_get.return_value = mock_resp

    client = MicrocontrollerClient(base_url="http://192.168.1.50")

    # First request -> Dispatched
    res1 = client.set_led_count(3, 100)
    assert res1.ok is True
    assert mock_get.call_count == 1

    # Second request with SAME count & brightness -> Skipped
    res2 = client.set_led_count(3, 100)
    assert res2.ok is True
    assert res2.message == "Skipped duplicate HTTP request"
    assert mock_get.call_count == 1

    # Third request with CHANGED brightness -> Dispatched
    mock_resp.json.return_value = {"ok": True, "count": 3, "brightness": 50, "leds": [1]*3 + [0]*7}
    res3 = client.set_led_count(3, 50)
    assert res3.ok is True
    assert mock_get.call_count == 2

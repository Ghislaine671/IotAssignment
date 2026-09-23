"""Unit tests for MicrocontrollerClient module."""

from unittest.mock import patch, MagicMock
import pytest
import requests
from control.microcontroller_client import MicrocontrollerClient


@patch("requests.get")
def test_set_led_count_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "count": 4, "leds": [1, 1, 1, 1, 0, 0]}
    mock_get.return_value = mock_resp

    client = MicrocontrollerClient(base_url="http://192.168.1.50")
    res = client.set_led_count(4)

    assert res.ok is True
    assert res.count == 4
    assert client.last_sent_count == 4
    assert client.is_online is True
    mock_get.assert_called_once_with("http://192.168.1.50/leds?count=4", timeout=1.0)


@patch("requests.get")
def test_duplicate_request_suppression(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "count": 3, "leds": [1, 1, 1, 0, 0, 0]}
    mock_get.return_value = mock_resp

    client = MicrocontrollerClient(base_url="http://192.168.1.50")

    # First request -> Dispatched
    res1 = client.set_led_count(3)
    assert res1.ok is True
    assert mock_get.call_count == 1

    # Second request with SAME count -> Skipped (De-duplication)
    res2 = client.set_led_count(3)
    assert res2.ok is True
    assert res2.message == "Skipped duplicate HTTP request"
    assert mock_get.call_count == 1  # Network call count stayed at 1!

    # Third request with NEW count -> Dispatched
    mock_resp.json.return_value = {"ok": True, "count": 5, "leds": [1, 1, 1, 1, 1, 0]}
    res3 = client.set_led_count(5)
    assert res3.ok is True
    assert mock_get.call_count == 2


@patch("requests.get")
def test_network_failure_handling(mock_get):
    mock_get.side_effect = requests.RequestException("Connection refused")

    client = MicrocontrollerClient(base_url="http://192.168.1.50")
    res = client.set_led_count(2)

    assert res.ok is False
    assert client.is_online is False
    assert "OFFLINE" in res.message

"""MicrocontrollerClient Module.

Communicates with the ESP32 web server over HTTP GET requests.
Enforces request de-duplication (sends /leds?count=N ONLY when count changes),
request timeout resilience, and graceful offline fallback mode.
"""

import logging
import requests
import config

logger = logging.getLogger(__name__)


class MicrocontrollerResult:
    """Encapsulates result of an ESP32 HTTP request."""

    def __init__(self, ok: bool, count: int, leds: list = None, message: str = "", raw_json: dict = None):
        self.ok = ok
        self.count = count
        self.leds = leds or [0] * config.MAX_LEDS
        self.message = message
        self.raw_json = raw_json or {}


class MicrocontrollerClient:
    """HTTP client for ESP32 LED controller server."""

    def __init__(
        self,
        base_url: str = config.ESP32_BASE_URL,
        timeout: float = config.REQUEST_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.last_sent_count = None
        self.is_online = False
        self.last_error = ""

    def health_check(self) -> bool:
        """Sends GET /health to check ESP32 connectivity.

        Returns:
            bool: True if ESP32 responds with HTTP 200, False otherwise.
        """
        url = f"{self.base_url}/health"
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                self.is_online = True
                self.last_error = ""
                return True
            else:
                self.is_online = False
                self.last_error = f"HTTP {resp.status_code}"
                return False
        except requests.RequestException as e:
            self.is_online = False
            self.last_error = "Connection error"
            logger.warning(f"ESP32 health check failed: {e}")
            return False

    def set_led_count(self, count: int, force: bool = False) -> MicrocontrollerResult:
        """Sends GET /leds?count=N to ESP32 ONLY when count changes or force is True.

        Args:
            count: Target LED count (0..6).
            force: If True, sends request even if count == last_sent_count.

        Returns:
            MicrocontrollerResult: Response summary object.
        """
        # De-duplication check: Skip network call if count hasn't changed
        if not force and self.last_sent_count == count and self.is_online:
            return MicrocontrollerResult(
                ok=True,
                count=count,
                leds=[1] * count + [0] * (config.MAX_LEDS - count),
                message="Skipped duplicate HTTP request"
            )

        url = f"{self.base_url}/leds?count={count}"
        logger.info(f"Sending GET command to ESP32: {url}")

        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                self.is_online = True
                self.last_sent_count = count
                self.last_error = ""
                return MicrocontrollerResult(
                    ok=data.get("ok", True),
                    count=data.get("count", count),
                    leds=data.get("leds", [1] * count + [0] * (config.MAX_LEDS - count)),
                    raw_json=data
                )
            else:
                self.is_online = False
                self.last_error = f"HTTP {resp.status_code}"
                logger.error(f"ESP32 returned error status: {resp.status_code}")
                return MicrocontrollerResult(
                    ok=False,
                    count=count,
                    message=f"HTTP {resp.status_code}"
                )
        except requests.RequestException as e:
            self.is_online = False
            self.last_error = "OFFLINE"
            logger.warning(f"Failed to reach ESP32 at {url}: {e}")
            return MicrocontrollerResult(
                ok=False,
                count=count,
                message=f"OFFLINE: {e}"
            )

    def close(self):
        """Best-effort cleanup: sends /leds?count=0 on application shutdown."""
        logger.info("Shutdown safety check: sending /leds?count=0 to ESP32...")
        try:
            self.set_led_count(0, force=True)
        except Exception as e:
            logger.warning(f"Shutdown LED off request failed: {e}")

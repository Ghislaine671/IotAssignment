"""Local Mock ESP32 HTTP Web Server.

Simulates the physical ESP32 microcontroller endpoints (/health, /status, /leds?count=N)
so you can test complete end-to-end HTTP network requests locally without hardware.

Usage:
    python mock_esp32.py --port 5000
"""

import sys
import argparse
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MOCK-ESP32] %(message)s")
logger = logging.getLogger("MockESP32")

# Global mock state
current_count = 0
num_leds = 6


class MockESP32Handler(BaseHTTPRequestHandler):
    """HTTP Request Handler simulating ESP32 routes."""

    def log_message(self, format, *args):
        # Clean logging
        logger.info(f"{self.address_string()} - {format % args}")

    def send_json(self, status_code: int, data: dict):
        import json
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global current_count, num_leds
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/health":
            self.send_json(200, {"status": "ok", "uptime_ms": 99999})
        elif path == "/status":
            leds = [1] * current_count + [0] * (num_leds - current_count)
            self.send_json(200, {"ok": True, "count": current_count, "leds": leds})
        elif path == "/leds":
            if "count" not in query:
                self.send_json(400, {"ok": False, "error": "Missing 'count' parameter"})
                return

            try:
                count_val = int(query["count"][0])
            except ValueError:
                self.send_json(400, {"ok": False, "error": "Count must be integer"})
                return

            if count_val < 0 or count_val > num_leds:
                self.send_json(400, {"ok": False, "error": f"Count must be between 0 and {num_leds}"})
                return

            current_count = count_val
            leds = [1] * current_count + [0] * (num_leds - current_count)
            logger.info(f"Updated LED states: count={count_val}, leds={leds}")
            self.send_json(200, {"ok": True, "count": count_val, "leds": leds})
        else:
            self.send_json(404, {"ok": False, "error": "Route not found"})


def main():
    parser = argparse.ArgumentParser(description="Mock ESP32 HTTP Server for local testing")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    server_address = ("127.0.0.1", args.port)
    httpd = HTTPServer(server_address, MockESP32Handler)
    logger.info(f"Mock ESP32 Server running on http://127.0.0.1:{args.port}")
    logger.info("Endpoints available: GET /health, GET /status, GET /leds?count=0..6")
    logger.info("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Mock ESP32 Server stopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()

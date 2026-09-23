"""Main Application Entry Point: Hand Gesture Detection, Gesture Recognition & LED Control System.

Orchestrates CameraManager, HandDetector, FingerCounter, GestureStabilizer,
MicrocontrollerClient, and DisplayOverlay in a synchronous video processing loop.
"""

import sys
import time
import logging
import argparse
import cv2

import config
from vision.camera_manager import CameraManager
from vision.hand_detector import HandDetector
from vision.finger_counter import FingerCounter
from control.stabilizer import GestureStabilizer
from control.led_mapper import LedMapper
from control.microcontroller_client import MicrocontrollerClient
from ui.overlay import DisplayOverlay

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("HandLedApp")


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Hand Gesture Detection and LED Control System MVP")
    parser.add_argument("--camera-index", type=int, default=config.CAMERA_INDEX, help="Webcam device index (default: 0)")
    parser.add_argument("--esp32-url", type=str, default=config.ESP32_BASE_URL, help="ESP32 web server URL (e.g. http://192.168.1.50)")
    parser.add_argument("--test-camera", action="store_true", help="Camera baseline test mode (no ML or network requests)")
    return parser.parse_args()


def run_camera_test(camera_index: int):
    """Phase 2 camera baseline test without ML processing."""
    logger.info("Running Camera Baseline Test Mode (press 'q' to exit)...")
    cam = CameraManager(camera_index=camera_index, mirror_flip=config.MIRROR_FLIP)
    if not cam.open():
        logger.error("Failed to open camera.")
        return

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret or frame is None:
                logger.error("Failed to read frame.")
                break

            cv2.putText(
                frame,
                "CAMERA BASELINE TEST - PRESS 'Q' TO EXIT",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Camera Baseline Test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cam.release()
        logger.info("Camera baseline test completed cleanly.")


def main():
    """Main application runtime loop."""
    args = parse_args()

    if args.test_camera:
        run_camera_test(args.camera_index)
        return

    logger.info("Starting Hand Gesture Detection, Gesture Recognition & LED Control System...")
    logger.info(f"Target ESP32 URL: {args.esp32_url}")
    logger.info(f"Max Hands: {config.MAX_HANDS}, Max LEDs: {config.MAX_LEDS}")

    # Initialize System Services
    camera = CameraManager(camera_index=args.camera_index, mirror_flip=config.MIRROR_FLIP)
    detector = HandDetector()
    finger_counter = FingerCounter(max_leds=config.MAX_LEDS)
    stabilizer = GestureStabilizer(window_size=config.STABILIZER_WINDOW_SIZE, threshold=config.STABILIZER_THRESHOLD)
    led_mapper = LedMapper(max_leds=config.MAX_LEDS)
    mcu_client = MicrocontrollerClient(base_url=args.esp32_url, timeout=config.REQUEST_TIMEOUT)
    overlay = DisplayOverlay()

    # Open Camera Device
    if not camera.open():
        logger.critical("Could not access webcam. Exiting.")
        sys.exit(1)

    # Health Check ESP32 (Non-blocking status check)
    mcu_client.health_check()

    try:
        while True:
            ret, frame = camera.read_frame()
            if not ret or frame is None:
                logger.warning("Camera frame read failed. Retrying...")
                time.sleep(0.01)
                continue

            timestamp_ms = int(time.time() * 1000)

            # 1. Process frame with MediaPipe HandLandmarker Tasks API
            hands = detector.process(frame, timestamp_ms=timestamp_ms)

            # 2. Calculate finger count (0..10), gestures (Thumbs Up/Down), and 2-finger brightness
            clamped_count, raw_count, hand_results, gesture_mode, raw_brightness = finger_counter.count_all(hands)

            # 3. Apply 5-frame sliding window stabilization for count and brightness
            stable_count, stable_brightness = stabilizer.update(clamped_count, raw_brightness)

            # 4. Hardware Command Dispatch: Send GET request when count OR brightness changes!
            if stable_count != mcu_client.last_sent_count or stable_brightness != mcu_client.last_sent_brightness:
                logger.info(
                    f"State change -> Count: {mcu_client.last_sent_count} -> {stable_count}, "
                    f"Brightness: {mcu_client.last_sent_brightness}% -> {stable_brightness}%"
                )
                mcu_client.set_led_count(count=stable_count, brightness=stable_brightness)

            # 5. Render Visual HUD Overlay
            overlay.render(frame, hands, raw_count, stable_count, gesture_mode, stable_brightness, hand_results, mcu_client)

            # 6. Display Video Frame
            cv2.imshow(config.WINDOW_TITLE, frame)

            # Check for user exit ('q' or ESC)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), 27]:
                logger.info("Exit requested by user.")
                break

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info("Executing safe application teardown...")
        # Shutdown Safety Rule: Best-effort HTTP request to turn LEDs off
        try:
            mcu_client.close()
        except Exception as e:
            logger.warning(f"Failed to send shutdown LED off request: {e}")

        detector.close()
        camera.release()
        logger.info("Application shutdown complete.")


if __name__ == "__main__":
    main()

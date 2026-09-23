"""CameraManager Module.

Manages OpenCV webcam video capture and enforces a single, centralized camera mirroring rule
(optional horizontal flip before MediaPipe processing and user overlay display).
"""

import cv2
import logging

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages OpenCV webcam input lifecycle and frame pre-processing."""

    def __init__(self, camera_index: int = 0, mirror_flip: bool = True):
        self.camera_index = camera_index
        self.mirror_flip = mirror_flip
        self.cap = None

    def open(self) -> bool:
        """Opens the OpenCV camera capture device.

        Returns:
            bool: True if camera opened successfully, False otherwise.
        """
        logger.info(f"Opening camera index {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera index {self.camera_index}")
            return False
        logger.info(f"Camera index {self.camera_index} opened successfully.")
        return True

    def read_frame(self):
        """Reads a video frame and applies the centralized mirroring rule if configured.

        Returns:
            tuple: (success (bool), frame (ndarray or None))
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        # Apply single horizontal flip rule here before MediaPipe or visualization
        if self.mirror_flip:
            frame = cv2.flip(frame, 1)

        return True, frame

    def release(self):
        """Releases the camera hardware resources and closes any OpenCV windows."""
        if self.cap is not None:
            logger.info("Releasing camera capture resources...")
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

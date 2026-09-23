"""HandDetector Module.

Adapter wrapping MediaPipe Hand Landmarker Tasks API.
Uses RunningMode.VIDEO to process webcam frames synchronously with sequential timestamps.
Converts MediaPipe result objects into decoupled Python dictionaries for FingerCounter.
"""

import os
import time
import logging
import urllib.request
import cv2
import config

logger = logging.getLogger(__name__)


def ensure_model_file(model_path: str, model_url: str) -> str:
    """Ensures the MediaPipe hand_landmarker.task model file exists locally. Downloads if missing.

    Args:
        model_path: Target local filepath for the model.
        model_url: Remote URL to download model asset from.

    Returns:
        str: Absolute path to the verified model file.
    """
    abs_path = os.path.abspath(model_path)
    if not os.path.exists(abs_path):
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        logger.info(f"Model file missing at {abs_path}. Downloading from {model_url}...")
        urllib.request.urlretrieve(model_url, abs_path)
        logger.info("Model download complete.")
    return abs_path


class HandDetector:
    """Wraps MediaPipe HandLandmarker in VIDEO running mode."""

    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        max_hands: int = config.MAX_HANDS,
        detection_confidence: float = config.DETECTION_CONFIDENCE,
        hand_presence_confidence: float = config.HAND_PRESENCE_CONFIDENCE,
        tracking_confidence: float = config.TRACKING_CONFIDENCE,
    ):
        self.model_path = ensure_model_file(model_path, config.MODEL_URL)
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.hand_presence_confidence = hand_presence_confidence
        self.tracking_confidence = tracking_confidence
        self.landmarker = None
        self._init_landmarker()

    def _init_landmarker(self):
        """Initializes the MediaPipe HandLandmarker Task engine."""
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=self.max_hands,
                min_hand_detection_confidence=self.detection_confidence,
                min_hand_presence_confidence=self.hand_presence_confidence,
                min_tracking_confidence=self.tracking_confidence,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            logger.info("MediaPipe HandLandmarker initialized in VIDEO mode.")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe HandLandmarker: {e}")
            self.landmarker = None

    def process(self, frame, timestamp_ms: int = None):
        """Processes an OpenCV BGR frame and returns detected hands as decoupled Python data.

        Args:
            frame: BGR numpy image frame.
            timestamp_ms: Integer millisecond timestamp (defaults to current time).

        Returns:
            list: List of hand dictionaries, e.g.:
                [
                    {
                        "handedness": "Right" | "Left",
                        "score": 0.98,
                        "landmarks": [{"x": 0.5, "y": 0.4, "z": -0.01}, ... 21 points],
                        "world_landmarks": [...] # optional
                    },
                    ...
                ]
        """
        if self.landmarker is None or frame is None:
            return []

        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        import mediapipe as mp

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        hands = []
        if result and result.hand_landmarks:
            for idx, landmarks in enumerate(result.hand_landmarks):
                # Retrieve handedness (Left vs Right) and confidence score
                handedness_label = "Right"
                score = 1.0
                if result.handedness and idx < len(result.handedness):
                    hand_info = result.handedness[idx][0]
                    handedness_label = hand_info.category_name
                    score = hand_info.score

                # Format 21 landmarks into standard list of dicts
                landmark_list = [
                    {"x": lm.x, "y": lm.y, "z": lm.z} for lm in landmarks
                ]

                hands.append({
                    "handedness": handedness_label,
                    "score": score,
                    "landmarks": landmark_list,
                })

        return hands

    def close(self):
        """Closes the MediaPipe HandLandmarker object."""
        if self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None
            logger.info("MediaPipe HandLandmarker closed.")

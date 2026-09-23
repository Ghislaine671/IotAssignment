"""GestureStabilizer Module.

Filters frame-to-frame landmark jitter using a sliding history window.
Stabilizes both LED count (0..10) and brightness percentage (0..100%).
"""

from collections import deque, Counter
import logging
import config

logger = logging.getLogger(__name__)


class GestureStabilizer:
    """Sliding-window gesture count and brightness stabilizer."""

    def __init__(
        self,
        window_size: int = config.STABILIZER_WINDOW_SIZE,
        threshold: int = config.STABILIZER_THRESHOLD,
    ):
        self.window_size = window_size
        self.threshold = threshold
        self.history = deque(maxlen=self.window_size)
        self.brightness_history = deque(maxlen=self.window_size)
        self.current_stable_count = 0
        self.current_stable_brightness = config.DEFAULT_BRIGHTNESS

    def update(self, raw_count: int, raw_brightness: int = config.DEFAULT_BRIGHTNESS) -> tuple:
        """Adds a raw frame count and brightness to history and computes stabilized values.

        Args:
            raw_count: Clamped integer finger count from current frame (0..10).
            raw_brightness: Brightness percentage from current frame (0..100).

        Returns:
            tuple: (stable_count: int, stable_brightness: int)
        """
        self.history.append(raw_count)
        self.brightness_history.append(raw_brightness)

        # 1. Count frequency consensus
        counts = Counter(self.history)
        most_common_value, frequency = counts.most_common(1)[0]

        if frequency >= self.threshold:
            if most_common_value != self.current_stable_count:
                logger.info(
                    f"Gesture count stabilized to {most_common_value} "
                    f"(frequency {frequency}/{len(self.history)})"
                )
                self.current_stable_count = most_common_value

        # 2. Smooth brightness percentage using sliding average
        if self.brightness_history:
            avg_b = sum(self.brightness_history) / len(self.brightness_history)
            self.current_stable_brightness = int(round(avg_b))

        return self.current_stable_count, self.current_stable_brightness

    def reset(self):
        """Resets history buffers."""
        self.history.clear()
        self.brightness_history.clear()
        self.current_stable_count = 0
        self.current_stable_brightness = config.DEFAULT_BRIGHTNESS

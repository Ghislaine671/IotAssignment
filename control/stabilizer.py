"""GestureStabilizer Module.

Filters frame-to-frame landmark jitter using a sliding history window.
Requires a count value to appear consistently in at least consensus_threshold
out of window_size frames before updating the stable gesture count.
"""

from collections import deque, Counter
import logging
import config

logger = logging.getLogger(__name__)


class GestureStabilizer:
    """Sliding-window gesture count stabilizer."""

    def __init__(
        self,
        window_size: int = config.STABILIZER_WINDOW_SIZE,
        threshold: int = config.STABILIZER_THRESHOLD,
    ):
        self.window_size = window_size
        self.threshold = threshold
        self.history = deque(maxlen=self.window_size)
        self.current_stable_count = 0

    def update(self, raw_count: int) -> int:
        """Adds a raw frame count to history and computes the stabilized count.

        Args:
            raw_count: Clamped integer finger count from current frame (0..6).

        Returns:
            int: Stabilized finger count (0..6).
        """
        self.history.append(raw_count)

        # Count frequencies in recent window
        counts = Counter(self.history)
        most_common_value, frequency = counts.most_common(1)[0]

        # Only update stable output if consensus threshold met
        if frequency >= self.threshold:
            if most_common_value != self.current_stable_count:
                logger.info(
                    f"Gesture stabilized to {most_common_value} "
                    f"(frequency {frequency}/{len(self.history)})"
                )
                self.current_stable_count = most_common_value

        return self.current_stable_count

    def reset(self):
        """Resets history buffer and resets stable count to 0."""
        self.history.clear()
        self.current_stable_count = 0

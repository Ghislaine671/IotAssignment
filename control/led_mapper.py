"""LedMapper Module.

Maps stable finger count N to physical LED channel state array [1]*N + [0]*(6-N).
Separates gesture logic from hardware pin definitions.
"""

import logging
import config

logger = logging.getLogger(__name__)


class LedMapper:
    """Maps integer finger count N to binary LED channel states."""

    def __init__(self, max_leds: int = config.MAX_LEDS):
        self.max_leds = max_leds

    def map_count(self, count: int) -> list:
        """Converts count N into list of binary channel states.

        Args:
            count: Integer in range 0..max_leds.

        Returns:
            list: List of ints [1/0, ...] of length max_leds.

        Raises:
            ValueError: If count is out of valid range 0..max_leds.
        """
        if not isinstance(count, int) or count < 0 or count > self.max_leds:
            raise ValueError(f"Count {count} out of range (must be int 0..{self.max_leds})")

        return [1] * count + [0] * (self.max_leds - count)

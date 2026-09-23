"""LedMapper Module.

Maps stable finger count N (0..10) and brightness percentage B (0..100%)
to physical LED channel state array [1]*N + [0]*(10-N).
"""

import logging
import config

logger = logging.getLogger(__name__)


class LedMapper:
    """Maps integer finger count N and brightness B to binary LED channel states."""

    def __init__(self, max_leds: int = config.MAX_LEDS):
        self.max_leds = max_leds

    def map_count(self, count: int, brightness: int = 100) -> list:
        """Converts count N into list of binary channel states.

        Args:
            count: Integer in range 0..max_leds.
            brightness: Integer percentage 0..100.

        Returns:
            list: List of ints [1/0, ...] of length max_leds.

        Raises:
            ValueError: If count or brightness is out of valid range.
        """
        if not isinstance(count, int) or count < 0 or count > self.max_leds:
            raise ValueError(f"Count {count} out of range (must be int 0..{self.max_leds})")

        if not isinstance(brightness, int) or brightness < 0 or brightness > 100:
            raise ValueError(f"Brightness {brightness} out of range (must be int 0..100)")

        return [1] * count + [0] * (self.max_leds - count)

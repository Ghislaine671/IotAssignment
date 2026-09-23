"""DisplayOverlay Module.

Draws MediaPipe 21-landmark nodes, hand skeleton connections, per-hand counts,
raw total count, clamped stable count, and ESP32 MCU status on the OpenCV preview.
"""

import cv2
import config

# Hand skeleton connections (pairs of landmark indices)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


class DisplayOverlay:
    """Renders visual HUD overlay on OpenCV camera frames."""

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_landmarks(self, frame, hands: list):
        """Draws hand skeleton lines and landmark joint nodes.

        Args:
            frame: OpenCV BGR image frame (modified in-place).
            hands: List of hand dicts from HandDetector.
        """
        h, w, _ = frame.shape

        for hand in hands:
            landmarks = hand.get("landmarks", [])
            if not landmarks:
                continue

            # Convert normalized 0..1 coordinates to pixel coordinates
            pts = [(int(lm["x"] * w), int(lm["y"] * h)) for lm in landmarks]

            # Draw skeleton connection lines
            for p1_idx, p2_idx in HAND_CONNECTIONS:
                if p1_idx < len(pts) and p2_idx < len(pts):
                    cv2.line(frame, pts[p1_idx], pts[p2_idx], (0, 255, 255), 2)

            # Draw landmark nodes (fingertips highlight green, joints cyan)
            for idx, pt in enumerate(pts):
                color = (0, 255, 0) if idx in [4, 8, 12, 16, 20] else (255, 200, 0)
                radius = 5 if idx in [4, 8, 12, 16, 20] else 3
                cv2.circle(frame, pt, radius, color, -1)

    def draw_hud(self, frame, raw_count: int, stable_count: int, hand_results: list, mcu_client):
        """Draws top status banner, per-hand count cards, and MCU connectivity badge.

        Args:
            frame: OpenCV BGR image frame.
            raw_count: Total raw finger count (0..10).
            stable_count: Clamped stable count (0..6).
            hand_results: List of per-hand count dicts from FingerCounter.
            mcu_client: MicrocontrollerClient instance.
        """
        h, w, _ = frame.shape

        # Draw top semi-transparent HUD background bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 90), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "HAND GESTURE LED CONTROLLER", (15, 25), self.font, 0.6, (255, 255, 255), 2)

        # Raw vs Clamped Stable Count Badges
        raw_text = f"Raw Fingers: {raw_count}"
        stable_text = f"STABLE COUNT: {stable_count} / {config.MAX_LEDS} LEDs"
        cv2.putText(frame, raw_text, (15, 52), self.font, 0.5, (180, 180, 180), 1)
        cv2.putText(frame, stable_text, (15, 78), self.font, 0.7, (0, 255, 255), 2)

        # MCU Connection Badge (Right side of banner)
        if mcu_client.is_online:
            status_str = f"MCU: ONLINE ({mcu_client.base_url})"
            status_color = (0, 255, 0)
        else:
            status_str = f"MCU: OFFLINE ({mcu_client.last_error or 'Disconnected'})"
            status_color = (0, 0, 255)

        cv2.putText(frame, status_str, (w - 360, 30), self.font, 0.5, status_color, 2)

        last_cmd = f"Last Sent: /leds?count={mcu_client.last_sent_count if mcu_client.last_sent_count is not None else 'None'}"
        cv2.putText(frame, last_cmd, (w - 360, 58), self.font, 0.5, (200, 200, 200), 1)

        # Per-hand count boxes (bottom-left overlay)
        card_y = h - 60
        for idx, hand_res in enumerate(hand_results):
            handedness = hand_res.get("handedness", f"Hand {idx+1}")
            cnt = hand_res.get("count", 0)
            card_text = f"{handedness} Hand: {cnt} fingers"

            cv2.rectangle(frame, (15 + idx * 220, card_y), (215 + idx * 220, card_y + 45), (30, 30, 40), -1)
            cv2.rectangle(frame, (15 + idx * 220, card_y), (215 + idx * 220, card_y + 45), (0, 255, 255), 1)
            cv2.putText(frame, card_text, (25 + idx * 220, card_y + 28), self.font, 0.55, (255, 255, 255), 2)

    def render(self, frame, hands: list, raw_count: int, stable_count: int, hand_results: list, mcu_client):
        """Complete overlay drawing pipeline."""
        self.draw_landmarks(frame, hands)
        self.draw_hud(frame, raw_count, stable_count, hand_results, mcu_client)
        return frame

"""DisplayOverlay Module.

Draws MediaPipe 21-landmark nodes, hand skeleton connections, per-hand counts,
detailed per-finger breakdown badges [T I M R P], gesture mode badges,
and Brightness Percentage progress bar (0..100%) on the OpenCV preview.
"""

import cv2
import config

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
        """Draws hand skeleton lines and landmark joint nodes."""
        h, w, _ = frame.shape

        for hand in hands:
            landmarks = hand.get("landmarks", [])
            if not landmarks:
                continue

            pts = [(int(lm["x"] * w), int(lm["y"] * h)) for lm in landmarks]

            for p1_idx, p2_idx in HAND_CONNECTIONS:
                if p1_idx < len(pts) and p2_idx < len(pts):
                    cv2.line(frame, pts[p1_idx], pts[p2_idx], (0, 255, 255), 2)

            for idx, pt in enumerate(pts):
                color = (0, 255, 0) if idx in [4, 8, 12, 16, 20] else (255, 200, 0)
                radius = 5 if idx in [4, 8, 12, 16, 20] else 3
                cv2.circle(frame, pt, radius, color, -1)

    def draw_hud(self, frame, raw_count: int, stable_count: int, gesture_mode: str, brightness: int, hand_results: list, mcu_client):
        """Draws top status banner, gesture badges, brightness bar, per-finger breakdown, and MCU status."""
        h, w, _ = frame.shape

        # Top semi-transparent HUD background bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 125), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

        # Title
        cv2.putText(frame, "HAND GESTURE LED & BRIGHTNESS CONTROLLER", (15, 25), self.font, 0.6, (255, 255, 255), 2)

        # 1. Gesture Mode Badge
        if gesture_mode == "THUMBS_UP":
            badge_text = "GESTURE: THUMBS UP (100% MAX)"
            badge_color = (0, 255, 0)
        elif gesture_mode == "THUMBS_DOWN":
            badge_text = "GESTURE: THUMBS DOWN (0% OFF)"
            badge_color = (0, 0, 255)
        elif gesture_mode == "BRIGHTNESS_CONTROL":
            badge_text = f"GESTURE: 2-FINGER BRIGHTNESS PINCH ({brightness}%)"
            badge_color = (0, 255, 255)
        else:
            badge_text = f"GESTURE: FINGER COUNTING ({stable_count}/{config.MAX_LEDS} LEDs)"
            badge_color = (200, 200, 200)

        cv2.putText(frame, badge_text, (15, 52), self.font, 0.55, badge_color, 2)

        # 2. Raw Count vs Clamped Stable Count Badges
        raw_text = f"Raw Fingers: {raw_count} | Active LEDs: {stable_count}/{config.MAX_LEDS}"
        cv2.putText(frame, raw_text, (15, 78), self.font, 0.5, (180, 180, 180), 1)

        # 3. Brightness Percentage Progress Bar
        bar_x, bar_y, bar_w, bar_h = 15, 95, 250, 16
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 60), -1)
        fill_w = int((brightness / 100.0) * bar_w)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 255, 255), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 1)
        cv2.putText(frame, f"Brightness: {brightness}%", (bar_x + bar_w + 12, bar_y + 13), self.font, 0.5, (255, 255, 255), 1)

        # 4. MCU Connection Badge (Right side of banner)
        if mcu_client.is_online:
            status_str = f"MCU: ONLINE ({mcu_client.base_url})"
            status_color = (0, 255, 0)
        else:
            status_str = f"MCU: OFFLINE ({mcu_client.last_error or 'Disconnected'})"
            status_color = (0, 0, 255)

        cv2.putText(frame, status_str, (w - 380, 30), self.font, 0.5, status_color, 2)

        b_sent = mcu_client.last_sent_brightness if mcu_client.last_sent_brightness is not None else 'None'
        c_sent = mcu_client.last_sent_count if mcu_client.last_sent_count is not None else 'None'
        last_cmd = f"Last Sent: /leds?count={c_sent}&brightness={b_sent}"
        cv2.putText(frame, last_cmd, (w - 380, 58), self.font, 0.45, (200, 200, 200), 1)

        # Per-hand detailed cards with [T I M R P] finger status (bottom-left overlay)
        card_y = h - 70
        for idx, hand_res in enumerate(hand_results):
            handedness = hand_res.get("handedness", f"Hand {idx+1}")
            cnt = hand_res.get("count", 0)
            details = hand_res.get("details", {})

            # Format per-finger breakdown string
            t = "1" if details.get("thumb") else "0"
            i = "1" if details.get("index") else "0"
            m = "1" if details.get("middle") else "0"
            r = "1" if details.get("ring") else "0"
            p = "1" if details.get("pinky") else "0"

            line1 = f"{handedness} Hand: {cnt} fingers"
            line2 = f"[T:{t} I:{i} M:{m} R:{r} P:{p}]"

            card_x1 = 15 + idx * 260
            card_x2 = 255 + idx * 260

            cv2.rectangle(frame, (card_x1, card_y), (card_x2, card_y + 55), (30, 30, 40), -1)
            cv2.rectangle(frame, (card_x1, card_y), (card_x2, card_y + 55), (0, 255, 255), 1)
            cv2.putText(frame, line1, (card_x1 + 10, card_y + 22), self.font, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, line2, (card_x1 + 10, card_y + 44), self.font, 0.45, (0, 255, 255), 1)

    def render(self, frame, hands: list, raw_count: int, stable_count: int, gesture_mode: str, brightness: int, hand_results: list, mcu_client):
        """Complete overlay drawing pipeline."""
        self.draw_landmarks(frame, hands)
        self.draw_hud(frame, raw_count, stable_count, gesture_mode, brightness, hand_results, mcu_client)
        return frame

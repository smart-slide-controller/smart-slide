from collections import deque
from dataclasses import dataclass
import time
import math

@dataclass
class GestureEvent:
    """A simple action from the hand gesture system."""
    action: str
    label: str

class GestureEngine:
    """Detect hand gestures and turn them into app actions.

    This class watches the hand position and gesture label.
    It decides when the user swipes, holds a hand, or exits the presentation.
    """
    def __init__(self, swipe_threshold_px=90, cooldown_seconds=0.8,
                 activation_hold_seconds=0.5, fist_hold_seconds=0.8,
                 gesture_hold_seconds=0.6):
        self.swipe_threshold_px = swipe_threshold_px
        self.cooldown_seconds = cooldown_seconds
        self.activation_hold_seconds = activation_hold_seconds
        self.fist_hold_seconds = fist_hold_seconds
        self.gesture_hold_seconds = gesture_hold_seconds
        self.history = deque(maxlen=12)
        self.last_action_time = 0.0
        self.gesture_active = False
        self._hold_name = None
        self._hold_start = None
        self._hold_fired = False
        self._swipe_latched = False

    def reset(self):
        """Clear saved hand state so a new gesture can start fresh."""
        self.history.clear()
        self._hold_name = None
        self._hold_start = None
        self._hold_fired = False
        self._swipe_latched = False

    def update(self, center_x, center_y, hand_label, now=None):
        """Check the latest hand data and return one or more app events."""
        now = time.monotonic() if now is None else now
        events = []
        if center_x is None:
            self.reset()
            return events

        # Save hand movement history so we can detect a swipe.
        self.history.append((now, int(center_x), int(center_y)))

        # Hold actions: open palm starts control, fist saves slide, etc.
        if hand_label in ("OPEN_PALM", "FIST", "THREE_FINGERS", "PEACE"):
            if self._hold_name != hand_label:
                self._hold_name, self._hold_start = hand_label, now
                self._hold_fired = False
            held = now - (self._hold_start if self._hold_start is not None else now)
            if (
                hand_label == "OPEN_PALM"
                and held >= self.activation_hold_seconds
                and not self._hold_fired
            ):
                self.gesture_active = True
                events.append(GestureEvent("ACTIVATE", "Gesture control active"))
                self._hold_fired = True
            elif (
                hand_label == "FIST"
                and held >= self.fist_hold_seconds
                and not self._hold_fired
            ):
                events.append(
                    GestureEvent("SCREENSHOT", "Closed fist: Save current PowerPoint slide")
                )
                self._hold_fired = True
            elif (
                hand_label == "THREE_FINGERS"
                and held >= self.gesture_hold_seconds
                and not self._hold_fired
            ):
                self.gesture_active = False
                events.append(GestureEvent("EXIT", "Three fingers: Exit presentation"))
                self._hold_fired = True
            elif (
                hand_label == "PEACE"
                and self.gesture_active
                and held >= self.gesture_hold_seconds
                and not self._hold_fired
            ):
                events.append(
                    GestureEvent("SCREENSHOT", "Save current PowerPoint slide")
                )
                self._hold_fired = True
        else:
            self._hold_name, self._hold_start = None, None
            self._hold_fired = False

        # These gestures are not used for swipe navigation.
        if hand_label in ("THREE_FINGERS", "PEACE"):
            return events

        if len(self.history) < 5:
            return events
        old_t, old_x, old_y = self.history[0]
        dx = self.history[-1][1] - old_x

        # Only act when gesture mode is active and the swipe has not been used yet.
        if not self.gesture_active or self._swipe_latched:
            if abs(dx) < self.swipe_threshold_px * 0.35:
                self._swipe_latched = False
            return events
        if now - self.last_action_time < self.cooldown_seconds:
            return events
        if dx <= -self.swipe_threshold_px:
            events.append(GestureEvent("NEXT", "Swipe right-to-left: Next slide"))
            self.last_action_time = now
            self._swipe_latched = True
            self.history.clear()
        elif dx >= self.swipe_threshold_px:
            events.append(GestureEvent("PREVIOUS", "Swipe left-to-right: Previous slide"))
            self.last_action_time = now
            self._swipe_latched = True
            self.history.clear()
        return events

def classify_hand(landmarks, image_width, image_height):
    """Look at finger positions and decide what hand pose is shown.

    The math compares finger tip distance to finger base distance.
    This helps the app tell apart a fist, open palm, peace sign, and other poses.
    """
    pts = [(lm.x * image_width, lm.y * image_height) for lm in landmarks]
    finger_joints = [(5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)]
    extended = [
        math.dist(pts[tip], pts[mcp]) > math.dist(pts[pip], pts[mcp]) * 1.15
        for mcp, pip, tip in finger_joints
    ]
    thumb_extended = (
        math.dist(pts[4], pts[5]) > math.dist(pts[3], pts[5]) * 1.25
    )
    extended_count = sum(extended)
    hand_scale = math.dist(pts[0], pts[9])
    pinch_distance = math.dist(pts[4], pts[8])
    thumb_index_middle = (
        thumb_extended and extended[0] and extended[1] and not any(extended[2:])
    )

    if hand_scale > 0 and pinch_distance < hand_scale * 0.22:
        label = "PINCH"
    elif extended[0] and extended[1] and not any(extended[2:]) and not thumb_extended:
        label = "PEACE"
    elif extended_count == 3 or thumb_index_middle:
        label = "THREE_FINGERS"
    elif extended_count == 4 and thumb_extended:
        label = "OPEN_PALM"
    elif extended_count == 0 and not thumb_extended:
        label = "FIST"
    else:
        label = "NEUTRAL"
    cx = sum(p[0] for p in pts) // len(pts)
    cy = sum(p[1] for p in pts) // len(pts)
    return label, (cx, cy), pts

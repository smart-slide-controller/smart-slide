import unittest
import math
from src.gesture_engine import GestureEngine, classify_hand


class Landmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_hand(extended_fingers, thumb_extended=False, rotation=0):
    points = [(0.5, 0.5) for _ in range(21)]
    points[0] = (0.50, 0.90)
    finger_joints = [
        (5, 6, 8, (0.38, 0.62), (0.35, 0.46), (0.32, 0.20)),
        (9, 10, 12, (0.46, 0.59), (0.45, 0.42), (0.44, 0.14)),
        (13, 14, 16, (0.54, 0.60), (0.55, 0.43), (0.57, 0.17)),
        (17, 18, 20, (0.62, 0.64), (0.65, 0.48), (0.68, 0.23)),
    ]
    folded_tips = [(0.44, 0.68), (0.47, 0.66), (0.53, 0.67), (0.58, 0.69)]
    for index, (mcp, pip, tip, mcp_point, pip_point, tip_point) in enumerate(finger_joints):
        points[mcp] = mcp_point
        points[pip] = pip_point
        points[tip] = tip_point if index in extended_fingers else folded_tips[index]

    points[2] = (0.38, 0.70)
    points[3] = (0.31, 0.67) if thumb_extended else (0.50, 0.76)
    points[4] = (0.22, 0.62) if thumb_extended else (0.52, 0.78)

    radians = math.radians(rotation)
    cosine, sine = math.cos(radians), math.sin(radians)
    wrist_x, wrist_y = points[0]
    rotated_points = []
    for x, y in points:
        dx, dy = x - wrist_x, y - wrist_y
        rotated_points.append(
            Landmark(
                wrist_x + dx * cosine - dy * sine,
                wrist_y + dx * sine + dy * cosine,
            )
        )
    return rotated_points

class GestureEngineTests(unittest.TestCase):
    def test_activation_requires_hold(self):
        e = GestureEngine(90, .8, .5, .8)
        self.assertEqual(e.update(100, 100, "OPEN_PALM", now=1.0), [])
        events = e.update(101, 100, "OPEN_PALM", now=1.6)
        self.assertTrue(any(x.action == "ACTIVATE" for x in events))

    def test_open_palm_activates_and_fist_saves_screenshot_after_hold(self):
        e = GestureEngine(90, .8, .5, .8)
        e.update(100, 100, "OPEN_PALM", now=1.0)
        activated = e.update(100, 100, "OPEN_PALM", now=1.6)
        self.assertEqual([event.action for event in activated], ["ACTIVATE"])
        self.assertEqual(e.update(100, 100, "OPEN_PALM", now=1.8), [])

        self.assertEqual(e.update(100, 100, "FIST", now=2.0), [])
        screenshot = e.update(100, 100, "FIST", now=2.81)
        self.assertEqual([event.action for event in screenshot], ["SCREENSHOT"])
        self.assertTrue(e.gesture_active)
        self.assertEqual(e.update(100, 100, "FIST", now=3.0), [])

    def test_open_palm_can_activate_again_after_pose_changes(self):
        e = GestureEngine(90, .8, .5, .8)
        first = e.update(100, 100, "OPEN_PALM", now=1.0)
        first += e.update(100, 100, "OPEN_PALM", now=1.6)
        self.assertEqual([event.action for event in first], ["ACTIVATE"])

        self.assertEqual(e.update(100, 100, "NEUTRAL", now=1.7), [])
        self.assertEqual(e.update(100, 100, "OPEN_PALM", now=2.0), [])
        second = e.update(100, 100, "OPEN_PALM", now=2.6)
        self.assertEqual([event.action for event in second], ["ACTIVATE"])
        self.assertTrue(e.gesture_active)

    def test_swipe_only_when_active(self):
        e = GestureEngine(50, .1, .1, .2)
        e.gesture_active = True
        xs = [200, 180, 150, 120, 90]
        found = []
        for i, x in enumerate(xs):
            found += e.update(x, 100, "NEUTRAL", now=2 + i*.1)
        self.assertTrue(any(x.action == "NEXT" for x in found))

    def test_three_fingers_triggers_exit_after_hold(self):
        e = GestureEngine(90, .8, .5, .8, gesture_hold_seconds=.5)
        self.assertEqual(e.update(100, 100, "THREE_FINGERS", now=1.0), [])
        events = e.update(100, 100, "THREE_FINGERS", now=1.6)
        self.assertEqual([event.action for event in events], ["EXIT"])
        self.assertFalse(e.gesture_active)
        self.assertEqual(e.update(100, 100, "THREE_FINGERS", now=1.8), [])

    def test_peace_sign_screenshot_requires_active_control(self):
        e = GestureEngine(90, .8, .5, .8, gesture_hold_seconds=.5)
        self.assertEqual(e.update(100, 100, "PEACE", now=1.0), [])
        self.assertEqual(e.update(100, 100, "PEACE", now=1.6), [])

        e.gesture_active = True
        e.update(100, 100, "NEUTRAL", now=2.0)
        e.update(100, 100, "PEACE", now=2.1)
        events = e.update(100, 100, "PEACE", now=2.7)
        self.assertEqual([event.action for event in events], ["SCREENSHOT"])

    def test_classifies_peace_and_three_finger_shapes(self):
        peace, _, _ = classify_hand(make_hand({0, 1}), 640, 480)
        three_fingers, _, _ = classify_hand(
            make_hand({0, 1, 2}, thumb_extended=True), 640, 480
        )
        thumb_index_middle, _, _ = classify_hand(
            make_hand({0, 1}, thumb_extended=True), 640, 480
        )
        fist, _, _ = classify_hand(make_hand(set()), 640, 480)

        self.assertEqual(peace, "PEACE")
        self.assertEqual(three_fingers, "THREE_FINGERS")
        self.assertEqual(thumb_index_middle, "THREE_FINGERS")
        self.assertEqual(fist, "FIST")

    def test_classifies_open_palm_and_gestures_when_hand_is_rotated(self):
        for rotation in (0, 45, 90, 180, 270):
            with self.subTest(rotation=rotation):
                open_palm, _, _ = classify_hand(
                    make_hand({0, 1, 2, 3}, thumb_extended=True, rotation=rotation),
                    640,
                    480,
                )
                four_fingers_thumb_folded, _, _ = classify_hand(
                    make_hand({0, 1, 2, 3}, rotation=rotation), 640, 480
                )
                peace, _, _ = classify_hand(
                    make_hand({0, 1}, rotation=rotation), 640, 480
                )
                three_fingers, _, _ = classify_hand(
                    make_hand({0, 1, 2}, rotation=rotation), 640, 480
                )
                thumb_index_middle, _, _ = classify_hand(
                    make_hand({0, 1}, thumb_extended=True, rotation=rotation),
                    640,
                    480,
                )

                self.assertEqual(open_palm, "OPEN_PALM")
                self.assertNotEqual(four_fingers_thumb_folded, "OPEN_PALM")
                self.assertEqual(peace, "PEACE")
                self.assertEqual(three_fingers, "THREE_FINGERS")
                self.assertEqual(thumb_index_middle, "THREE_FINGERS")

if __name__ == "__main__":
    unittest.main()

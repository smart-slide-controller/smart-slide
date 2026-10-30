import cv2
import threading
import time
from src.gesture_engine import classify_hand

class CameraWorker:
    """Run the webcam in a background thread and detect hand gestures."""

    def __init__(self, settings, on_frame, on_gesture, on_status):
        # Save the app settings and callback functions.
        self.settings = settings
        self.on_frame = on_frame
        self.on_gesture = on_gesture
        self.on_status = on_status
        self._stop = threading.Event()
        self._thread = None
        self._cap = None

    @property
    def running(self):
        """Return True when the webcam thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """Start the camera thread if it is not already running."""
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the camera thread and free the webcam device."""
        self._stop.set()
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        self.on_status("Camera stopped")

    def _run(self):
        """Open the camera, watch for hands, and send frame + gesture updates."""
        cap = cv2.VideoCapture(self.settings.camera_index)
        self._cap = cap
        if not cap.isOpened():
            self.on_status("ERROR: Cannot access webcam. Check camera index/permissions.")
            cap.release()
            self._cap = None
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        try:
            import mediapipe as mp
            hands_api = mp.solutions.hands
            drawing = mp.solutions.drawing_utils
        except Exception as exc:
            self.on_status(f"ERROR: MediaPipe Hands unavailable: {exc}")
            cap.release()
            self._cap = None
            return
        self.on_status("Camera running")
        with hands_api.Hands(
            static_image_mode=False,
            max_num_hands=self.settings.max_hands,
            min_detection_confidence=self.settings.detection_confidence,
            min_tracking_confidence=self.settings.tracking_confidence,
        ) as hands:
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    self.on_status("Camera frame unavailable; retrying")
                    time.sleep(0.1)
                    continue
                if self.settings.mirror_camera:
                    frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb)
                label, center = "NO HAND", None
                if result.multi_hand_landmarks:
                    hand = result.multi_hand_landmarks[0]
                    drawing.draw_landmarks(frame, hand, hands_api.HAND_CONNECTIONS)
                    label, center, _ = classify_hand(hand.landmark, frame.shape[1], frame.shape[0])
                self.on_frame(frame, label)
                self.on_gesture(center, label, frame.shape[1], frame.shape[0])
        cap.release()
        self._cap = None
        self.on_status("Camera stopped")

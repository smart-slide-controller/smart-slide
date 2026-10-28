from dataclasses import dataclass

@dataclass
class Settings:
    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480
    mirror_camera: bool = True
    swipe_threshold_px: int = 90
    cooldown_seconds: float = 0.8
    activation_hold_seconds: float = 0.5
    fist_hold_seconds: float = 0.8
    feedback_enabled: bool = True
    max_hands: int = 1
    detection_confidence: float = 0.55
    tracking_confidence: float = 0.55

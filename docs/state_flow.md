# Presentation State Flow

```text
HOME
  └── Select valid file → FILE_SELECTED
        └── Start Presentation → PRESENTING
              ├── Open palm held → GESTURE_ACTIVE
              │     ├── Swipe right-to-left → NEXT_SLIDE
              │     ├── Swipe left-to-right → PREVIOUS_SLIDE
              │     └── Closed fist held → GESTURE_PAUSED
              │             └── Open palm held → GESTURE_ACTIVE
              └── Esc / Exit → HOME
```

# Gesture Mapping

| Gesture | Hold / motion | Implemented action |
|---|---|---|
| Open palm (all five fingers extended) | Hold about 0.5 seconds on the dashboard | Open the selected presentation |
| Open palm (all five fingers extended) | Hold about 0.5 seconds during a presentation | Activate gesture control |
| Right-to-left swipe | Horizontal movement reaches the configured threshold | Next slide |
| Left-to-right swipe | Horizontal movement reaches the configured threshold | Previous slide |
| Closed fist | Hold about 0.8 seconds | Save the current PowerPoint slide as a PNG |
| Three fingers (index, middle, ring; or thumb, index, middle) | Hold about 0.6 seconds | Exit the active presentation like `Esc` and return to the dashboard |
| Peace sign (index and middle fingers) | Hold about 0.6 seconds while control is active | Choose a save location for a PNG export of the current PowerPoint slide |
| Pinch (thumb and index finger) | Detected by the hand classifier | Feedback label only; it does not select anything |

Hold gestures trigger once per continuous pose. Change your hand pose or briefly move it out of view before repeating a hold. An open-palm hold can activate control or start a presentation again after returning to the dashboard, even if control was already active. One continuous swipe should cause only one navigation event. A cooldown and movement threshold reduce accidental actions.

Closed-fist and peace-sign image exports are available only for PowerPoint presentations. They export the slide content as a timestamped PNG in the `screenshots` folder beside the project (or packaged executable); this is not a screenshot of the whole desktop or PowerPoint controls. Three-finger exit works for both PowerPoint and PDF presentations.

Pointer mode and menu selection are not implemented. The current app has no pointer movement or selectable presentation menu actions, so Pinch must not be described as a working selection feature.

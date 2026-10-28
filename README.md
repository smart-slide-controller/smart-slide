# Smart Presentation Controller

A Windows desktop app for controlling PDF and PowerPoint presentations with hand gestures.

## Features

- Opens `.pptx` files in Microsoft PowerPoint Slide Show mode using Windows COM automation.
- Opens `.pdf` files in the built-in full-screen PDF viewer.
- Uses a webcam and MediaPipe hand tracking for gesture control.
- Keeps camera processing local; webcam frames are not recorded or uploaded.
- Supports keyboard controls in the PDF viewer.

## Requirements

- Windows 10 or later.
- Python 3.12 is recommended for the tested development environment.
- A webcam for hand tracking.
- Microsoft PowerPoint desktop installed to control `.pptx` slide shows.

PowerPoint COM control is Windows-only. The PDF viewer does not require Microsoft PowerPoint.

## Install and run from source

Open PowerShell in this project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

To create a new virtual environment instead:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Use the application

1. Choose a `.pptx` or `.pdf` file.
2. Start the camera. You can use the **Start presentation** button, or hold an open palm to open the selected file.
3. If you started from the button, hold an open palm to activate gesture navigation.
   To start another presentation after returning to the dashboard, change your hand pose
   briefly, then hold an open palm again.
4. Use a horizontal swipe to change slides.
5. Hold a fist to pause gesture navigation.
6. Hold three fingers to exit to the dashboard, or press `Esc` in the presentation.

PowerPoint files open in the actual Microsoft PowerPoint slide show. PDF files continue to use the app's own viewer.

## Gesture mapping

| Gesture | Action |
|---|---|
| All five fingers extended, held for about 0.5 seconds on the dashboard | Open the selected presentation |
| All five fingers extended, held for about 0.5 seconds during a presentation | Activate gesture control |
| Swipe right-to-left | Next slide |
| Swipe left-to-right | Previous slide |
| Closed fist held for about 0.8 seconds | Save the current PowerPoint slide as a PNG |
| Index, middle, and ring fingers raised, or thumb, index, and middle fingers raised, held for about 0.6 seconds | Exit the presentation like `Esc` and return to the dashboard |
| Peace sign held for about 0.6 seconds while control is active | Save the current PowerPoint slide as a PNG |
| Pinch thumb and index finger | Detection feedback only; no selection is performed |

Pointer mode and menu selection are not implemented. Do not treat Pinch as a working presentation selection command.
Closed-fist and peace-sign exports are available only for PowerPoint and save slide content, not a screenshot of the full desktop. Images are saved automatically in the `screenshots` folder beside the project when running from source, or beside the executable when packaged. Each image gets a timestamped filename.

In the PDF viewer, keyboard controls are:

- `Right Arrow`, `Page Down`, or `Space`: next slide
- `Left Arrow` or `Page Up`: previous slide
- `P`: pause or resume gesture control
- `H`: show gesture help
- `Esc`: exit the presentation

## Tests

Run the automated gesture tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

PowerPoint also has manual COM test scripts in the project root. They use a sample file at:

```text
%USERPROFILE%\Downloads\Broadsheet_presentation_design.pptx
```

Change the path in a test script if your sample presentation is stored elsewhere. Microsoft PowerPoint must be installed for these tests.

## Build a Windows executable

Install the build dependencies and create a one-folder build. The script uses a temporary short drive path to work around Windows path-length limits; build output still goes into this project folder.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build_exe.ps1
```

The executable is created at:

```text
dist\SmartPresentationController\SmartPresentationController.exe
```

Keep the full `dist\SmartPresentationController` folder when distributing the one-folder build. Microsoft PowerPoint desktop must still be installed on the target computer for `.pptx` control.

## Known limitations

- The application controls PowerPoint through Windows COM; it does not run PowerPoint files on non-Windows systems.
- Pointer movement and menu selection are not implemented.
- Pinch is detected for feedback only.
- Gestures should be tested in the intended room lighting and camera position before presenting.
- A packaged executable must be tested separately from the Python source before it is considered ready to submit.

## Project structure

```text
Smart_Presentation_Controller/
├── main.py
├── requirements.txt
├── requirements-build.txt
├── README.md
├── src/
├── tests/
├── docs/
├── cache/
└── dist/  # generated when packaging
```

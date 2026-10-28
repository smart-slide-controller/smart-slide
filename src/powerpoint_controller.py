
from pathlib import Path

import pythoncom
import win32com.client


class PowerPointController:
    """Control a PowerPoint presentation using Microsoft PowerPoint COM."""

    def __init__(self):
        self.app = None
        self.presentation = None
        self.slide_show = None
        self._com_initialized = False

    def open(self, file_path: str) -> int:
        """Open a PPTX file in PowerPoint Slide Show mode."""
        if self._com_initialized or self.presentation is not None:
            raise RuntimeError(
                "A presentation is already open in this controller."
            )

        path = Path(file_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(f"Presentation not found: {path}")

        if path.suffix.lower() != ".pptx":
            raise ValueError(
                "Only .pptx files are supported by this controller."
            )

        pythoncom.CoInitialize()
        self._com_initialized = True

        try:
            self.app = win32com.client.DispatchEx(
                "PowerPoint.Application"
            )

            self.app.Visible = True

            self.presentation = self.app.Presentations.Open(
                str(path),
                ReadOnly=True,
                Untitled=False,
                WithWindow=True,
            )

            self.presentation.SlideShowSettings.Run()
            self.slide_show = self.presentation.SlideShowWindow
            if self.slide_show is None:
                raise RuntimeError(
                    "PowerPoint started the slideshow, but no slideshow window was found."
                )

            return self.presentation.Slides.Count

        except Exception:
            self.close()
            raise

    def next_slide(self) -> bool:
        """Move to the next slide if one exists."""
        if self.slide_show is None or self.presentation is None:
            return False

        view = self.slide_show.View

        if view.CurrentShowPosition >= self.presentation.Slides.Count:
            return False

        view.Next()
        return True

    def previous_slide(self) -> bool:
        """Move to the previous slide if one exists."""
        if self.slide_show is None or self.presentation is None:
            return False

        view = self.slide_show.View

        if view.CurrentShowPosition <= 1:
            return False

        view.Previous()
        return True

    def current_slide_number(self) -> int:
        """Return the slide number currently displayed by this slideshow."""
        if self.slide_show is None or self.presentation is None:
            raise RuntimeError("No PowerPoint slideshow is active.")
        return self.slide_show.View.CurrentShowPosition

    def export_current_slide(self, file_path: str) -> Path:
        """Export the current PowerPoint slide as a PNG image."""
        if self.presentation is None:
            raise RuntimeError("No PowerPoint presentation is open.")

        path = Path(file_path).expanduser().resolve()
        if path.suffix.lower() != ".png":
            raise ValueError("Slide screenshots must use the .png file extension.")

        slide_number = self.current_slide_number()
        slide = self.presentation.Slides.Item(slide_number)
        slide.Export(str(path), "PNG")
        return path

    def close(self):
        """Close this controller's presentation and its dedicated PowerPoint instance."""
        try:
            if self.slide_show is not None:
                self.slide_show.View.Exit()
        except Exception:
            pass

        try:
            if self.presentation is not None:
                self.presentation.Close()
        except Exception:
            pass

        try:
            if self.app is not None:
                self.app.Quit()
        except Exception:
            pass

        self.slide_show = None
        self.presentation = None
        self.app = None

        if self._com_initialized:
            self._com_initialized = False
            pythoncom.CoUninitialize()

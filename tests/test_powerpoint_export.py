import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.powerpoint_controller import PowerPointController


class FakeSlide:
    def __init__(self):
        self.export_arguments = None

    def Export(self, file_path, image_format):
        self.export_arguments = (file_path, image_format)
        Path(file_path).write_bytes(b"png")


class FakeSlides:
    def __init__(self, slide):
        self.slide = slide
        self.requested_number = None

    def Item(self, slide_number):
        self.requested_number = slide_number
        return self.slide


class PowerPointExportTests(unittest.TestCase):
    def make_controller(self):
        slide = FakeSlide()
        slides = FakeSlides(slide)
        controller = PowerPointController()
        controller.presentation = SimpleNamespace(Slides=slides)
        controller.slide_show = SimpleNamespace(
            View=SimpleNamespace(CurrentShowPosition=2)
        )
        return controller, slide, slides

    def test_exports_the_current_slide_as_png(self):
        controller, slide, slides = self.make_controller()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "current_slide.png"

            saved_path = controller.export_current_slide(str(path))

            self.assertEqual(saved_path, path.resolve())
            self.assertEqual(slides.requested_number, 2)
            self.assertEqual(slide.export_arguments, (str(path.resolve()), "PNG"))
            self.assertEqual(path.read_bytes(), b"png")

    def test_rejects_non_png_export_path(self):
        controller, _, _ = self.make_controller()

        with self.assertRaisesRegex(ValueError, "must use the .png"):
            controller.export_current_slide("current_slide.jpg")

    def test_current_slide_requires_active_slideshow(self):
        controller = PowerPointController()

        with self.assertRaisesRegex(RuntimeError, "No PowerPoint slideshow"):
            controller.current_slide_number()

    def test_close_exits_slideshow_closes_document_and_quits_powerpoint(self):
        controller = PowerPointController()
        slide_show = SimpleNamespace(View=SimpleNamespace(Exit=Mock()))
        presentation = SimpleNamespace(Close=Mock())
        app = SimpleNamespace(Quit=Mock())
        controller.slide_show = slide_show
        controller.presentation = presentation
        controller.app = app

        controller.close()

        slide_show.View.Exit.assert_called_once_with()
        presentation.Close.assert_called_once_with()
        app.Quit.assert_called_once_with()
        self.assertIsNone(controller.slide_show)
        self.assertIsNone(controller.presentation)
        self.assertIsNone(controller.app)


if __name__ == "__main__":
    unittest.main()

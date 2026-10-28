import tempfile
import unittest
from pathlib import Path

import fitz

from src.presentation_loader import (
    PresentationLoadError,
    load_pdf,
    validate_presentation,
)


class PresentationLoaderTests(unittest.TestCase):
    def test_load_pdf_returns_path_and_page_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.pdf"
            document = fitz.open()
            document.new_page()
            document.new_page()
            document.save(path)
            document.close()

            loaded_path, page_count = load_pdf(str(path))

            self.assertEqual(loaded_path, path.resolve())
            self.assertEqual(page_count, 2)

    def test_load_pdf_rejects_powerpoint_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.pptx"
            path.write_bytes(b"pptx")

            with self.assertRaisesRegex(PresentationLoadError, "Open .pptx files in PowerPoint"):
                load_pdf(str(path))

    def test_load_pdf_rejects_invalid_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.pdf"
            path.write_text("not a PDF", encoding="utf-8")

            with self.assertRaisesRegex(PresentationLoadError, "Cannot open PDF"):
                load_pdf(str(path))

    def test_validate_presentation_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.pdf"

            with self.assertRaisesRegex(PresentationLoadError, "does not exist"):
                validate_presentation(str(path))


if __name__ == "__main__":
    unittest.main()

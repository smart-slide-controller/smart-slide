from pathlib import Path

import fitz

SUPPORTED = {".pdf", ".pptx"}


class PresentationLoadError(Exception):
    """Raised when the app cannot open or use the selected presentation file."""


def validate_presentation(path: str) -> Path:
    """Check that the file exists, is a supported file type, and is not empty."""
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise PresentationLoadError("The selected file does not exist.")
    if p.suffix.lower() not in SUPPORTED:
        raise PresentationLoadError("Unsupported file type. Choose a .pptx or .pdf file.")
    if p.stat().st_size == 0:
        raise PresentationLoadError("The selected file is empty.")
    return p


def load_pdf(path: str) -> tuple[Path, int]:
    """Open a PDF and return the file path plus the number of pages."""
    p = validate_presentation(path)
    if p.suffix.lower() != ".pdf":
        raise PresentationLoadError(
            "The built-in viewer supports PDF files. Open .pptx files in PowerPoint."
        )

    try:
        document = fitz.open(p)
    except Exception as exc:
        raise PresentationLoadError(f"Cannot open PDF: {exc}") from exc

    with document:
        page_count = len(document)

    if page_count < 1:
        raise PresentationLoadError("This PDF has no pages.")

    return p, page_count

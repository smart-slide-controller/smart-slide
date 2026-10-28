
from pathlib import Path

from src.powerpoint_controller import PowerPointController


def main():
    file_path = (
        Path.home()
        / "Downloads"
        / "Broadsheet_presentation_design.pptx"
    )

    controller = PowerPointController()

    try:
        print("Opening test presentation...")

        slide_count = controller.open(str(file_path))

        print("PowerPoint open: PASS")
        print(f"Slide count: {slide_count}")

        input(
            "Check that the slideshow is visible. "
            "Press Enter here to close only this test presentation..."
        )

    except Exception as error:
        print("PowerPoint test: FAIL")
        print(f"Error: {type(error).__name__}: {error}")

    finally:
        controller.close()
        print("Controller cleanup: DONE")


if __name__ == "__main__":
    main()


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
        count = controller.open(str(file_path))
        print("PowerPoint open: PASS")
        print("Slide count:", count)

        input("Check that slide 1 is visible, then press Enter for Next.")
        print("Calling next_slide()...")
        print("Next result:", controller.next_slide())
        print(
            "Current slide:",
            controller.slide_show.View.CurrentShowPosition
        )

        input("Check that slide 2 is visible, then press Enter for Previous.")
        print("Calling previous_slide()...")
        print("Previous result:", controller.previous_slide())
        print(
            "Current slide:",
            controller.slide_show.View.CurrentShowPosition
        )

        input("Press Enter to close this test presentation.")

    except Exception as error:
        print("Navigation test: FAIL")
        print(f"{type(error).__name__}: {error}")

    finally:
        controller.close()
        print("Controller cleanup: DONE")


if __name__ == "__main__":
    main()

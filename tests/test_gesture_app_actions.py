import unittest
import tempfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

from src.app import SmartPresentationApp
from src.gesture_engine import GestureEvent


class GestureAppActionTests(unittest.TestCase):
    def make_app(self, selected_file=None, presentation=None, powerpoint_controller=None):
        return SimpleNamespace(
            status=SimpleNamespace(set=Mock()),
            engine=SimpleNamespace(gesture_active=True),
            selected_file=selected_file,
            presentation=presentation,
            powerpoint_controller=powerpoint_controller,
            start_presentation=Mock(),
            exit_presentation=Mock(),
            _presentation_key=Mock(),
            _save_powerpoint_slide_screenshot=Mock(),
        )

    def test_open_palm_starts_selected_presentation_from_dashboard(self):
        app = self.make_app(selected_file="deck.pptx")

        SmartPresentationApp._handle_gesture_event(
            app, GestureEvent("ACTIVATE", "Gesture control active")
        )

        app.start_presentation.assert_called_once_with()

    def test_open_palm_without_file_does_not_start_and_can_retry(self):
        app = self.make_app()

        SmartPresentationApp._handle_gesture_event(
            app, GestureEvent("ACTIVATE", "Gesture control active")
        )

        app.start_presentation.assert_not_called()
        self.assertFalse(app.engine.gesture_active)

    def test_open_palm_during_presentation_activates_navigation(self):
        app = self.make_app(selected_file="deck.pptx", presentation=object())

        SmartPresentationApp._handle_gesture_event(
            app, GestureEvent("ACTIVATE", "Gesture control active")
        )

        app.start_presentation.assert_not_called()

    def test_three_fingers_exits_active_presentation(self):
        app = self.make_app(selected_file="deck.pdf", presentation=object())

        SmartPresentationApp._handle_gesture_event(
            app, GestureEvent("EXIT", "Three fingers: Exit presentation")
        )

        app._presentation_key.assert_called_once_with("ESCAPE")

    def test_three_fingers_without_presentation_does_not_exit_app(self):
        app = self.make_app()

        SmartPresentationApp._handle_gesture_event(
            app, GestureEvent("EXIT", "Three fingers: Exit presentation")
        )

        app.exit_presentation.assert_not_called()
        app._presentation_key.assert_not_called()

    def test_screenshot_is_saved_to_timestamped_screenshots_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = SimpleNamespace(
                current_slide_number=Mock(return_value=3),
                export_current_slide=Mock(side_effect=lambda path: Path(path)),
            )
            app = SimpleNamespace(
                powerpoint_controller=controller,
                status=SimpleNamespace(set=Mock()),
            )

            with patch("src.app.sys.executable", str(Path(temp_dir) / "app.exe")), patch(
                "src.app.sys.frozen", True, create=True
            ):
                SmartPresentationApp._save_powerpoint_slide_screenshot(app)

            controller.export_current_slide.assert_called_once()
            saved_path = Path(controller.export_current_slide.call_args.args[0])
            self.assertEqual(
                saved_path.parent,
                (Path(temp_dir) / "screenshots").resolve(),
            )
            self.assertRegex(saved_path.name, r"^slide_03_\d{8}_\d{6}_\d{6}\.png$")
            self.assertTrue(saved_path.parent.is_dir())
            app.status.set.assert_called_once_with(f"Saved slide screenshot: {saved_path}")

    def test_escape_action_exits_active_presentation(self):
        app = SimpleNamespace(
            presentation=object(),
            powerpoint_controller=None,
            exit_presentation=Mock(),
        )

        SmartPresentationApp._presentation_key(app, "ESCAPE")

        app.exit_presentation.assert_called_once_with()

    def test_presentation_only_hides_dashboard(self):
        app = SimpleNamespace(
            root=SimpleNamespace(withdraw=Mock())
        )

        SmartPresentationApp._show_presentation_only(app)

        app.root.withdraw.assert_called_once_with()

    def test_returning_to_dashboard_shows_and_focuses_app(self):
        app = SimpleNamespace(
            root=SimpleNamespace(
                deiconify=Mock(),
                lift=Mock(),
                focus_force=Mock(),
            )
        )

        SmartPresentationApp._show_dashboard(app)

        app.root.deiconify.assert_called_once_with()
        app.root.lift.assert_called_once_with()
        app.root.focus_force.assert_called_once_with()

    def test_powerpoint_start_hides_dashboard_before_opening_slideshow(self):
        order = []
        controller = SimpleNamespace(
            open=Mock(side_effect=lambda path: order.append("open") or 14),
            close=Mock(),
        )
        root = SimpleNamespace(
            withdraw=Mock(side_effect=lambda: order.append("hide")),
            update_idletasks=Mock(side_effect=lambda: order.append("update")),
        )
        app = SimpleNamespace(
            selected_file="deck.pptx",
            presentation=None,
            powerpoint_controller=None,
            root=root,
            status=SimpleNamespace(set=Mock()),
            engine=SimpleNamespace(gesture_active=True),
            camera=SimpleNamespace(running=True),
            _show_presentation_only=lambda: root.withdraw(),
            _show_dashboard=Mock(),
            _schedule_powerpoint_monitor=Mock(),
            start_camera=Mock(),
            _close_active_presentation=Mock(),
        )

        with patch("src.app.PowerPointController", return_value=controller):
            SmartPresentationApp.start_presentation(app)

        self.assertEqual(order, ["hide", "update", "open"])
        self.assertIs(app.powerpoint_controller, controller)
        app._show_dashboard.assert_not_called()

    def test_failed_powerpoint_start_restores_dashboard(self):
        controller = SimpleNamespace(
            open=Mock(side_effect=RuntimeError("PowerPoint unavailable")),
            close=Mock(),
        )
        root = SimpleNamespace(withdraw=Mock(), update_idletasks=Mock())
        app = SimpleNamespace(
            selected_file="deck.pptx",
            presentation=None,
            powerpoint_controller=None,
            root=root,
            status=SimpleNamespace(set=Mock()),
            engine=SimpleNamespace(gesture_active=True),
            camera=SimpleNamespace(running=True),
            _show_presentation_only=lambda: root.withdraw(),
            _show_dashboard=Mock(),
            _schedule_powerpoint_monitor=Mock(),
            start_camera=Mock(),
            _close_active_presentation=Mock(),
        )

        with (
            patch("src.app.PowerPointController", return_value=controller),
            patch("src.app.messagebox.showerror") as showerror,
        ):
            SmartPresentationApp.start_presentation(app)

        controller.close.assert_called_once_with()
        app._show_dashboard.assert_called_once_with()
        showerror.assert_called_once()


if __name__ == "__main__":
    unittest.main()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import cv2
import time
import sys
from datetime import datetime
from src.settings import Settings
from src.presentation_loader import validate_presentation, load_pdf, PresentationLoadError
from src.gesture_engine import GestureEngine
from src.camera import CameraWorker
from src.presentation_view import PresentationView
from src.powerpoint_controller import PowerPointController

class SmartPresentationApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Presentation Controller")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)
        self.settings = Settings()
        self.selected_file = None
        self.pdf_path = None
        self.camera = None
        self.presentation = None
        self.powerpoint_controller = None
        self._powerpoint_monitor_id = None
        self.last_frame_photo = None
        self.last_gesture = "Waiting for hand"
        self.status = tk.StringVar(value="Ready — select a PowerPoint or PDF file.")
        self.engine = GestureEngine(
            self.settings.swipe_threshold_px, self.settings.cooldown_seconds,
            self.settings.activation_hold_seconds, self.settings.fist_hold_seconds
        )
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def _build_ui(self):
        palette = {
            "background": "#080e1b",
            "surface": "#111b2d",
            "raised": "#17243a",
            "muted": "#8fa1ba",
            "text": "#f4f7fb",
            "accent": "#6366f1",
            "green": "#10b981",
        }
        self.palette = palette
        self.root.configure(bg=palette["background"])

        header = tk.Frame(self.root, bg=palette["background"], padx=32, pady=18)
        header.pack(fill="x")
        brand = tk.Frame(header, bg=palette["background"])
        brand.pack(side="left", anchor="w")
        tk.Label(brand, text="SMART PRESENTATION", bg=palette["background"],
                 fg=palette["text"], font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(brand, text="Touchless control for PowerPoint and PDF",
                 bg=palette["background"], fg=palette["muted"],
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        tk.Label(header, text="●  RUNS LOCALLY", bg="#102a2a", fg="#6ee7b7",
                 padx=12, pady=7, font=("Segoe UI", 9, "bold")).pack(side="right", anchor="n")

        body = tk.Frame(self.root, bg=palette["background"], padx=32)
        body.pack(fill="both", expand=True, pady=(0, 12))
        left = tk.Frame(body, bg=palette["surface"], padx=22, pady=20)
        left.pack(side="left", fill="both", expand=True, padx=(0, 18))
        right = tk.Frame(body, bg=palette["surface"], padx=18, pady=16, width=340)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(left, text="YOUR PRESENTATION", bg=palette["surface"],
                 fg="#a5b4fc", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(left, text="Ready for your next talk?", bg=palette["surface"],
                 fg=palette["text"], font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(5, 3))
        tk.Label(left, text="Choose a deck, then use simple hand gestures to move through it.",
                 bg=palette["surface"], fg=palette["muted"], font=("Segoe UI", 10),
                 wraplength=520, justify="left").pack(anchor="w", pady=(0, 20))

        file_card = tk.Frame(left, bg=palette["raised"], padx=16, pady=16)
        file_card.pack(fill="x")
        file_heading = tk.Frame(file_card, bg=palette["raised"])
        file_heading.pack(fill="x")
        tk.Label(file_heading, text="SELECTED DECK", bg=palette["raised"],
                 fg=palette["muted"], font=("Segoe UI", 9, "bold")).pack(side="left")
        self.file_state = tk.Label(file_heading, text="NO FILE", bg="#263449",
                                  fg="#cbd5e1", padx=8, pady=3,
                                  font=("Segoe UI", 8, "bold"))
        self.file_state.pack(side="right")
        self.file_title = tk.Label(file_card, text="No presentation selected",
                                   bg=palette["raised"], fg=palette["text"],
                                   font=("Segoe UI", 12, "bold"), anchor="w",
                                   wraplength=500, justify="left")
        self.file_title.pack(fill="x", pady=(12, 3))
        self.file_details = tk.Label(file_card, text="PPTX and PDF files are supported",
                                     bg=palette["raised"], fg=palette["muted"],
                                     font=("Segoe UI", 9), anchor="w",
                                     wraplength=500, justify="left")
        self.file_details.pack(fill="x")

        file_actions = tk.Frame(left, bg=palette["surface"])
        file_actions.pack(fill="x", pady=(14, 0))
        self._button(file_actions, "Choose presentation", self.select_file,
                     palette["accent"]).pack(side="left")
        self.remove_button = self._button(file_actions, "Remove", self.remove_file, "#28364a")
        self.remove_button.pack(side="left", padx=(9, 0))
        self.remove_button.configure(state="disabled", disabledforeground="#64748b")

        self.start_button = self._button(left, "Start presentation  →",
                                         self.start_presentation, palette["green"])
        self.start_button.pack(fill="x", pady=(16, 0))
        self.start_button.configure(state="disabled", disabledforeground="#a7b3c2")

        guide_header = tk.Frame(left, bg=palette["surface"])
        guide_header.pack(fill="x", pady=(18, 8))
        tk.Label(guide_header, text="GESTURE QUICK GUIDE", bg=palette["surface"],
                 fg=palette["text"], font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(guide_header, text="KEYBOARD FALLBACK INCLUDED",
                 bg=palette["surface"], fg=palette["muted"],
                 font=("Segoe UI", 8, "bold")).pack(side="right")

        guide = [
            ("OPEN PALM", "Open selected deck / activate control"),
            ("SWIPE RIGHT → LEFT", "Go to the next slide"),
            ("SWIPE LEFT → RIGHT", "Go to the previous slide"),
            ("CLOSED FIST", "Hold to save the current PowerPoint slide"),
            ("THREE FINGERS", "Hold to exit like Esc"),
            ("PEACE SIGN ✌", "Activate control, then hold to save the PowerPoint slide"),
        ]
        for gesture, action in guide:
            row = tk.Frame(left, bg=palette["surface"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=gesture, bg=palette["surface"], fg="#c7d2fe",
                     width=22, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left")
            tk.Label(row, text=action, bg=palette["surface"], fg="#d1d9e6",
                     anchor="w", font=("Segoe UI", 9), wraplength=310,
                     justify="left").pack(side="left", fill="x", expand=True)
        tk.Label(left, text="Keyboard: ← / → or Space to navigate • P to pause • Esc to exit",
                 bg=palette["surface"], fg=palette["muted"],
                 font=("Segoe UI", 9), wraplength=520,
                 justify="left").pack(anchor="w", pady=(8, 0))

        camera_header = tk.Frame(right, bg=palette["surface"])
        camera_header.pack(fill="x")
        tk.Label(camera_header, text="CAMERA", bg=palette["surface"],
                 fg=palette["text"], font=("Segoe UI", 13, "bold")).pack(side="left")
        self.camera_status = tk.Label(camera_header, text="● OFF", bg="#263449",
                                      fg="#cbd5e1", padx=9, pady=4,
                                      font=("Segoe UI", 8, "bold"))
        self.camera_status.pack(side="right")
        tk.Label(right, text="Preview is processed on this device",
                 bg=palette["surface"], fg=palette["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 12))

        self.preview = tk.Label(right, text="Camera is off\n\nStart the camera to see the preview",
                                bg="#070c15", fg="#8392a8", width=36, height=10,
                                font=("Segoe UI", 10), justify="center")
        self.preview.pack(fill="x")

        gesture_card = tk.Frame(right, bg=palette["raised"], padx=12, pady=10)
        gesture_card.pack(fill="x", pady=(12, 8))
        tk.Label(gesture_card, text="DETECTED GESTURE", bg=palette["raised"],
                 fg=palette["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.gesture_text = tk.StringVar(value="Waiting for camera")
        self.gesture_label = tk.Label(gesture_card, textvariable=self.gesture_text,
                                      bg=palette["raised"], fg="#6ee7b7",
                                      font=("Segoe UI", 11, "bold"), anchor="w")
        self.gesture_label.pack(anchor="w", pady=(4, 0))
        tk.Label(right, textvariable=self.status, bg=palette["surface"],
                 fg="#cbd5e1", wraplength=290, justify="left",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 12))

        controls = tk.Frame(right, bg=palette["surface"])
        controls.pack(fill="x")
        for column in range(2):
            controls.columnconfigure(column, weight=1, uniform="camera-controls")
        for row, (label, command, color) in enumerate((
            ("Start camera", self.start_camera, "#2563eb"),
            ("Stop camera", self.stop_camera, "#374151"),
            ("Settings", self.open_settings, "#374151"),
            ("Exit app", self.close_app, "#7f1d1d"),
        )):
            self._button(controls, label, command, color).grid(
                row=row // 2, column=row % 2, sticky="ew",
                padx=(0 if row % 2 == 0 else 4, 4 if row % 2 == 0 else 0),
                pady=3,
            )

        footer = tk.Frame(self.root, bg="#0d1728", padx=32, pady=11)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="Your original presentation is never modified. Webcam frames are not saved.",
                 bg="#0d1728", fg="#9eb0c8",
                 font=("Segoe UI", 9)).pack(anchor="w")

    def _button(self, parent, text, command, color):
        return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                         activebackground=color, activeforeground="white",
                         relief="flat", padx=13, pady=9, cursor="hand2",
                         font=("Segoe UI", 10, "bold"))

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Select a presentation",
            filetypes=[("PowerPoint and PDF", "*.pptx *.pdf"), ("PowerPoint", "*.pptx"), ("PDF", "*.pdf")]
        )
        if not path:
            return
        try:
            p = validate_presentation(path)
            self.selected_file = str(p)
            self.pdf_path = None
            suffix_note = "PDF pages" if p.suffix.lower() == ".pdf" else "PowerPoint Slide Show"
            self.file_title.configure(text=p.name)
            self.file_details.configure(
                text=f"{p.suffix.upper()}  •  {p.stat().st_size / (1024 * 1024):.1f} MB  •  {suffix_note}"
            )
            self.file_state.configure(text="READY", bg="#123b35", fg="#6ee7b7")
            self.start_button.configure(state="normal")
            self.remove_button.configure(state="normal")
            self.status.set("File selected and validated. Start presentation when ready.")
        except PresentationLoadError as exc:
            messagebox.showerror("Invalid presentation", str(exc))

    def remove_file(self):
        self.selected_file = self.pdf_path = None
        self.file_title.configure(text="No presentation selected")
        self.file_details.configure(text="PPTX and PDF files are supported")
        self.file_state.configure(text="NO FILE", bg="#263449", fg="#cbd5e1")
        self.start_button.configure(state="disabled")
        self.remove_button.configure(state="disabled")
        self.status.set("Presentation removed.")

    def start_presentation(self):
        if not self.selected_file:
            messagebox.showwarning("No file", "Please select a .pptx or .pdf file first.")
            return
        if self.presentation or self.powerpoint_controller:
            self.status.set("A presentation is already open. Exit it before starting another.")
            return

        is_powerpoint = Path(self.selected_file).suffix.lower() == ".pptx"
        dashboard_hidden = False
        try:
            if is_powerpoint:
                self._show_presentation_only()
                self.root.update_idletasks()
                dashboard_hidden = True
                controller = PowerPointController()
                try:
                    count = controller.open(self.selected_file)
                except Exception:
                    controller.close()
                    raise
                self.powerpoint_controller = controller
            else:
                pdf_path, count = load_pdf(self.selected_file)
                self.pdf_path = str(pdf_path)
                self.presentation = PresentationView(
                    self.root, self.pdf_path, self.exit_presentation, self._presentation_key
                )

            gesture_hint = (
                "Gesture control is active. Swipe to navigate."
                if self.engine.gesture_active
                else "Hold open palm to activate gesture control."
            )
            self.status.set(f"Presentation started: {count} slides/pages. {gesture_hint}")
            if self.powerpoint_controller:
                self._schedule_powerpoint_monitor()
            if not self.camera or not self.camera.running:
                self.start_camera()
            if not is_powerpoint:
                self._show_presentation_only()
        except PresentationLoadError as exc:
            if self.presentation or self.powerpoint_controller:
                self._close_active_presentation()
            if dashboard_hidden:
                self._show_dashboard()
            messagebox.showerror("Cannot start presentation", str(exc))
        except Exception as exc:
            if self.presentation or self.powerpoint_controller:
                self._close_active_presentation()
            if dashboard_hidden:
                self._show_dashboard()
            messagebox.showerror("Presentation error", f"Could not start presentation:\n{exc}")

    def _show_presentation_only(self):
        self.root.withdraw()

    def _show_dashboard(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def start_camera(self):
        if self.camera and self.camera.running:
            self.status.set("Camera is already running.")
            return
        self._set_camera_status("STARTING")
        self.gesture_text.set("Waiting for camera")
        self.camera = CameraWorker(self.settings, self._on_frame_threadsafe,
                                   self._on_gesture_threadsafe, self._on_status_threadsafe)
        self.camera.start()

    def stop_camera(self):
        if self.camera:
            self.camera.stop()
            self.camera = None
        self.engine.reset()
        self.preview.configure(image="", text="Camera is off\n\nStart the camera to see the preview")
        self.last_frame_photo = None
        self.gesture_text.set("Waiting for camera")
        self._set_camera_status("OFF")
        self.status.set("Camera stopped. Gesture commands are disabled.")

    def _set_camera_status(self, state):
        styles = {
            "STARTING": ("● STARTING", "#3b2e18", "#fcd34d"),
            "RUNNING": ("● ON", "#123b35", "#6ee7b7"),
            "ERROR": ("● ERROR", "#451f2a", "#fda4af"),
            "OFF": ("● OFF", "#263449", "#cbd5e1"),
        }
        text, background, foreground = styles[state]
        self.camera_status.configure(text=text, bg=background, fg=foreground)

    def _update_status(self, status):
        self.status.set(status)
        normalized = status.lower()
        if normalized.startswith("error:"):
            self._set_camera_status("ERROR")
        elif normalized == "camera running":
            self._set_camera_status("RUNNING")
        elif normalized == "camera stopped":
            self._set_camera_status("OFF")

    def _on_frame_threadsafe(self, frame, label):
        self.root.after(0, self._update_preview, frame, label)

    def _update_preview(self, frame, label):
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            image.thumbnail((285, 170))
            self.last_frame_photo = ImageTk.PhotoImage(image)
            self.preview.configure(
            image=self.last_frame_photo,
            text="",
            width=image.width,
            height=image.height
            )
            self.gesture_text.set(f"Gesture: {label}")
        except tk.TclError:
            pass

    def _on_gesture_threadsafe(self, center, label, width, height):
        events = self.engine.update(center[0] if center else None, center[1] if center else None, label)
        for event in events:
            self.root.after(0, self._handle_gesture_event, event)

    def _handle_gesture_event(self, event):
        self.status.set(event.label)
        if event.action == "ACTIVATE":
            if self.presentation or self.powerpoint_controller:
                self.status.set("Gesture control ACTIVE. Swipe to navigate.")
            elif self.selected_file:
                self.status.set("Open palm detected. Starting selected presentation.")
                self.start_presentation()
            else:
                self.engine.gesture_active = False
                self.status.set("Select a presentation before using Open Palm to start it.")
        elif event.action == "PAUSE":
            self.status.set("Gesture control PAUSED. Hold open palm to activate.")
        elif event.action == "EXIT":
            if self.presentation or self.powerpoint_controller:
                self._presentation_key("ESCAPE")
            else:
                self.status.set("No active presentation to exit.")
        elif event.action == "NEXT":
            self._presentation_key("NEXT")
        elif event.action == "PREVIOUS":
            self._presentation_key("PREVIOUS")
        elif event.action == "SCREENSHOT":
            self._save_powerpoint_slide_screenshot()

    def _save_powerpoint_slide_screenshot(self):
        controller = self.powerpoint_controller
        if not controller:
            self.status.set("Slide screenshot is available only during a PowerPoint slideshow.")
            return

        try:
            slide_number = controller.current_slide_number()
        except Exception as exc:
            messagebox.showerror("Screenshot unavailable", f"Could not read the current slide:\n{exc}")
            return

        try:
            app_directory = (
                Path(sys.executable).resolve().parent
                if getattr(sys, "frozen", False)
                else Path(__file__).resolve().parent.parent
            )
            screenshot_directory = app_directory / "screenshots"
            screenshot_directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = screenshot_directory / f"slide_{slide_number:02}_{timestamp}.png"
            saved_path = controller.export_current_slide(str(path))
            self.status.set(f"Saved slide screenshot: {saved_path}")
        except Exception as exc:
            messagebox.showerror("Screenshot failed", f"Could not save the slide image:\n{exc}")

    def _on_status_threadsafe(self, status):
        self.root.after(0, self._update_status, status)

    def _presentation_key(self, action):
        if not self.presentation and not self.powerpoint_controller:
            return
        if action == "NEXT":
            try:
                moved = (
                    self.powerpoint_controller.next_slide()
                    if self.powerpoint_controller
                    else self.presentation.next()
                )
            except Exception as exc:
                self.exit_presentation()
                self.status.set(f"PowerPoint slideshow ended or unavailable: {exc}")
                return
            if not moved:
                self.status.set("Already on the final slide.")
        elif action == "PREVIOUS":
            try:
                moved = (
                    self.powerpoint_controller.previous_slide()
                    if self.powerpoint_controller
                    else self.presentation.previous()
                )
            except Exception as exc:
                self.exit_presentation()
                self.status.set(f"PowerPoint slideshow ended or unavailable: {exc}")
                return
            if not moved:
                self.status.set("Already on the first slide.")
        elif action == "PAUSE_TOGGLE":
            self.engine.gesture_active = not self.engine.gesture_active
            self.status.set("Gesture control ACTIVE" if self.engine.gesture_active else "Gesture control PAUSED")
        elif action == "ESCAPE":
            self.exit_presentation()
        elif action == "HELP":
            self.status.set("Swipe right-to-left: Next; left-to-right: Previous; P: Pause; Esc: Exit")

    def exit_presentation(self):
        self._close_active_presentation()
        self.status.set("Returned to dashboard.")
        self._show_dashboard()

    def _close_active_presentation(self):
        if self._powerpoint_monitor_id is not None:
            try:
                self.root.after_cancel(self._powerpoint_monitor_id)
            except tk.TclError:
                pass
            self._powerpoint_monitor_id = None
        if self.presentation:
            self.presentation.close()
            self.presentation = None
        if self.powerpoint_controller:
            self.powerpoint_controller.close()
            self.powerpoint_controller = None

    def _schedule_powerpoint_monitor(self):
        if self.powerpoint_controller and self._powerpoint_monitor_id is None:
            self._powerpoint_monitor_id = self.root.after(
                500, self._check_powerpoint_slideshow
            )

    def _check_powerpoint_slideshow(self):
        self._powerpoint_monitor_id = None
        controller = self.powerpoint_controller
        if not controller:
            return
        try:
            position = controller.slide_show.View.CurrentShowPosition
            if position < 1:
                raise RuntimeError("PowerPoint slideshow is no longer active.")
        except Exception as exc:
            self._close_active_presentation()
            self._show_dashboard()
            self.status.set(f"PowerPoint slideshow closed. Returned to dashboard. ({exc})")
            return
        self._schedule_powerpoint_monitor()

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.configure(bg="#111b31")
        win.resizable(False, False)
        fields = [
            ("Camera index", "camera_index", int),
            ("Swipe threshold (px)", "swipe_threshold_px", int),
            ("Cooldown seconds", "cooldown_seconds", float),
            ("Detection confidence (0-1)", "detection_confidence", float),
            ("Tracking confidence (0-1)", "tracking_confidence", float),
        ]
        vars_ = {}
        for i, (label, attr, typ) in enumerate(fields):
            tk.Label(win, text=label, bg="#111b31", fg="white", padx=12, pady=8).grid(row=i, column=0, sticky="w")
            var = tk.StringVar(value=str(getattr(self.settings, attr)))
            vars_[attr] = (var, typ)
            tk.Entry(win, textvariable=var, width=18).grid(row=i, column=1, padx=12, pady=6)
        mirror = tk.BooleanVar(value=self.settings.mirror_camera)
        tk.Checkbutton(win, text="Mirror camera preview", variable=mirror, bg="#111b31", fg="white",
                       selectcolor="#111b31", activebackground="#111b31").grid(row=len(fields), column=0, columnspan=2, sticky="w", padx=12, pady=6)
        def save():
            try:
                new = {}
                for attr, (var, typ) in vars_.items():
                    new[attr] = typ(var.get())
                if new["camera_index"] < 0 or new["swipe_threshold_px"] < 20:
                    raise ValueError("Camera index must be >= 0 and swipe threshold >= 20.")
                if not 0 <= new["detection_confidence"] <= 1 or not 0 <= new["tracking_confidence"] <= 1:
                    raise ValueError("Confidence values must be between 0 and 1.")
                if new["cooldown_seconds"] < 0:
                    raise ValueError("Cooldown cannot be negative.")
                for k, v in new.items():
                    setattr(self.settings, k, v)
                self.settings.mirror_camera = mirror.get()
                self.engine.swipe_threshold_px = self.settings.swipe_threshold_px
                self.engine.cooldown_seconds = self.settings.cooldown_seconds
                self.engine.activation_hold_seconds = self.settings.activation_hold_seconds
                self.engine.fist_hold_seconds = self.settings.fist_hold_seconds
                messagebox.showinfo("Settings", "Settings saved. Restart camera to apply camera settings.")
                win.destroy()
            except Exception as exc:
                messagebox.showerror("Invalid settings", str(exc))
        self._button(win, "Save Settings", save, "#059669").grid(row=len(fields)+1, column=0, columnspan=2, padx=12, pady=12, sticky="ew")

    def close_app(self):
        try:
            self.stop_camera()
        except Exception:
            pass
        self._close_active_presentation()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

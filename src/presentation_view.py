import tkinter as tk
from PIL import Image, ImageTk
import fitz

class PresentationView:
    def __init__(self, root, pdf_path, on_exit, on_key, counter_visible=True):
        self.root = root
        self.pdf_path = pdf_path
        self.on_exit = on_exit
        self.on_key = on_key
        self.doc = fitz.open(pdf_path)
        self.index = 0
        self.counter_visible = counter_visible
        self.window = tk.Toplevel(root)
        self.window.configure(bg="black")
        self.window.attributes("-fullscreen", True)
        self.window.bind("<Escape>", lambda e: self.on_key("ESCAPE"))
        self.window.bind("<Key>", self._key)
        self.window.bind("<Configure>", lambda e: self._render())
        self.image_label = tk.Label(self.window, bg="black")
        self.image_label.pack(fill="both", expand=True)
        self.counter = tk.Label(self.window, bg="#111827", fg="white",
                                font=("Segoe UI", 15), padx=12, pady=6)
        if counter_visible:
            self.counter.place(relx=0.98, rely=0.03, anchor="ne")
        self.help_label = tk.Label(self.window, bg="#111827", fg="white",
                                   text="← Previous   → Next   P Pause   H Help   Esc Exit",
                                   font=("Segoe UI", 12), padx=12, pady=6)
        self.help_label.place(relx=0.02, rely=0.97, anchor="sw")
        self._photo = None
        self._render()
        self.window.focus_force()

    @property
    def total(self):
        return len(self.doc)

    def _key(self, event):
        key = event.keysym.lower()
        if key in ("right", "space", "pagedown"):
            self.on_key("NEXT")
        elif key in ("left", "pageup"):
            self.on_key("PREVIOUS")
        elif key == "p":
            self.on_key("PAUSE_TOGGLE")
        elif key == "h":
            self.help_label.place(relx=0.02, rely=0.97, anchor="sw")

    def next(self):
        if self.index < self.total - 1:
            self.index += 1
            self._render()
            return True
        return False

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self._render()
            return True
        return False

    def _render(self):
        if not self.window.winfo_exists():
            return
        width = max(320, self.window.winfo_width())
        height = max(240, self.window.winfo_height())
        try:
            page = self.doc.load_page(self.index)
            rect = page.rect
            scale = min((width - 24) / rect.width, (height - 70) / rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self._photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=self._photo)
            self.counter.configure(text=f"Slide {self.index + 1} / {self.total}")
        except Exception as exc:
            self.image_label.configure(text=f"Could not render slide: {exc}", fg="white")
    def close(self):
        try:
            self.doc.close()
        except Exception:
            pass
        if self.window.winfo_exists():
            self.window.destroy()

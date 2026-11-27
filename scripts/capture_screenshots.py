"""Capture high-DPI screenshots of ModernTtk's ShowcaseApp for README.md.

Run from the repository root:
    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys
import traceback

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import demo  # noqa: E402
import modernttk as mtk  # noqa: E402

OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _grab_window(app: demo.ShowcaseApp, path: Path) -> None:
    app.update_idletasks()
    app.update()
    if sys.platform == "win32":
        hwnd = ctypes.windll.user32.GetParent(app.winfo_id()) or app.winfo_id()
        img = ImageGrab.grab(window=hwnd)
    else:
        x1 = app.winfo_rootx()
        y1 = app.winfo_rooty()
        x2 = x1 + app.winfo_width()
        y2 = y1 + app.winfo_height()
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    img.save(path, format="PNG", optimize=True)
    print(f"Saved {path.relative_to(ROOT)} ({img.width}x{img.height})")


def main() -> None:
    app = demo.ShowcaseApp()
    app.geometry("1280x860+40+40")
    app.lift()
    app.attributes("-topmost", True)
    error_holder: list[BaseException] = []

    shots = [
        ("Components", "fluent_dark", OUT_DIR / "components_dark.png"),
        ("Components", "fluent_light", OUT_DIR / "components_light.png"),
        ("Gauges Gallery", "fluent_dark", OUT_DIR / "gauges_gallery_dark.png"),
        ("Enterprise & RCCP", "fluent_dark", OUT_DIR / "enterprise_datastream_dark.png"),
    ]

    def _run_shot(idx: int = 0) -> None:
        try:
            if idx >= len(shots):
                app.destroy()
                return
            page, theme, out_path = shots[idx]
            if mtk.get_theme() != theme:
                mtk.set_theme(theme, root=app)
                app.theme_combo.set(theme, notify=False)
            app._switch_page(page)
            app.update_idletasks()
            app.update()

            # Wait briefly so animated gauges / DataStream / ActivityTimer render mid-motion
            def _snap() -> None:
                try:
                    _grab_window(app, out_path)
                    app.after(220, lambda: _run_shot(idx + 1))
                except BaseException as exc:  # noqa: BLE001
                    error_holder.append(exc)
                    traceback.print_exc()
                    app.destroy()

            app.after(450, _snap)
        except BaseException as exc:  # noqa: BLE001
            error_holder.append(exc)
            traceback.print_exc()
            app.destroy()

    app.after(600, _run_shot)
    app.mainloop()
    if error_holder:
        sys.exit(1)


if __name__ == "__main__":
    main()

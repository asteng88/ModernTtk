"""Procedural 4x supersampled vector icon renderer for ModernTtk.

Generates crisp, theme-colored PhotoImage icons in memory using Pillow (PIL.ImageDraw)
with zero external asset files required.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageTk

from .utils import _is_photo_valid, hex_to_rgb

_ICON_PHOTO_CACHE: Dict[Tuple, ImageTk.PhotoImage] = {}

AVAILABLE_ICONS = (
    "search",
    "check",
    "close",
    "plus",
    "minus",
    "chevron_down",
    "chevron_up",
    "chevron_left",
    "chevron_right",
    "settings",
    "sun",
    "moon",
    "user",
    "lock",
    "eye",
    "eye_off",
    "calendar",
    "download",
    "upload",
    "trash",
    "refresh",
    "info",
    "warning",
    "filter",
    "folder",
    "terminal",
    "sliders",
    "sparkles",
    "chart",
    "layers",
    "zap",
    "users",
    "database",
    "clock",
    "excel_export",
    "activity",
    "edit",
    "link",
    "unlink",
    "swap",
    "arrow_right",
)


def clear_icon_cache() -> None:
    """Clear cached icon PhotoImage instances."""
    _ICON_PHOTO_CACHE.clear()


@lru_cache(maxsize=512)
def _render_icon_pil(
    name: str,
    size: int = 16,
    color_hex: str = "#ffffff",
    stroke_width: float = 1.8,
    scale: int = 4,
) -> Image.Image:
    """Render a vector icon at 4x supersampled resolution and downsample with LANCZOS."""
    w = max(8, size) * scale
    h = max(8, size) * scale
    sw = max(2, int(round(stroke_width * scale)))
    rgba = (*hex_to_rgb(color_hex), 255)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def p(nx: float, ny: float) -> Tuple[float, float]:
        return (nx * w, ny * h)

    icon_key = name.lower().strip()

    if icon_key == "search":
        # Magnifying glass circle + handle
        r_box = [w * 0.14, h * 0.14, w * 0.68, h * 0.68]
        draw.ellipse(r_box, outline=rgba, width=sw)
        draw.line([p(0.60, 0.60), p(0.86, 0.86)], fill=rgba, width=sw)

    elif icon_key == "check":
        draw.line([p(0.18, 0.52), p(0.42, 0.76), p(0.84, 0.26)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "close":
        draw.line([p(0.22, 0.22), p(0.78, 0.78)], fill=rgba, width=sw)
        draw.line([p(0.78, 0.22), p(0.22, 0.78)], fill=rgba, width=sw)

    elif icon_key == "plus":
        draw.line([p(0.50, 0.18), p(0.50, 0.82)], fill=rgba, width=sw)
        draw.line([p(0.18, 0.50), p(0.82, 0.50)], fill=rgba, width=sw)

    elif icon_key == "minus":
        draw.line([p(0.20, 0.50), p(0.80, 0.50)], fill=rgba, width=sw)

    elif icon_key == "chevron_down":
        draw.line([p(0.22, 0.36), p(0.50, 0.66), p(0.78, 0.36)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "chevron_up":
        draw.line([p(0.22, 0.64), p(0.50, 0.34), p(0.78, 0.64)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "chevron_left":
        draw.line([p(0.64, 0.22), p(0.34, 0.50), p(0.64, 0.78)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "chevron_right":
        draw.line([p(0.36, 0.22), p(0.66, 0.50), p(0.36, 0.78)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "settings":
        # Gear teeth + inner ring
        cx, cy = w * 0.5, h * 0.5
        for i in range(8):
            ang = i * (math.pi / 4.0)
            x1 = cx + math.cos(ang) * (w * 0.26)
            y1 = cy + math.sin(ang) * (h * 0.26)
            x2 = cx + math.cos(ang) * (w * 0.42)
            y2 = cy + math.sin(ang) * (h * 0.42)
            draw.line([(x1, y1), (x2, y2)], fill=rgba, width=sw)
        draw.ellipse([w * 0.24, h * 0.24, w * 0.76, h * 0.76], outline=rgba, width=sw)
        draw.ellipse([w * 0.36, h * 0.36, w * 0.64, h * 0.64], fill=(0, 0, 0, 0), outline=rgba, width=max(1, sw // 2))

    elif icon_key == "sun":
        cx, cy = w * 0.5, h * 0.5
        draw.ellipse([w * 0.28, h * 0.28, w * 0.72, h * 0.72], outline=rgba, width=sw)
        for i in range(8):
            ang = i * (math.pi / 4.0)
            x1 = cx + math.cos(ang) * (w * 0.32)
            y1 = cy + math.sin(ang) * (h * 0.32)
            x2 = cx + math.cos(ang) * (w * 0.45)
            y2 = cy + math.sin(ang) * (h * 0.45)
            draw.line([(x1, y1), (x2, y2)], fill=rgba, width=sw)

    elif icon_key == "moon":
        draw.arc([w * 0.16, h * 0.16, w * 0.84, h * 0.84], start=45, end=315, fill=rgba, width=sw)
        draw.arc([w * 0.32, h * 0.12, w * 0.92, h * 0.72], start=110, end=260, fill=rgba, width=sw)

    elif icon_key == "user":
        draw.ellipse([w * 0.30, h * 0.14, w * 0.70, h * 0.52], outline=rgba, width=sw)
        draw.arc([w * 0.16, h * 0.54, w * 0.84, h * 1.10], start=180, end=360, fill=rgba, width=sw)

    elif icon_key == "lock":
        draw.rounded_rectangle([w * 0.20, h * 0.44, w * 0.80, h * 0.86], radius=w * 0.08, outline=rgba, width=sw)
        draw.arc([w * 0.30, h * 0.16, w * 0.70, h * 0.64], start=180, end=360, fill=rgba, width=sw)

    elif icon_key == "eye":
        draw.arc([w * 0.10, h * 0.22, w * 0.90, h * 0.92], start=195, end=345, fill=rgba, width=sw)
        draw.arc([w * 0.10, h * 0.08, w * 0.90, h * 0.78], start=15, end=165, fill=rgba, width=sw)
        draw.ellipse([w * 0.38, h * 0.38, w * 0.62, h * 0.62], outline=rgba, width=sw)

    elif icon_key == "eye_off":
        draw.arc([w * 0.10, h * 0.22, w * 0.90, h * 0.92], start=195, end=345, fill=rgba, width=sw)
        draw.arc([w * 0.10, h * 0.08, w * 0.90, h * 0.78], start=15, end=165, fill=rgba, width=sw)
        draw.line([p(0.18, 0.18), p(0.82, 0.82)], fill=rgba, width=sw)

    elif icon_key == "calendar":
        draw.rounded_rectangle([w * 0.14, h * 0.22, w * 0.86, h * 0.86], radius=w * 0.08, outline=rgba, width=sw)
        draw.line([p(0.14, 0.40), p(0.86, 0.40)], fill=rgba, width=sw)
        draw.line([p(0.32, 0.12), p(0.32, 0.28)], fill=rgba, width=sw)
        draw.line([p(0.68, 0.12), p(0.68, 0.28)], fill=rgba, width=sw)

    elif icon_key == "download":
        draw.line([p(0.50, 0.16), p(0.50, 0.66)], fill=rgba, width=sw)
        draw.line([p(0.30, 0.48), p(0.50, 0.68), p(0.70, 0.48)], fill=rgba, width=sw, joint="curve")
        draw.line([p(0.20, 0.84), p(0.80, 0.84)], fill=rgba, width=sw)

    elif icon_key == "upload":
        draw.line([p(0.50, 0.68), p(0.50, 0.18)], fill=rgba, width=sw)
        draw.line([p(0.30, 0.36), p(0.50, 0.16), p(0.70, 0.36)], fill=rgba, width=sw, joint="curve")
        draw.line([p(0.20, 0.84), p(0.80, 0.84)], fill=rgba, width=sw)

    elif icon_key == "trash":
        draw.line([p(0.18, 0.26), p(0.82, 0.26)], fill=rgba, width=sw)
        draw.rounded_rectangle([w * 0.26, h * 0.26, w * 0.74, h * 0.86], radius=w * 0.06, outline=rgba, width=sw)
        draw.line([p(0.38, 0.16), p(0.62, 0.16)], fill=rgba, width=sw)
        draw.line([p(0.42, 0.42), p(0.42, 0.72)], fill=rgba, width=max(1, sw - 2))
        draw.line([p(0.58, 0.42), p(0.58, 0.72)], fill=rgba, width=max(1, sw - 2))

    elif icon_key == "refresh":
        draw.arc([w * 0.16, h * 0.16, w * 0.84, h * 0.84], start=35, end=315, fill=rgba, width=sw)
        draw.line([p(0.62, 0.16), p(0.84, 0.18), p(0.80, 0.38)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "info":
        draw.ellipse([w * 0.12, h * 0.12, w * 0.88, h * 0.88], outline=rgba, width=sw)
        draw.line([p(0.50, 0.44), p(0.50, 0.72)], fill=rgba, width=sw)
        r = max(2, sw // 2 + 1)
        draw.ellipse([w * 0.50 - r, h * 0.29 - r, w * 0.50 + r, h * 0.29 + r], fill=rgba)

    elif icon_key == "warning":
        draw.polygon([p(0.50, 0.14), p(0.88, 0.84), p(0.12, 0.84)], outline=rgba, width=sw)
        draw.line([p(0.50, 0.40), p(0.50, 0.62)], fill=rgba, width=sw)
        r = max(2, sw // 2 + 1)
        draw.ellipse([w * 0.50 - r, h * 0.73 - r, w * 0.50 + r, h * 0.73 + r], fill=rgba)

    elif icon_key == "filter":
        draw.polygon([p(0.14, 0.20), p(0.86, 0.20), p(0.58, 0.54), p(0.58, 0.84), p(0.42, 0.76), p(0.42, 0.54)], outline=rgba, width=sw)

    elif icon_key == "folder":
        draw.polygon(
            [p(0.12, 0.24), p(0.40, 0.24), p(0.48, 0.34), p(0.88, 0.34), p(0.88, 0.82), p(0.12, 0.82)],
            outline=rgba,
            width=sw,
        )

    elif icon_key == "terminal":
        draw.rounded_rectangle([w * 0.12, h * 0.18, w * 0.88, h * 0.82], radius=w * 0.08, outline=rgba, width=sw)
        draw.line([p(0.26, 0.38), p(0.42, 0.50), p(0.26, 0.62)], fill=rgba, width=sw, joint="curve")
        draw.line([p(0.48, 0.62), p(0.70, 0.62)], fill=rgba, width=sw)

    elif icon_key == "sliders":
        for idx, (y_pos, knob_x) in enumerate([(0.28, 0.36), (0.50, 0.66), (0.72, 0.44)]):
            draw.line([p(0.16, y_pos), p(0.84, y_pos)], fill=rgba, width=sw)
            r = w * 0.08
            cx, cy = p(knob_x, y_pos)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba)

    elif icon_key == "chart":
        draw.line([p(0.16, 0.84), p(0.86, 0.84)], fill=rgba, width=sw)
        draw.line([p(0.26, 0.84), p(0.26, 0.52)], fill=rgba, width=int(sw * 1.4))
        draw.line([p(0.50, 0.84), p(0.50, 0.24)], fill=rgba, width=int(sw * 1.4))
        draw.line([p(0.74, 0.84), p(0.74, 0.38)], fill=rgba, width=int(sw * 1.4))

    elif icon_key == "layers":
        draw.polygon([p(0.50, 0.16), p(0.86, 0.36), p(0.50, 0.56), p(0.14, 0.36)], outline=rgba, width=sw)
        draw.line([p(0.14, 0.54), p(0.50, 0.72), p(0.86, 0.54)], fill=rgba, width=sw, joint="curve")
        draw.line([p(0.14, 0.70), p(0.50, 0.88), p(0.86, 0.70)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "zap":
        draw.polygon(
            [p(0.56, 0.12), p(0.22, 0.54), p(0.48, 0.54), p(0.42, 0.88), p(0.78, 0.46), p(0.52, 0.46)],
            outline=rgba,
            width=sw,
        )

    elif icon_key == "users":
        r1 = w * 0.14
        c1x, c1y = p(0.38, 0.32)
        draw.ellipse([c1x - r1, c1y - r1, c1x + r1, c1y + r1], outline=rgba, width=sw)
        draw.arc([w * 0.14, h * 0.52, w * 0.62, h * 0.94], start=195, end=345, fill=rgba, width=sw)
        r2 = w * 0.11
        c2x, c2y = p(0.68, 0.36)
        draw.ellipse([c2x - r2, c2y - r2, c2x + r2, c2y + r2], outline=rgba, width=sw)
        draw.arc([w * 0.50, h * 0.56, w * 0.88, h * 0.92], start=210, end=340, fill=rgba, width=sw)

    elif icon_key == "database":
        draw.ellipse([w * 0.18, h * 0.14, w * 0.82, h * 0.36], outline=rgba, width=sw)
        draw.line([p(0.18, 0.25), p(0.18, 0.75)], fill=rgba, width=sw)
        draw.line([p(0.82, 0.25), p(0.82, 0.75)], fill=rgba, width=sw)
        draw.arc([w * 0.18, h * 0.39, w * 0.82, h * 0.61], start=0, end=180, fill=rgba, width=sw)
        draw.arc([w * 0.18, h * 0.64, w * 0.82, h * 0.86], start=0, end=180, fill=rgba, width=sw)

    elif icon_key == "clock":
        draw.ellipse([w * 0.14, h * 0.14, w * 0.86, h * 0.86], outline=rgba, width=sw)
        draw.line([p(0.50, 0.28), p(0.50, 0.50), p(0.66, 0.60)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "excel_export":
        # Spreadsheet grid on lower-left with bold upward/outward export arrow emerging from top-right
        thin_sw = max(2, int(round(sw * 0.78)))
        # Grid outer frame (clipped on top-right so arrow breaks out cleanly)
        draw.line(
            [p(0.52, 0.24), p(0.14, 0.24), p(0.14, 0.88), p(0.80, 0.88), p(0.80, 0.54)],
            fill=rgba,
            width=sw,
            joint="curve",
        )
        # Spreadsheet internal grid lines (rows & columns)
        draw.line([p(0.14, 0.46), p(0.60, 0.46)], fill=rgba, width=thin_sw)
        draw.line([p(0.14, 0.67), p(0.80, 0.67)], fill=rgba, width=thin_sw)
        draw.line([p(0.37, 0.24), p(0.37, 0.88)], fill=rgba, width=thin_sw)
        draw.line([p(0.58, 0.46), p(0.58, 0.88)], fill=rgba, width=thin_sw)
        # Bold upward export arrow emerging out of the grid (center-top / top-right)
        arrow_sw = max(sw, int(round(sw * 1.15)))
        draw.line([p(0.68, 0.50), p(0.68, 0.10)], fill=rgba, width=arrow_sw)
        draw.line([p(0.50, 0.28), p(0.68, 0.10), p(0.86, 0.28)], fill=rgba, width=arrow_sw, joint="curve")

    elif icon_key == "activity":
        # Heartbeat / capacity health pulse line
        draw.line(
            [p(0.10, 0.52), p(0.30, 0.52), p(0.42, 0.18), p(0.58, 0.84), p(0.70, 0.52), p(0.90, 0.52)],
            fill=rgba,
            width=sw,
            joint="curve",
        )

    elif icon_key == "edit":
        # Pencil / edit icon
        draw.polygon(
            [p(0.66, 0.16), p(0.84, 0.34), p(0.36, 0.82), p(0.16, 0.84), p(0.18, 0.64)],
            outline=rgba,
            width=sw,
        )
        draw.line([p(0.56, 0.26), p(0.74, 0.44)], fill=rgba, width=max(1, sw - 1))

    elif icon_key == "link":
        # Chain link icon
        draw.rounded_rectangle([w * 0.12, h * 0.32, w * 0.56, h * 0.68], radius=w * 0.16, outline=rgba, width=sw)
        draw.rounded_rectangle([w * 0.44, h * 0.32, w * 0.88, h * 0.68], radius=w * 0.16, outline=rgba, width=sw)

    elif icon_key == "unlink":
        # Broken chain link icon
        draw.arc([w * 0.10, h * 0.32, w * 0.52, h * 0.68], start=90, end=270, fill=rgba, width=sw)
        draw.arc([w * 0.48, h * 0.32, w * 0.90, h * 0.68], start=270, end=90, fill=rgba, width=sw)
        draw.line([p(0.24, 0.78), p(0.76, 0.22)], fill=rgba, width=sw)

    elif icon_key == "swap":
        # Horizontal swap / toggle arrows
        draw.line([p(0.16, 0.36), p(0.82, 0.36)], fill=rgba, width=sw)
        draw.line([p(0.64, 0.20), p(0.84, 0.36), p(0.64, 0.52)], fill=rgba, width=sw, joint="curve")
        draw.line([p(0.84, 0.66), p(0.18, 0.66)], fill=rgba, width=sw)
        draw.line([p(0.36, 0.50), p(0.16, 0.66), p(0.36, 0.82)], fill=rgba, width=sw, joint="curve")

    elif icon_key == "arrow_right":
        draw.line([p(0.16, 0.50), p(0.82, 0.50)], fill=rgba, width=sw)
        draw.line([p(0.56, 0.24), p(0.84, 0.50), p(0.56, 0.76)], fill=rgba, width=sw, joint="curve")

    else:  # "sparkles" or fallback star
        cx, cy = w * 0.5, h * 0.5
        pts = [
            p(0.50, 0.12),
            p(0.60, 0.40),
            p(0.88, 0.50),
            p(0.60, 0.60),
            p(0.50, 0.88),
            p(0.40, 0.60),
            p(0.12, 0.50),
            p(0.40, 0.40),
        ]
        draw.polygon(pts, outline=rgba, width=sw)

    resample = getattr(Image, "Resampling", Image).LANCZOS
    return img.resize((max(8, size), max(8, size)), resample=resample)


def create_icon_image(
    name: str,
    size: int = 16,
    color: str = "#ffffff",
    stroke_width: float = 1.8,
    color_hex: str | None = None,
) -> ImageTk.PhotoImage:
    """Create (or fetch from cache) a supersampled anti-aliased vector icon PhotoImage."""
    if color_hex is not None:
        color = color_hex
    import tkinter as tk
    root = getattr(tk, "_default_root", None)
    root_id = id(getattr(root, "tk", root))
    key = ("icon", root_id, name.lower().strip(), int(size), color, round(stroke_width, 1))
    if key not in _ICON_PHOTO_CACHE or not _is_photo_valid(_ICON_PHOTO_CACHE[key]):
        pil_img = _render_icon_pil(name, int(size), color, round(stroke_width, 1))
        _ICON_PHOTO_CACHE[key] = ImageTk.PhotoImage(pil_img)
    return _ICON_PHOTO_CACHE[key]


# Ergonomic alias
icon = create_icon_image

"""Color manipulation and anti-aliased Pillow shape generators for ModernTkk."""

from __future__ import annotations

import tkinter as tk
from functools import lru_cache
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert a hex color string (#RRGGBB or #RGB) to an (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert an (R, G, B) tuple to a #RRGGBB string."""
    r, g, b = (max(0, min(255, int(v))) for v in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_colors(color1: str, color2: str, t: float) -> str:
    """Linearly interpolate between two hex colors (t=0.0 -> color1, t=1.0 -> color2)."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    return rgb_to_hex((
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    ))


def adjust_brightness(hex_color: str, factor: float) -> str:
    """Adjust brightness of a hex color. factor > 0 lightens, factor < 0 darkens."""
    if factor >= 0:
        return blend_colors(hex_color, "#ffffff", factor)
    return blend_colors(hex_color, "#000000", -factor)


def contrast_text_color(bg_hex: str) -> str:
    """Return #ffffff or #0f172a depending on the perceived luminance of bg_hex."""
    r, g, b = hex_to_rgb(bg_hex)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#0f172a" if luminance > 0.62 else "#ffffff"


# Global cache of PhotoImage references so Tk does not garbage-collect them
_PHOTO_CACHE: dict[tuple, ImageTk.PhotoImage] = {}


def clear_image_cache() -> None:
    """Clear the cached PhotoImage objects (e.g., when root changes)."""
    _PHOTO_CACHE.clear()


@lru_cache(maxsize=1024)
def _render_rounded_rect_pil(
    width: int,
    height: int,
    radius: int,
    fill_hex: str,
    border_hex: str | None = None,
    border_width: int = 0,
    bg_hex: str | None = None,
    bottom_border_hex: str | None = None,
    scale: int = 4,
) -> Image.Image:
    """Render a supersampled anti-aliased rounded rectangle using PIL."""
    w = max(1, width) * scale
    h = max(1, height) * scale
    r = min(radius * scale, w // 2, h // 2)
    bw = border_width * scale

    if bg_hex:
        bg_rgba = (*hex_to_rgb(bg_hex), 255)
    else:
        bg_rgba = (0, 0, 0, 0)

    img = Image.new("RGBA", (w, h), bg_rgba)
    draw = ImageDraw.Draw(img)

    fill_rgba = (*hex_to_rgb(fill_hex), 255) if fill_hex else (0, 0, 0, 0)

    if bw > 0 and border_hex:
        border_rgba = (*hex_to_rgb(border_hex), 255)
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=border_rgba)
        inner_r = max(0, r - bw)
        if w - 1 - bw > bw and h - 1 - bw > bw:
            draw.rounded_rectangle(
                [bw, bw, w - 1 - bw, h - 1 - bw],
                radius=inner_r,
                fill=fill_rgba,
            )
    else:
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill_rgba)

    resample = getattr(Image, "Resampling", Image).LANCZOS
    return img.resize((max(1, width), max(1, height)), resample=resample)


def create_rounded_rect_image(
    width: int,
    height: int,
    radius: int,
    fill_hex: str,
    border_hex: str | None = None,
    border_width: int = 0,
    bg_hex: str | None = None,
    bottom_border_hex: str | None = None,
) -> ImageTk.PhotoImage:
    """Create (or fetch from cache) a PhotoImage of an anti-aliased rounded rectangle."""
    key = (
        "rrect",
        int(width),
        int(height),
        int(radius),
        fill_hex,
        border_hex,
        int(border_width),
        bg_hex,
        bottom_border_hex,
    )
    if key not in _PHOTO_CACHE:
        pil_img = _render_rounded_rect_pil(
            int(width),
            int(height),
            int(radius),
            fill_hex,
            border_hex,
            int(border_width),
            bg_hex,
            bottom_border_hex,
        )
        _PHOTO_CACHE[key] = ImageTk.PhotoImage(pil_img)
    return _PHOTO_CACHE[key]


@lru_cache(maxsize=512)
def _render_circle_pil(
    diameter: int,
    fill_hex: str,
    border_hex: str | None = None,
    border_width: int = 0,
    bg_hex: str | None = None,
    scale: int = 4,
) -> Image.Image:
    """Render a supersampled anti-aliased circle using PIL."""
    return _render_rounded_rect_pil(
        diameter,
        diameter,
        diameter // 2,
        fill_hex,
        border_hex=border_hex,
        border_width=border_width,
        bg_hex=bg_hex,
        scale=scale,
    )


def create_circle_image(
    diameter: int,
    fill_hex: str,
    border_hex: str | None = None,
    border_width: int = 0,
    bg_hex: str | None = None,
) -> ImageTk.PhotoImage:
    """Create (or fetch from cache) a PhotoImage of an anti-aliased circle."""
    key = ("circle", int(diameter), fill_hex, border_hex, int(border_width), bg_hex)
    if key not in _PHOTO_CACHE:
        pil_img = _render_circle_pil(
            int(diameter),
            fill_hex,
            border_hex=border_hex,
            border_width=int(border_width),
            bg_hex=bg_hex,
        )
        _PHOTO_CACHE[key] = ImageTk.PhotoImage(pil_img)
    return _PHOTO_CACHE[key]


@lru_cache(maxsize=256)
def _render_checkbox_pil(
    size: int,
    radius: int,
    fill_hex: str,
    border_hex: str,
    border_width: int,
    check_hex: str | None,
    check_progress: float = 1.0,
    indeterminate: bool = False,
    bg_hex: str | None = None,
    scale: int = 4,
) -> Image.Image:
    """Render an anti-aliased rounded checkbox with optional checkmark or dash."""
    img = _render_rounded_rect_pil(
        size,
        size,
        radius,
        fill_hex,
        border_hex=border_hex,
        border_width=border_width,
        bg_hex=bg_hex,
        scale=scale,
    ).copy()

    if not check_hex or check_progress <= 0.01:
        return img

    w = size * scale
    h = size * scale
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    stroke_w = max(2, int(size * 0.12 * scale))
    c_rgba = (*hex_to_rgb(check_hex), int(255 * min(1.0, check_progress)))

    if indeterminate:
        x1 = int(w * 0.26)
        x2 = int(w * (0.26 + 0.48 * check_progress))
        y = h // 2
        draw.line([(x1, y), (x2, y)], fill=c_rgba, width=stroke_w)
    else:
        # Checkmark vertices: p1 -> p2 -> p3
        p1 = (w * 0.25, h * 0.52)
        p2 = (w * 0.43, h * 0.70)
        p3 = (w * 0.76, h * 0.31)
        if check_progress < 0.45:
            t = check_progress / 0.45
            mid = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
            draw.line([p1, mid], fill=c_rgba, width=stroke_w, joint="curve")
        else:
            t = (check_progress - 0.45) / 0.55
            end = (p2[0] + (p3[0] - p2[0]) * t, p2[1] + (p3[1] - p2[1]) * t)
            draw.line([p1, p2, end], fill=c_rgba, width=stroke_w, joint="curve")

    resample = getattr(Image, "Resampling", Image).LANCZOS
    overlay_small = overlay.resize((size, size), resample=resample)
    return Image.alpha_composite(img, overlay_small)


def create_checkbox_image(
    size: int,
    radius: int,
    fill_hex: str,
    border_hex: str,
    border_width: int = 1,
    check_hex: str | None = None,
    check_progress: float = 1.0,
    indeterminate: bool = False,
    bg_hex: str | None = None,
) -> ImageTk.PhotoImage:
    """Create a PhotoImage of a modern rounded checkbox."""
    prog_bucket = round(check_progress, 2)
    key = (
        "checkbox",
        int(size),
        int(radius),
        fill_hex,
        border_hex,
        int(border_width),
        check_hex,
        prog_bucket,
        indeterminate,
        bg_hex,
    )
    if key not in _PHOTO_CACHE:
        pil_img = _render_checkbox_pil(
            int(size),
            int(radius),
            fill_hex,
            border_hex,
            int(border_width),
            check_hex,
            prog_bucket,
            indeterminate,
            bg_hex=bg_hex,
        )
        _PHOTO_CACHE[key] = ImageTk.PhotoImage(pil_img)
    return _PHOTO_CACHE[key]

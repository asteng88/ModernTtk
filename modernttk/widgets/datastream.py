"""High-DPI Animated Data Stream Widget (Database <-> Computer) for ModernTtk.

Provides:
- `DATA_STREAM_FRAME_COUNT` (36 frames = seamless 1.2s loop at 30 FPS)
- `normalize_stream_direction` (normalizes aliases like `db_to_pc`/`download`, `pc_to_db`/`upload`, `bidirectional`/`sync`)
- `build_data_stream_frames` (2x supersampled anti-aliased frosted glassmorphic Database <-> Computer animation frames)
- `render_data_stream_overlay_badge` (Composites the 320x104 stream scene + 2x supersampled live status/elapsed/pct pill)
- `ModernDataStream` / `DataStream` (Standalone theme-reactive animated data streaming widget)
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from ..themes import ThemePalette
from ..utils import hex_to_rgb
from .base import ThemedWidgetMixin

DATA_STREAM_FRAME_COUNT: int = 36

_DATA_STREAM_FRAMES_CACHE: Dict[Tuple[Any, ...], List[Image.Image]] = {}

_DEFAULT_STATUS_BY_DIR: Dict[str, str] = {
    "db_to_pc": "Streaming from Database",
    "pc_to_db": "Streaming to Database",
    "bidirectional": "Syncing Database & Computer",
}


def normalize_stream_direction(direction: str) -> str:
    """Normalize friendly direction aliases to `'db_to_pc'`, `'pc_to_db'`, or `'bidirectional'`."""
    key = (direction or "db_to_pc").strip().lower().replace("-", "_").replace(" ", "_")
    if key in ("db_to_pc", "download", "fetch", "read", "from_db", "pull", "query", "in", "right"):
        return "db_to_pc"
    if key in ("pc_to_db", "upload", "save", "write", "to_db", "push", "commit", "out", "left"):
        return "pc_to_db"
    if key in ("bidirectional", "sync", "both", "two_way", "duplex", "db_pc"):
        return "bidirectional"
    return "db_to_pc"


def default_stream_status(direction: str) -> str:
    """Return a sensible default status label for the normalized stream direction."""
    return _DEFAULT_STATUS_BY_DIR.get(normalize_stream_direction(direction), "Streaming Data")


def _parse_rgb(hex_str: str, fallback: Tuple[int, int, int] = (76, 194, 255)) -> Tuple[int, int, int]:
    try:
        return hex_to_rgb(hex_str)
    except Exception:
        return fallback


def _mix_rgb(
    c1: Tuple[int, int, int],
    c2: Tuple[int, int, int],
    t: float,
) -> Tuple[int, int, int]:
    k = max(0.0, min(1.0, float(t)))
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * k)),
        int(round(c1[1] + (c2[1] - c1[1]) * k)),
        int(round(c1[2] + (c2[2] - c1[2]) * k)),
    )


def _load_stream_font(size_px: int, *, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")
        if bold
        else ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size_px)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_soft_glow(
    canvas: Image.Image,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    rgb: Tuple[int, int, int],
    alpha: int,
    blur_radius: float,
) -> None:
    """Composite a soft elliptical radial glow onto an RGBA Pillow image."""
    if alpha <= 0 or rx <= 1 or ry <= 1:
        return
    pad = int(math.ceil(blur_radius * 3.0)) + 4
    x0 = max(0, int(math.floor(cx - rx - pad)))
    y0 = max(0, int(math.floor(cy - ry - pad)))
    x1 = min(canvas.width, int(math.ceil(cx + rx + pad)))
    y1 = min(canvas.height, int(math.ceil(cy + ry + pad)))
    if x1 <= x0 or y1 <= y0:
        return
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(
        [cx - rx - x0, cy - ry - y0, cx + rx - x0, cy + ry - y0],
        fill=(*rgb, max(0, min(255, int(alpha)))),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(blur_radius))
    canvas.alpha_composite(layer, (x0, y0))


def _draw_database_node(
    img: Image.Image,
    *,
    cx: float,
    cy: float,
    scale: int,
    dark: bool,
    accent_rgb: Tuple[int, int, int],
    pulse: float,
    phase: float,
    label: str,
    show_label: bool,
) -> None:
    """Draw a sleek glassmorphic Database node card with 3-tier cylinder and activity LEDs."""
    s = scale
    # Subtle node container
    bx0 = cx - 34 * s
    by0 = cy - 30 * s
    bx1 = cx + 34 * s
    by1 = cy + 30 * s

    if pulse > 0.02:
        _draw_soft_glow(
            img,
            cx,
            cy - 2 * s,
            26 * s,
            22 * s,
            accent_rgb,
            alpha=int((85 if dark else 55) * pulse),
            blur_radius=7 * s,
        )

    d = ImageDraw.Draw(img)
    box_fill = (24, 34, 54, 215) if dark else (238, 244, 252, 235)
    rim_idle = (62, 78, 108, 170) if dark else (184, 198, 220, 200)
    rim_rgb = _mix_rgb(rim_idle[:3], accent_rgb, 0.25 + 0.55 * pulse)
    d.rounded_rectangle(
        [bx0, by0, bx1, by1],
        radius=13 * s,
        fill=box_fill,
        outline=(*rim_rgb, 215),
        width=max(1, int(1.5 * s)),
    )

    # 3-tier Database Cylinder geometry
    cyl_w = 34 * s
    cyl_x0 = cx - cyl_w / 2.0
    cyl_x1 = cx + cyl_w / 2.0
    top_y = cy - 19 * s
    bot_y = cy + 13 * s
    ell_h = 9 * s

    body_fill = (38, 52, 78, 245) if dark else (222, 232, 246, 250)
    top_fill = _mix_rgb(body_fill[:3], accent_rgb, 0.24 if dark else 0.18)
    stroke_col = (196, 218, 245, 235) if dark else (48, 68, 102, 235)
    sw = max(2, int(1.8 * s))

    # Cylinder vertical fill + bottom cap
    d.rectangle([cyl_x0, top_y + ell_h / 2.0, cyl_x1, bot_y], fill=body_fill)
    d.ellipse([cyl_x0, bot_y - ell_h / 2.0, cyl_x1, bot_y + ell_h / 2.0], fill=body_fill, outline=stroke_col, width=sw)

    # Side walls
    d.line([(cyl_x0, top_y + ell_h / 2.0), (cyl_x0, bot_y)], fill=stroke_col, width=sw)
    d.line([(cyl_x1, top_y + ell_h / 2.0), (cyl_x1, bot_y)], fill=stroke_col, width=sw)

    # Mid-tier curved dividers
    mid1_y = top_y + 15.5 * s
    mid2_y = top_y + 24.5 * s
    for my in (mid1_y, mid2_y):
        d.arc(
            [cyl_x0, my - ell_h / 2.0, cyl_x1, my + ell_h / 2.0],
            start=0,
            end=180,
            fill=stroke_col,
            width=sw,
        )

    # Top platter ellipse
    d.ellipse(
        [cyl_x0, top_y, cyl_x1, top_y + ell_h],
        fill=(*top_fill, 250),
        outline=stroke_col,
        width=sw,
    )

    # Three tiny glowing tier LEDs that cascade softly with phase
    led_x = cyl_x1 - 5.5 * s
    for idx, ly in enumerate((top_y + 12.2 * s, top_y + 21.2 * s, top_y + 29.5 * s)):
        wave = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase - idx * 0.22))
        led_rgb = _mix_rgb((95, 115, 145) if dark else (140, 158, 185), accent_rgb, 0.35 + 0.65 * wave)
        r_led = 2.0 * s
        d.ellipse(
            [led_x - r_led, ly - r_led, led_x + r_led, ly + r_led],
            fill=(*led_rgb, 255),
        )

    if show_label and label:
        font = _load_stream_font(10 * s, bold=True)
        lbl_col = (196, 210, 232, 230) if dark else (58, 74, 98, 235)
        bbox = d.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        d.text((cx - tw / 2.0 - bbox[0], by1 + 4 * s - bbox[1]), label, font=font, fill=lbl_col)


def _draw_computer_node(
    img: Image.Image,
    *,
    cx: float,
    cy: float,
    scale: int,
    dark: bool,
    accent_rgb: Tuple[int, int, int],
    pulse: float,
    phase: float,
    label: str,
    show_label: bool,
) -> None:
    """Draw a sleek glassmorphic Computer/Workstation node with animated screen activity bars."""
    s = scale
    bx0 = cx - 34 * s
    by0 = cy - 30 * s
    bx1 = cx + 34 * s
    by1 = cy + 30 * s

    if pulse > 0.02:
        _draw_soft_glow(
            img,
            cx,
            cy - 2 * s,
            26 * s,
            22 * s,
            accent_rgb,
            alpha=int((85 if dark else 55) * pulse),
            blur_radius=7 * s,
        )

    d = ImageDraw.Draw(img)
    box_fill = (24, 34, 54, 215) if dark else (238, 244, 252, 235)
    rim_idle = (62, 78, 108, 170) if dark else (184, 198, 220, 200)
    rim_rgb = _mix_rgb(rim_idle[:3], accent_rgb, 0.25 + 0.55 * pulse)
    d.rounded_rectangle(
        [bx0, by0, bx1, by1],
        radius=13 * s,
        fill=box_fill,
        outline=(*rim_rgb, 215),
        width=max(1, int(1.5 * s)),
    )

    # Monitor bezel
    mon_x0 = cx - 21 * s
    mon_y0 = cy - 19 * s
    mon_x1 = cx + 21 * s
    mon_y1 = cy + 9 * s
    bezel_fill = (32, 44, 68, 248) if dark else (222, 232, 246, 250)
    screen_fill = (14, 21, 35, 255) if dark else (245, 249, 255, 255)
    stroke_col = (196, 218, 245, 235) if dark else (48, 68, 102, 235)
    sw = max(2, int(1.8 * s))

    d.rounded_rectangle(
        [mon_x0, mon_y0, mon_x1, mon_y1],
        radius=4 * s,
        fill=bezel_fill,
        outline=stroke_col,
        width=sw,
    )
    # Inner display area
    sc_x0 = mon_x0 + 3.5 * s
    sc_y0 = mon_y0 + 3.5 * s
    sc_x1 = mon_x1 - 3.5 * s
    sc_y1 = mon_y1 - 4.5 * s
    d.rounded_rectangle(
        [sc_x0, sc_y0, sc_x1, sc_y1],
        radius=2 * s,
        fill=screen_fill,
    )

    # Animated data-processing bars inside the monitor screen
    inner_w = sc_x1 - sc_x0 - 6 * s
    bar_x0 = sc_x0 + 3 * s
    for idx in range(3):
        by = sc_y0 + (4.0 + idx * 5.2) * s
        wave = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase + idx * 0.28))
        bar_len = max(4 * s, inner_w * (0.35 + 0.60 * wave))
        bar_col = _mix_rgb(
            (72, 96, 132) if dark else (155, 178, 210),
            accent_rgb,
            0.40 + 0.60 * wave,
        )
        d.rounded_rectangle(
            [bar_x0, by, bar_x0 + bar_len, by + 2.6 * s],
            radius=max(1, int(1.3 * s)),
            fill=(*bar_col, 240),
        )

    # Monitor neck and base stand
    neck_x0 = cx - 4 * s
    neck_x1 = cx + 4 * s
    d.rectangle([neck_x0, mon_y1, neck_x1, mon_y1 + 5.5 * s], fill=stroke_col)
    d.rounded_rectangle(
        [cx - 12 * s, mon_y1 + 4.5 * s, cx + 12 * s, mon_y1 + 7.5 * s],
        radius=max(1, int(1.5 * s)),
        fill=stroke_col,
    )

    # Tiny activity LED on monitor chin
    led_r = 1.4 * s
    led_y = mon_y1 - 2.2 * s
    led_col = _mix_rgb((110, 130, 160), accent_rgb, 0.5 + 0.5 * pulse)
    d.ellipse([cx - led_r, led_y - led_r, cx + led_r, led_y + led_r], fill=(*led_col, 255))

    if show_label and label:
        font = _load_stream_font(10 * s, bold=True)
        lbl_col = (196, 210, 232, 230) if dark else (58, 74, 98, 235)
        bbox = d.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        d.text((cx - tw / 2.0 - bbox[0], by1 + 4 * s - bbox[1]), label, font=font, fill=lbl_col)


def _draw_stream_lane(
    img: Image.Image,
    *,
    x_left: float,
    x_right: float,
    y_mid: float,
    scale: int,
    dark: bool,
    rgb: Tuple[int, int, int],
    go_right: bool,
    phase: float,
    num_packets: int,
) -> None:
    """Draw a recessed stream rail, animated chevrons, and glowing comet data packets."""
    s = scale
    d = ImageDraw.Draw(img)

    # Recessed conduit rail
    rail_h = 4.0 * s
    rail_fill = (28, 40, 62, 185) if dark else (206, 218, 235, 210)
    rail_edge = (54, 72, 102, 140) if dark else (178, 194, 216, 175)
    d.rounded_rectangle(
        [x_left, y_mid - rail_h / 2.0, x_right, y_mid + rail_h / 2.0],
        radius=rail_h / 2.0,
        fill=rail_fill,
        outline=rail_edge,
        width=max(1, s // 2),
    )

    # Connector ports at both ends of the rail
    port_r = 3.2 * s
    port_col = _mix_rgb(rail_edge[:3], rgb, 0.55)
    for px in (x_left, x_right):
        d.ellipse([px - port_r, y_mid - port_r, px + port_r, y_mid + port_r], fill=(*port_col, 230))

    # Subtle directional chevron wave along the conduit
    span = x_right - x_left
    n_chev = 5
    chev_size = 3.4 * s
    for c_idx in range(n_chev):
        u = (c_idx + 0.5) / n_chev
        cx = x_left + u * span
        # Traveling brightness wave in direction of flow
        dist = (u - phase) % 1.0 if go_right else (phase - u) % 1.0
        wave = math.exp(-((min(dist, 1.0 - dist) * 4.5) ** 2))
        c_alpha = int((42 if dark else 50) + (115 if dark else 110) * wave)
        c_col = (*_mix_rgb((120, 140, 170) if dark else (130, 150, 178), rgb, 0.45 + 0.55 * wave), c_alpha)
        dir_sign = 1.0 if go_right else -1.0
        pts = [
            (cx - dir_sign * chev_size * 0.6, y_mid - chev_size),
            (cx + dir_sign * chev_size * 0.6, y_mid),
            (cx - dir_sign * chev_size * 0.6, y_mid + chev_size),
        ]
        d.line(pts, fill=c_col, width=max(1, int(1.3 * s)), joint="curve")

    # Animated glowing data packets with comet tails
    dir_sign = 1.0 if go_right else -1.0
    for k in range(num_packets):
        t = (phase + k / float(num_packets)) % 1.0
        # Smooth fade-in at source, fade-out at destination
        edge_fade = min(1.0, t / 0.13) * min(1.0, (1.0 - t) / 0.13)
        if edge_fade <= 0.02:
            continue

        px = (x_left + t * span) if go_right else (x_right - t * span)

        # Soft ambient glow around packet head
        _draw_soft_glow(
            img,
            px,
            y_mid,
            8.5 * s,
            5.0 * s,
            rgb,
            alpha=int((115 if dark else 75) * edge_fade),
            blur_radius=4.5 * s,
        )

        d = ImageDraw.Draw(img)
        # Tapered comet tail segments behind the packet
        tail_steps = 5
        for st in range(tail_steps, 0, -1):
            frac = st / float(tail_steps + 1)
            tx = px - dir_sign * (st * 4.2 * s)
            if tx < x_left + 1 * s or tx > x_right - 1 * s:
                continue
            th = (2.6 - 1.5 * frac) * s
            tw = (4.8 - 1.8 * frac) * s
            ta = int((145 * (1.0 - frac) ** 1.6) * edge_fade)
            if ta > 4:
                d.rounded_rectangle(
                    [tx - tw, y_mid - th, tx + tw, y_mid + th],
                    radius=max(1, int(th)),
                    fill=(*rgb, ta),
                )

        # Crisp glowing packet capsule + specular core
        pw = 5.6 * s
        ph = 2.8 * s
        d.rounded_rectangle(
            [px - pw, y_mid - ph, px + pw, y_mid + ph],
            radius=ph,
            fill=(*rgb, int(245 * edge_fade)),
        )
        hi_rgb = _mix_rgb(rgb, (255, 255, 255), 0.65 if dark else 0.45)
        d.rounded_rectangle(
            [px - pw * 0.55, y_mid - ph * 0.48, px + pw * 0.55, y_mid + ph * 0.48],
            radius=max(1, int(ph * 0.48)),
            fill=(*hi_rgb, int(255 * edge_fade)),
        )


def build_data_stream_frames(
    *,
    dark: bool = True,
    primary_rgb: Tuple[int, int, int] = (76, 194, 255),
    info_rgb: Tuple[int, int, int] = (56, 189, 248),
    direction: str = "db_to_pc",
    source_label: str = "Database",
    target_label: str = "Computer",
    show_labels: bool = True,
    num_frames: int = DATA_STREAM_FRAME_COUNT,
) -> List[Image.Image]:
    """Render 2x supersampled anti-aliased Database <-> Computer data stream frames (320x104 RGBA)."""
    norm_dir = normalize_stream_direction(direction)
    n_safe = max(1, int(num_frames))
    cache_key = (
        bool(dark),
        tuple(primary_rgb),
        tuple(info_rgb),
        norm_dir,
        str(source_label),
        str(target_label),
        bool(show_labels),
        n_safe,
    )
    cached = _DATA_STREAM_FRAMES_CACHE.get(cache_key)
    if cached is not None:
        return list(cached)

    # Ensure distinct secondary lane color in bidirectional mode if primary and info are nearly identical
    secondary_rgb = info_rgb
    color_dist = sum(abs(a - b) for a, b in zip(primary_rgb, info_rgb))
    if color_dist < 55:
        secondary_rgb = (52, 211, 153) if dark else (16, 163, 127)

    W, H = 320, 104
    scale = 2
    W2, H2 = W * scale, H * scale

    # 1. Pre-render static frosted glassmorphic capsule card
    sh = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d_sh = ImageDraw.Draw(sh)
    d_sh.rounded_rectangle(
        [10 * scale, 10 * scale, (W - 10) * scale, (H - 6) * scale],
        radius=18 * scale,
        fill=(2, 6, 14, 105 if dark else 52),
    )
    base = sh.filter(ImageFilter.GaussianBlur(4.5 * scale))

    d_base = ImageDraw.Draw(base)
    card_fill = (16, 23, 38, 228) if dark else (247, 250, 255, 238)
    card_edge = (*_mix_rgb((70, 88, 120), primary_rgb, 0.42), 165) if dark else (175, 192, 216, 200)
    d_base.rounded_rectangle(
        [10 * scale, 6 * scale, (W - 10) * scale, (H - 10) * scale],
        radius=18 * scale,
        fill=card_fill,
        outline=card_edge,
        width=max(2, int(1.3 * scale)),
    )

    # Subtle top glass reflection hairline
    sheen_col = (255, 255, 255, 24 if dark else 95)
    d_base.line(
        [(28 * scale, 8 * scale), ((W - 28) * scale, 8 * scale)],
        fill=sheen_col,
        width=max(1, scale),
    )

    # 2. Render each animation frame
    frames: List[Image.Image] = []
    resample = getattr(Image, "Resampling", Image).LANCZOS
    node_cy = (46 if show_labels else 50) * scale
    db_cx = 56 * scale
    pc_cx = (W - 56) * scale
    lane_x0 = 96 * scale
    lane_x1 = (W - 96) * scale

    for i in range(n_safe):
        phase = i / float(n_safe)
        fr = base.copy()

        # Subtle node arrival/departure pulse synchronized with packet cadence
        if norm_dir == "db_to_pc":
            db_pulse = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 4.0)))
            pc_pulse = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 4.0 - 0.35)))
            _draw_stream_lane(
                fr,
                x_left=lane_x0,
                x_right=lane_x1,
                y_mid=node_cy,
                scale=scale,
                dark=dark,
                rgb=primary_rgb,
                go_right=True,
                phase=phase,
                num_packets=4,
            )
            pc_accent = primary_rgb
            db_accent = primary_rgb
        elif norm_dir == "pc_to_db":
            pc_pulse = 0.25 + 0.35 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 4.0)))
            db_pulse = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 4.0 - 0.35)))
            _draw_stream_lane(
                fr,
                x_left=lane_x0,
                x_right=lane_x1,
                y_mid=node_cy,
                scale=scale,
                dark=dark,
                rgb=primary_rgb,
                go_right=False,
                phase=phase,
                num_packets=4,
            )
            pc_accent = primary_rgb
            db_accent = primary_rgb
        else:
            db_pulse = 0.35 + 0.55 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 3.0)))
            pc_pulse = 0.35 + 0.55 * (0.5 + 0.5 * math.sin(2.0 * math.pi * (phase * 3.0 + 0.5)))
            _draw_stream_lane(
                fr,
                x_left=lane_x0,
                x_right=lane_x1,
                y_mid=node_cy - 10 * scale,
                scale=scale,
                dark=dark,
                rgb=primary_rgb,
                go_right=True,
                phase=phase,
                num_packets=3,
            )
            _draw_stream_lane(
                fr,
                x_left=lane_x0,
                x_right=lane_x1,
                y_mid=node_cy + 10 * scale,
                scale=scale,
                dark=dark,
                rgb=secondary_rgb,
                go_right=False,
                phase=(phase + 0.16) % 1.0,
                num_packets=3,
            )
            db_accent = secondary_rgb
            pc_accent = primary_rgb

        _draw_database_node(
            fr,
            cx=db_cx,
            cy=node_cy,
            scale=scale,
            dark=dark,
            accent_rgb=db_accent,
            pulse=db_pulse,
            phase=phase,
            label=source_label,
            show_label=show_labels,
        )
        _draw_computer_node(
            fr,
            cx=pc_cx,
            cy=node_cy,
            scale=scale,
            dark=dark,
            accent_rgb=pc_accent,
            pulse=pc_pulse,
            phase=phase,
            label=target_label,
            show_label=show_labels,
        )

        frames.append(fr.resize((W, H), resample=resample))

    if len(_DATA_STREAM_FRAMES_CACHE) >= 16:
        _DATA_STREAM_FRAMES_CACHE.clear()
    _DATA_STREAM_FRAMES_CACHE[cache_key] = frames
    return list(frames)


def render_data_stream_overlay_badge(
    stream_frame: Image.Image,
    *,
    elapsed_sec: float = 0.0,
    pct: Optional[float] = None,
    status_text: str = "",
    dark: bool = True,
    primary_rgb: Tuple[int, int, int] = (76, 194, 255),
    show_pill: bool = True,
    pill_cache: Optional[Dict[Tuple[Any, ...], Image.Image]] = None,
) -> Image.Image:
    """Compose a 320x148 high-DPI Database <-> Computer stream scene + live status pill."""
    if not show_pill:
        return stream_frame.copy()

    tenths = int(min(9999, round(max(0.0, float(elapsed_sec)) * 10.0)))
    pct_i = None if pct is None else int(max(0, min(99, round(float(pct)))))
    clean_status = (status_text or "").strip()
    cache_key = (bool(dark), tuple(primary_rgb), tenths, pct_i, clean_status)

    pill_1x: Optional[Image.Image] = None
    if pill_cache is not None:
        pill_1x = pill_cache.get(cache_key)

    if pill_1x is None:
        pw, ph = 320, 44
        pw2, ph2 = pw * 2, ph * 2
        sh = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh)
        d_sh.rounded_rectangle(
            [40, 12, pw2 - 40, ph2 - 12],
            radius=28,
            fill=(2, 6, 14, 110 if dark else 60),
        )
        pill_2x = sh.filter(ImageFilter.GaussianBlur(5))
        d2 = ImageDraw.Draw(pill_2x)

        parts: List[str] = []
        if clean_status:
            parts.append(clean_status)
        parts.append(f"{tenths / 10.0:.1f}s")
        if pct_i is not None:
            parts.append(f"{pct_i}%")
        text_str = "  •  ".join(parts)

        font = _load_stream_font(21, bold=True)
        bbox = d2.textbbox((0, 0), text_str, font=font)
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])

        dot_d = 12
        gap = 12
        content_w = dot_d + gap + tw
        box_w = min(pw2 - 24, max(280, content_w + 56))
        box_x0 = (pw2 - box_w) // 2
        box_x1 = box_x0 + box_w

        pill_fill = (15, 22, 36, 226) if dark else (246, 249, 254, 238)
        pill_edge = (*primary_rgb, 115) if dark else (150, 170, 198, 160)
        d2.rounded_rectangle(
            [box_x0, 8, box_x1, ph2 - 14],
            radius=30,
            fill=pill_fill,
            outline=pill_edge,
            width=2,
        )

        start_x = (pw2 - content_w) // 2
        pill_cy = (8 + (ph2 - 14)) // 2

        d2.ellipse(
            [start_x - 3, pill_cy - dot_d // 2 - 3, start_x + dot_d + 3, pill_cy + dot_d // 2 + 3],
            fill=(*primary_rgb, 65),
        )
        d2.ellipse(
            [start_x, pill_cy - dot_d // 2, start_x + dot_d, pill_cy + dot_d // 2],
            fill=(*primary_rgb, 255),
        )

        text_col = (236, 243, 252, 255) if dark else (22, 32, 48, 255)
        tx = start_x + dot_d + gap - bbox[0]
        ty = pill_cy - th // 2 - bbox[1] - 1
        d2.text((tx, ty), text_str, font=font, fill=text_col)

        resample = getattr(Image, "Resampling", Image).LANCZOS
        pill_1x = pill_2x.resize((pw, ph), resample=resample)
        if pill_cache is not None:
            if len(pill_cache) >= 64:
                pill_cache.clear()
            pill_cache[cache_key] = pill_1x

    badge = Image.new("RGBA", (320, 148), (0, 0, 0, 0))
    badge.alpha_composite(stream_frame, (0, 0))
    badge.alpha_composite(pill_1x, (0, 102))
    return badge


class ModernDataStream(tk.Canvas, ThemedWidgetMixin):
    """Standalone theme-reactive animated data streaming widget (Database <-> Computer).

    Displays glowing data packets streaming along a frosted glassmorphic pipeline between
    a Database node and a Computer/Workstation node at 30 FPS (`interval_ms=33`).

    Supports three directions:
    - `"db_to_pc"` (default, aliases: `"download"`, `"fetch"`, `"read"`, `"pull"`, `"query"`)
    - `"pc_to_db"` (aliases: `"upload"`, `"save"`, `"write"`, `"push"`, `"commit"`)
    - `"bidirectional"` (aliases: `"sync"`, `"both"`, `"two_way"`)
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        direction: str = "db_to_pc",
        bootstyle: str = "primary",
        status_text: Optional[str] = None,
        source_label: str = "Database",
        target_label: str = "Computer",
        show_labels: bool = True,
        show_pill: bool = True,
        pct: Optional[float] = None,
        autostart: bool = False,
        interval_ms: int = 33,
        width: int = 320,
        height: Optional[int] = None,
        **kwargs,
    ) -> None:
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._direction = normalize_stream_direction(direction)
        self._custom_status = status_text
        self._source_label = source_label
        self._target_label = target_label
        self._show_labels = bool(show_labels)
        self._show_pill = bool(show_pill)
        self._pct: Optional[float] = None if pct is None else max(0.0, min(100.0, float(pct)))
        self._pct_ceil: Optional[float] = None
        self._interval_ms = max(16, int(interval_ms))

        self._running = False
        self._start_t = time.perf_counter()
        self._elapsed_override: Optional[float] = None
        self._frame_idx = 0
        self._anim_job: Optional[str] = None
        self._frames_cache_key: Optional[Tuple[Any, ...]] = None
        self._frames: List[Image.Image] = []
        self._pill_cache: Dict[Tuple[Any, ...], Image.Image] = {}
        self._photo: Optional[ImageTk.PhotoImage] = None

        resolved_h = int(height) if height is not None else (148 if self._show_pill else 104)
        super().__init__(
            master,
            width=int(width),
            height=resolved_h,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Destroy>", self._on_destroy_cleanup, add="+")

        if autostart:
            self.start()
        else:
            self._redraw()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def pct(self) -> Optional[float]:
        return self._pct

    @property
    def frame_index(self) -> int:
        return self._frame_idx

    @property
    def elapsed_sec(self) -> float:
        if self._elapsed_override is not None:
            return self._elapsed_override
        if self._running:
            return max(0.0, time.perf_counter() - self._start_t)
        return 0.0

    @property
    def status_text(self) -> str:
        if self._custom_status is not None:
            return self._custom_status
        return default_stream_status(self._direction)

    def _on_destroy_cleanup(self, e: tk.Event) -> None:
        if e.widget is self:
            self.stop()

    def _ensure_frames(self) -> Tuple[List[Image.Image], bool, Tuple[int, int, int]]:
        p = self.palette
        dark = p.mode == "dark"
        prim = _parse_rgb(p.role_color(self._role), (76, 194, 255))
        info = _parse_rgb(p.info, (56, 189, 248))
        key = (
            dark,
            prim,
            info,
            self._direction,
            self._source_label,
            self._target_label,
            self._show_labels,
            DATA_STREAM_FRAME_COUNT,
        )
        if self._frames_cache_key != key or not self._frames:
            self._frames = build_data_stream_frames(
                dark=dark,
                primary_rgb=prim,
                info_rgb=info,
                direction=self._direction,
                source_label=self._source_label,
                target_label=self._target_label,
                show_labels=self._show_labels,
                num_frames=DATA_STREAM_FRAME_COUNT,
            )
            self._frames_cache_key = key
        return self._frames, dark, prim

    def set_direction(self, direction: str, status_text: Optional[str] = None) -> None:
        """Change the streaming direction (`'db_to_pc'`, `'pc_to_db'`, or `'bidirectional'`)."""
        self._direction = normalize_stream_direction(direction)
        if status_text is not None:
            self._custom_status = status_text
        self._frames_cache_key = None
        self._redraw()

    def set_status(self, text: Optional[str]) -> None:
        """Set a custom status label (or `None` to revert to the direction's default label)."""
        self._custom_status = text
        self._redraw()

    def set_progress(
        self,
        pct: float,
        *,
        ceiling: Optional[float] = None,
        elapsed_sec: Optional[float] = None,
    ) -> None:
        """Update optional progress percentage (with smooth ceiling gliding when running)."""
        new_pct = max(0.0, min(100.0, float(pct)))
        if self._running and self._pct is not None:
            self._pct = max(self._pct, new_pct)
        else:
            self._pct = new_pct
        if ceiling is not None:
            self._pct_ceil = max(self._pct, min(99.0, float(ceiling)))
        elif self._pct_ceil is not None:
            self._pct_ceil = max(self._pct, self._pct_ceil)
        if elapsed_sec is not None:
            self._elapsed_override = max(0.0, float(elapsed_sec))
        self._redraw()

    def start(
        self,
        *,
        direction: Optional[str] = None,
        status_text: Optional[str] = None,
        initial_pct: Optional[float] = None,
        initial_ceiling: Optional[float] = None,
        interval_ms: Optional[int] = None,
    ) -> None:
        """Start the 30 FPS data streaming animation."""
        if direction is not None:
            self._direction = normalize_stream_direction(direction)
            self._frames_cache_key = None
        if status_text is not None:
            self._custom_status = status_text
        if interval_ms is not None:
            self._interval_ms = max(16, int(interval_ms))
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        self._running = True
        self._elapsed_override = None
        self._start_t = time.perf_counter()
        if initial_pct is not None:
            self._pct = max(0.0, min(99.0, float(initial_pct)))
        if initial_ceiling is not None:
            self._pct_ceil = max(self._pct or 0.0, min(99.0, float(initial_ceiling)))
        self._frame_idx = 0
        self._redraw()
        self._anim_job = self.after(self._interval_ms, self._tick)

    def stop(self) -> None:
        """Stop the data streaming animation loop."""
        self._running = False
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

    def reset(self) -> None:
        """Stop and reset frame index, elapsed timer, and optional percentage."""
        self.stop()
        self._frame_idx = 0
        if self._pct is not None:
            self._pct = 0.0
        self._pct_ceil = None
        self._elapsed_override = 0.0
        self._redraw()

    def step_frame(self) -> None:
        """Advance one animation frame and glide percentage toward the ceiling if enabled."""
        self._frame_idx = (self._frame_idx + 1) % DATA_STREAM_FRAME_COUNT
        if self._pct is not None and self._pct_ceil is not None and self._pct < self._pct_ceil:
            step = max(0.22, (self._pct_ceil - self._pct) * 0.055)
            self._pct = min(self._pct_ceil, self._pct + step)
        self._redraw()

    def _tick(self) -> None:
        self._anim_job = None
        if not self._running or not self.winfo_exists():
            return
        self.step_frame()
        try:
            self._anim_job = self.after(self._interval_ms, self._tick)
        except tk.TclError:
            self._anim_job = None

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._frames_cache_key = None
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        frames, dark, prim = self._ensure_frames()
        frame = frames[self._frame_idx % len(frames)]
        badge_im = render_data_stream_overlay_badge(
            frame,
            elapsed_sec=self.elapsed_sec,
            pct=self._pct,
            status_text=self.status_text,
            dark=dark,
            primary_rgb=prim,
            show_pill=self._show_pill,
            pill_cache=self._pill_cache,
        )
        self._photo = ImageTk.PhotoImage(badge_im, master=self.winfo_toplevel())
        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        cx, cy = w // 2, h // 2
        existing = self.find_withtag("data_stream_badge")
        if existing:
            self.coords(existing[0], cx, cy)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(cx, cy, image=self._photo, anchor="center", tags=("data_stream_badge",))

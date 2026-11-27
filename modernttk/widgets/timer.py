"""High-DPI Animated Chronograph Timer & Uninterrupted Execution Engine for ModernTtk.

Provides:
- `SPINNER_FRAME_COUNT` (36 frames = 10° per step at 30 FPS)
- `build_timer_dial_frames` (Subpixel anti-aliased frosted glassmorphic chronograph dial frames)
- `render_timer_overlay_badge` (Composites the 168x188 rotating dial + 2x supersampled elapsed/pct pill)
- `ModernActivityTimer` / `ActivityTimer` (Standalone theme-reactive animated chronograph timer widget)
- `ModernBusyOverlay` / `BusyOverlay` (Non-blocking canvas overlay controller with stage-ceiling progress gliding)
- `ModernSubprocessWorker` / `SubprocessWorker` & `run_subprocess_worker_loop` (Persistent GIL-free IPC worker)
- `ModernTaskRunner` / `TaskRunner` (Uninterrupted background task coordinator with 25ms queue polling + 30 FPS timer)
"""

from __future__ import annotations

import atexit
import math
from pathlib import Path
import pickle
import queue
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from ..style import ThemeManager
from ..themes import ThemePalette
from ..utils import hex_to_rgb
from .base import ThemedWidgetMixin
from .datastream import (
    DATA_STREAM_FRAME_COUNT,
    build_data_stream_frames,
    default_stream_status,
    normalize_stream_direction,
    render_data_stream_overlay_badge,
)

try:
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    np = None  # type: ignore


SPINNER_FRAME_COUNT: int = 36

DEFAULT_STAGE_CEILINGS: Tuple[Tuple[float, float], ...] = (
    (18.0, 17.0),
    (30.0, 29.0),
    (38.0, 37.0),
    (66.0, 64.0),
    (80.0, 78.0),
    (97.0, 96.0),
    (100.0, 99.0),
)


def default_stage_pct_ceiling(
    pct: float,
    milestones: Sequence[Tuple[float, float]] = DEFAULT_STAGE_CEILINGS,
) -> float:
    """Return the smooth stage ceiling target for a reported worker milestone percentage."""
    val = float(pct)
    for threshold, ceiling in milestones:
        if val < threshold:
            return float(ceiling)
    return 100.0


def _parse_rgb_hex(hex_str: str, fallback: Tuple[int, int, int] = (76, 194, 255)) -> Tuple[int, int, int]:
    try:
        return hex_to_rgb(hex_str)
    except Exception:
        return fallback


def _blend_premul(
    acc: Any,
    rgb: Any,
    alpha: Any,
) -> None:
    """In-place Porter-Duff `over` compositing in premultiplied float32 space."""
    a = np.clip(alpha, 0.0, 1.0)[..., None]
    rgb_arr = np.asarray(rgb, dtype=np.float32)
    inv = 1.0 - a
    acc[..., :3] = acc[..., :3] * inv + rgb_arr * a
    acc[..., 3:4] = acc[..., 3:4] * inv + a


def _load_ui_font(size_px: int, *, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a clean TrueType sans-serif UI font with tabular-digit friendly metrics."""
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


_DIAL_FRAMES_CACHE: Dict[
    Tuple[bool, Tuple[int, int, int], Tuple[int, int, int], int],
    List[Image.Image],
] = {}


def _build_timer_dial_frames_pil(
    *,
    dark: bool,
    primary_rgb: Tuple[int, int, int],
    info_rgb: Tuple[int, int, int],
    num_frames: int,
) -> List[Image.Image]:
    """2x supersampled pure-Pillow fallback when NumPy is unavailable."""
    W, H = 168, 146
    scale = 2
    W2, H2 = W * scale, H * scale
    cx, cy = 84 * scale, 72 * scale
    r_med = 56 * scale
    r_track = 44 * scale

    base = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    db = ImageDraw.Draw(base)
    fill_col = (18, 26, 42, 228) if dark else (246, 249, 254, 236)
    rim_col = (*primary_rgb, 180) if dark else (175, 190, 214, 215)
    db.ellipse([cx - r_med, cy - r_med, cx + r_med, cy + r_med], fill=fill_col, outline=rim_col, width=3)
    track_col = (41, 56, 86, 175) if dark else (202, 214, 232, 200)
    db.ellipse(
        [cx - r_track, cy - r_track, cx + r_track, cy + r_track],
        outline=track_col,
        width=6 * scale,
    )
    for k in range(12):
        ang = k * (math.pi / 6.0)
        tx, ty = math.sin(ang), -math.cos(ang)
        r_in = (28.5 if k % 3 == 0 else 31.0) * scale
        r_out = 35.0 * scale
        db.line(
            [cx + tx * r_in, cy + ty * r_in, cx + tx * r_out, cy + ty * r_out],
            fill=(132, 153, 188, 160),
            width=2 * scale if k % 3 == 0 else scale,
        )

    frames: List[Image.Image] = []
    resample = getattr(Image, "Resampling", Image).LANCZOS
    for i in range(num_frames):
        fr = base.copy()
        d = ImageDraw.Draw(fr)
        deg = i * (360.0 / num_frames)
        ang = math.radians(deg)
        ux, uy = math.sin(ang), -math.cos(ang)
        start_deg = deg - 270.0 - 140.0
        end_deg = deg - 90.0
        d.arc(
            [cx - r_track, cy - r_track, cx + r_track, cy + r_track],
            start=start_deg,
            end=end_deg,
            fill=(*primary_rgb, 240),
            width=6 * scale,
        )
        d.line(
            [cx - ux * 7 * scale, cy - uy * 7 * scale, cx + ux * 26 * scale, cy + uy * 26 * scale],
            fill=(242, 248, 255, 255) if dark else (28, 42, 68, 255),
            width=3 * scale,
        )
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(*primary_rgb, 255))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(15, 23, 40, 255) if dark else (245, 250, 255, 255))
        frames.append(fr.resize((W, H), resample=resample))
    return frames


def build_timer_dial_frames(
    *,
    dark: bool = True,
    primary_rgb: Tuple[int, int, int] = (76, 194, 255),
    info_rgb: Tuple[int, int, int] = (56, 189, 248),
    num_frames: int = SPINNER_FRAME_COUNT,
) -> List[Image.Image]:
    """Render subpixel-anti-aliased rotating chronograph timer dial frames (168x146 RGBA)."""
    n_safe = max(1, int(num_frames))
    cache_key = (bool(dark), tuple(primary_rgb), tuple(info_rgb), n_safe)
    cached = _DIAL_FRAMES_CACHE.get(cache_key)
    if cached is not None:
        return list(cached)

    if np is None:  # pragma: no cover
        frames_fallback = _build_timer_dial_frames_pil(
            dark=dark,
            primary_rgb=primary_rgb,
            info_rgb=info_rgb,
            num_frames=n_safe,
        )
        _DIAL_FRAMES_CACHE[cache_key] = frames_fallback
        return list(frames_fallback)

    W, H = 168, 146
    cx, cy = 84.0, 72.0
    r_med = 56.0
    r_track = np.float32(44.0)
    hw_track = np.float32(3.25)
    two_pi = np.float32(2.0 * np.pi)
    sweep_span = np.float32(1.55 * np.pi)

    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    dx = xx - cx
    dy = yy - cy
    r = np.hypot(dx, dy)
    theta = np.mod(np.arctan2(dx, -dy), two_pi)

    prim_f = np.array(primary_rgb, dtype=np.float32) / 255.0
    info_f = np.array(info_rgb, dtype=np.float32) / 255.0

    # 1. Static Frosted Glassmorphic Medallion Base
    acc_base = np.zeros((H, W, 4), dtype=np.float32)

    # Ambient drop shadow offset slightly downward
    r_shad = np.hypot(dx, dy - 4.5)
    shad_d = np.maximum(0.0, r_shad - (r_med - 4.0))
    shad_a = (0.44 if dark else 0.26) * np.exp(-(shad_d ** 2) / (2.0 * 6.0 ** 2))
    _blend_premul(acc_base, (0.01, 0.02, 0.05) if dark else (0.06, 0.10, 0.18), shad_a)

    # Frosted medallion disc with subtle vertical depth gradient
    disc_cov = np.clip((r_med - r) * 1.2 + 0.5, 0.0, 1.0)
    vert_t = np.clip((dy + r_med) / (2.0 * r_med), 0.0, 1.0)[..., None]
    if dark:
        top_c = np.array([0.10, 0.14, 0.23], dtype=np.float32)
        bot_c = np.array([0.04, 0.06, 0.11], dtype=np.float32)
        disc_rgb = top_c * (1.0 - vert_t) + bot_c * vert_t
        disc_alpha = 0.88
    else:
        top_c = np.array([0.99, 0.995, 1.00], dtype=np.float32)
        bot_c = np.array([0.91, 0.94, 0.98], dtype=np.float32)
        disc_rgb = top_c * (1.0 - vert_t) + bot_c * vert_t
        disc_alpha = 0.92
    _blend_premul(acc_base, disc_rgb, disc_cov * disc_alpha)

    # Soft top-left glass reflection sheen
    d_spec = np.hypot(dx + 16.0, dy + 22.0)
    spec_a = (0.09 if dark else 0.22) * np.exp(-(d_spec ** 2) / (2.0 * 28.0 ** 2)) * disc_cov
    _blend_premul(acc_base, (1.0, 1.0, 1.0), spec_a)

    # Directional outer bezel + subtle inner dial hairline
    rim_cov = np.clip(1.25 - np.abs(r - (r_med - 0.8)) * 1.15, 0.0, 1.0) * disc_cov
    tl_bias = np.clip(0.5 - 0.35 * ((dx + dy) / max(1.0, r_med * 1.4)), 0.15, 0.95)[..., None]
    if dark:
        rim_base = np.array([0.36, 0.44, 0.58], dtype=np.float32)
        rim_hi = 0.55 * prim_f + 0.45 * np.array([0.85, 0.93, 1.0], dtype=np.float32)
        rim_rgb = rim_base * (1.0 - tl_bias) + rim_hi * tl_bias
        rim_a = rim_cov * 0.72
    else:
        rim_base = np.array([0.68, 0.74, 0.84], dtype=np.float32)
        rim_hi = 0.45 * prim_f + 0.55 * np.array([1.0, 1.0, 1.0], dtype=np.float32)
        rim_rgb = rim_base * (1.0 - tl_bias) + rim_hi * tl_bias
        rim_a = rim_cov * 0.85
    _blend_premul(acc_base, rim_rgb, rim_a)

    inner_ring_cov = np.clip(1.0 - np.abs(r - 37.5) * 1.25, 0.0, 1.0) * disc_cov
    _blend_premul(
        acc_base,
        (0.55, 0.68, 0.85) if dark else (0.52, 0.60, 0.72),
        inner_ring_cov * 0.18,
    )

    # Recessed circular track groove
    groove_cov = np.clip((hw_track - np.abs(r - r_track)) * 1.25 + 0.5, 0.0, 1.0)
    _blend_premul(
        acc_base,
        (0.16, 0.22, 0.34) if dark else (0.79, 0.84, 0.91),
        groove_cov * (0.68 if dark else 0.78),
    )

    # Un-premultiply static outer frame once; only inner dial ROI changes across frames
    a_base = np.clip(acc_base[..., 3], 0.0, 1.0)
    safe_base = np.where(a_base > 1e-5, a_base, 1.0)[..., None]
    rgb_base = np.where(a_base[..., None] > 1e-5, acc_base[..., :3] / safe_base, 0.0)
    rgba_base = np.empty((H, W, 4), dtype=np.uint8)
    rgba_base[..., :3] = np.clip(np.round(rgb_base * 255.0), 0.0, 255.0).astype(np.uint8)
    rgba_base[..., 3] = np.clip(np.round(a_base * 255.0), 0.0, 255.0).astype(np.uint8)

    # 2. Vectorized 3D Broadcast Pass Restricted to Rotating Dial ROI (r <= 57)
    y0, y1 = 15, 130
    x0, x1 = 27, 142
    dx_2d = dx[y0:y1, x0:x1]
    dy_2d = dy[y0:y1, x0:x1]
    r_2d = r[y0:y1, x0:x1]
    theta_2d = theta[y0:y1, x0:x1]
    disc_2d = disc_cov[y0:y1, x0:x1]

    # Pre-bake the 12 disjoint radial chronograph ticks into 2D ROI lookup maps
    tick_cov_2d = np.zeros_like(r_2d)
    tick_ang_2d = np.zeros_like(r_2d)
    for k in range(12):
        ang_k = k * (math.pi / 6.0)
        tx, ty = math.sin(ang_k), -math.cos(ang_k)
        r_inner = 28.5 if (k % 3 == 0) else 31.0
        hw_t = 0.95 if (k % 3 == 0) else 0.65
        proj_clamped = np.clip(dx_2d * tx + dy_2d * ty, r_inner, 35.0)
        d_t = np.hypot(dx_2d - proj_clamped * tx, dy_2d - proj_clamped * ty)
        t_cov = np.clip((hw_t - d_t) * 1.25 + 0.5, 0.0, 1.0)
        mask_k = t_cov > tick_cov_2d
        tick_cov_2d = np.maximum(tick_cov_2d, t_cov)
        tick_ang_2d[mask_k] = ang_k

    # Compute dynamic foreground layers using 4-fold 90-degree symmetry when divisible by 4
    use_sym = n_safe % 4 == 0
    n_compute = (n_safe // 4) if use_sym else n_safe
    fg = np.zeros((n_compute, y1 - y0, x1 - x0, 4), dtype=np.float32)

    heads = np.deg2rad(np.arange(n_compute, dtype=np.float32) * (360.0 / n_safe))[:, None, None]
    ux = np.sin(heads)
    uy = -np.cos(heads)

    dx_3 = dx_2d[None, ...]
    dy_3 = dy_2d[None, ...]
    r_3 = r_2d[None, ...]
    theta_3 = theta_2d[None, ...]
    disc_3 = disc_2d[None, ...]

    tick_base_c = np.array([0.52, 0.60, 0.74] if dark else [0.46, 0.53, 0.64], dtype=np.float32)

    # 2a. Radial dial ticks (brighten shortly after sweep passes)
    ang_behind = np.mod(heads - tick_ang_2d[None, ...], two_pi)
    wake = np.where(ang_behind <= np.float32(1.2), np.exp(-(ang_behind ** 2) / np.float32(0.65)), np.float32(0.0))
    w_mix = (wake * np.float32(0.75))[..., None]
    ticks_rgb = tick_base_c * (np.float32(1.0) - w_mix) + prim_f * w_mix
    ticks_a = tick_cov_2d[None, ...] * (np.float32(0.42) + np.float32(0.48) * wake)
    _blend_premul(fg, ticks_rgb, ticks_a)

    # 2b. Leading comet radial bloom halo
    d_head = np.hypot(dx_3 - r_track * ux, dy_3 - r_track * uy)
    glow_scale = np.float32(0.38 if dark else 0.20)
    glow_a = glow_scale * np.exp(-(d_head ** 2) / np.float32(2.0 * 7.5 ** 2)) * disc_3
    _blend_premul(fg, prim_f, glow_a)

    # 2c. Tapered conical gradient sweep arc + rounded glowing cap
    behind = np.mod(heads - theta_3, two_pi)
    prog = np.clip(np.float32(1.0) - behind / sweep_span, np.float32(0.0), np.float32(1.0))
    hw_dyn = hw_track * (np.float32(0.42) + np.float32(0.58) * np.sqrt(prog))
    arc_cov = np.where(
        behind <= sweep_span,
        np.clip((hw_dyn - np.abs(r_3 - r_track)) * np.float32(1.25) + np.float32(0.5), np.float32(0.0), np.float32(1.0))
        * (prog ** np.float32(1.2)),
        np.float32(0.0),
    )
    cap_cov = np.clip((hw_track - d_head) * np.float32(1.25) + np.float32(0.5), np.float32(0.0), np.float32(1.0))
    comet_cov = np.maximum(arc_cov, cap_cov)

    prog_3 = prog[..., None]
    comet_rgb = info_f * (np.float32(1.0) - prog_3) + prim_f * prog_3
    white_mix = np.clip(
        cap_cov * np.float32(0.45) + (prog ** np.float32(3.0)) * np.float32(0.25),
        np.float32(0.0),
        np.float32(0.6),
    )[..., None]
    spec_peak = np.float32(0.28 if dark else 0.14)
    comet_rgb = comet_rgb * (np.float32(1.0) - white_mix) + (np.float32(0.72) * prim_f + spec_peak) * white_mix
    _blend_premul(fg, comet_rgb, comet_cov)

    # 2d. Chronograph rotating timer hand with symmetric ambient elevation shadow
    proj_c = np.clip(dx_3 * ux + dy_3 * uy, np.float32(-7.5), np.float32(26.5))
    d_hand = np.hypot(dx_3 - proj_c * ux, dy_3 - proj_c * uy)
    hw_hand = np.where(
        proj_c < np.float32(0.0),
        np.float32(1.45),
        np.float32(1.45) - np.float32(0.68) * np.clip(proj_c / np.float32(26.5), np.float32(0.0), np.float32(1.0)),
    )
    hand_shad_cov = (
        np.clip(
            (hw_hand + np.float32(1.4) - d_hand) * np.float32(0.85) + np.float32(0.35),
            np.float32(0.0),
            np.float32(1.0),
        )
        * np.float32(0.26)
    )
    _blend_premul(fg, (0.01, 0.02, 0.05), hand_shad_cov)

    hand_cov = np.clip((hw_hand - d_hand) * np.float32(1.3) + np.float32(0.5), np.float32(0.0), np.float32(1.0))
    body_c = np.array([0.95, 0.98, 1.0] if dark else [0.11, 0.17, 0.27], dtype=np.float32)
    tip_t = np.clip((proj_c - np.float32(15.0)) / np.float32(10.0), np.float32(0.0), np.float32(1.0))[..., None]
    hand_rgb = body_c * (np.float32(1.0) - tip_t) + prim_f * tip_t
    _blend_premul(fg, hand_rgb, hand_cov)

    # 2e. Center pivot jewel collar + dark/light inner pin
    pivot_outer = np.clip((np.float32(4.8) - r_3) * np.float32(1.3) + np.float32(0.5), np.float32(0.0), np.float32(1.0))
    _blend_premul(fg, prim_f, pivot_outer)
    pivot_inner = np.clip((np.float32(2.1) - r_3) * np.float32(1.3) + np.float32(0.5), np.float32(0.0), np.float32(1.0))
    _blend_premul(fg, (0.06, 0.09, 0.16) if dark else (0.96, 0.98, 1.0), pivot_inner)

    if use_sym:
        fg_all = np.concatenate(
            [
                fg,
                np.rot90(fg, k=-1, axes=(1, 2)),
                np.rot90(fg, k=-2, axes=(1, 2)),
                np.rot90(fg, k=-3, axes=(1, 2)),
            ],
            axis=0,
        )
    else:
        fg_all = fg

    base_roi = acc_base[y0:y1, x0:x1][None, ...]
    acc_roi = fg_all + base_roi * (np.float32(1.0) - fg_all[..., 3:4])

    # Un-premultiply ROI into uint8 frames
    a_roi = np.clip(acc_roi[..., 3], np.float32(0.0), np.float32(1.0))
    safe_roi = np.where(a_roi > np.float32(1e-5), a_roi, np.float32(1.0))[..., None]
    rgb_roi = np.where(a_roi[..., None] > np.float32(1e-5), acc_roi[..., :3] / safe_roi, np.float32(0.0))

    rgba_all = np.broadcast_to(rgba_base, (n_safe, H, W, 4)).copy()
    rgba_all[:, y0:y1, x0:x1, :3] = np.clip(np.round(rgb_roi * np.float32(255.0)), 0.0, 255.0).astype(np.uint8)
    rgba_all[:, y0:y1, x0:x1, 3] = np.clip(np.round(a_roi * np.float32(255.0)), 0.0, 255.0).astype(np.uint8)

    frames = [Image.fromarray(rgba_all[i], mode="RGBA") for i in range(n_safe)]
    if len(_DIAL_FRAMES_CACHE) >= 16:
        _DIAL_FRAMES_CACHE.clear()
    _DIAL_FRAMES_CACHE[cache_key] = frames
    return list(frames)


def render_timer_overlay_badge(
    dial_frame: Image.Image,
    *,
    elapsed_sec: float,
    pct: float = 0.0,
    dark: bool = True,
    primary_rgb: Tuple[int, int, int] = (76, 194, 255),
    pill_cache: Optional[Dict[Tuple[Any, ...], Image.Image]] = None,
) -> Image.Image:
    """Compose a 168x188 high-DPI rotating timer medallion + live readout pill."""
    tenths = int(min(9999, round(max(0.0, float(elapsed_sec)) * 10.0)))
    pct_i = int(max(0, min(99, round(float(pct)))))
    cache_key = (bool(dark), primary_rgb, tenths, pct_i)

    pill_1x: Optional[Image.Image] = None
    if pill_cache is not None:
        pill_1x = pill_cache.get(cache_key)

    if pill_1x is None:
        pw2, ph2 = 336, 92  # 2x supersampling -> 168x46
        sh = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh)
        d_sh.rounded_rectangle(
            [26, 14, 310, 74],
            radius=30,
            fill=(2, 6, 14, 115 if dark else 65),
        )
        pill_2x = sh.filter(ImageFilter.GaussianBlur(5))

        d2 = ImageDraw.Draw(pill_2x)
        pill_fill = (15, 22, 36, 226) if dark else (246, 249, 254, 236)
        pill_edge = (*primary_rgb, 110) if dark else (150, 170, 198, 150)
        d2.rounded_rectangle(
            [26, 8, 310, 68],
            radius=30,
            fill=pill_fill,
            outline=pill_edge,
            width=2,
        )

        text_str = f"{tenths / 10.0:.1f}s  •  {pct_i}%"
        font = _load_ui_font(22, bold=True)
        bbox = d2.textbbox((0, 0), text_str, font=font)
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])

        dot_d = 12
        gap = 12
        total_w = dot_d + gap + tw
        start_x = (pw2 - total_w) // 2
        pill_cy = (8 + 68) // 2

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
        pill_1x = pill_2x.resize((168, 46), resample=resample)
        if pill_cache is not None:
            if len(pill_cache) >= 64:
                pill_cache.clear()
            pill_cache[cache_key] = pill_1x

    badge = Image.new("RGBA", (168, 188), (0, 0, 0, 0))
    badge.alpha_composite(dial_frame, (0, 0))
    badge.alpha_composite(pill_1x, (0, 142))
    return badge


class ModernActivityTimer(tk.Canvas, ThemedWidgetMixin):
    """Standalone theme-reactive animated chronograph timer widget (168x188 default).

    Renders the subpixel-anti-aliased rotating chronograph medallion and live elapsed/percentage
    pill at an uninterrupted 30 FPS (`interval_ms=33`), with automatic stage-ceiling progress
    gliding between worker milestones.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        bootstyle: str = "primary",
        pct: float = 0.0,
        autostart: bool = False,
        interval_ms: int = 33,
        width: int = 168,
        height: int = 188,
        **kwargs,
    ) -> None:
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._pct = max(0.0, min(100.0, float(pct)))
        self._pct_ceil = default_stage_pct_ceiling(self._pct)
        self._interval_ms = max(16, int(interval_ms))
        self._running = False
        self._start_t = time.perf_counter()
        self._elapsed_override: Optional[float] = None
        self._frame_idx = 0
        self._anim_job: Optional[str] = None
        self._frames_cache_key: Optional[Tuple[bool, Tuple[int, int, int], Tuple[int, int, int], int]] = None
        self._frames: List[Image.Image] = []
        self._pill_cache: Dict[Tuple[Any, ...], Image.Image] = {}
        self._photo: Optional[ImageTk.PhotoImage] = None

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Destroy>", self._on_destroy_cleanup, add="+")

        if autostart:
            self.start(initial_pct=max(5.0, self._pct))
        else:
            self._redraw()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def pct(self) -> float:
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

    def _on_destroy_cleanup(self, e: tk.Event) -> None:
        if e.widget is self:
            self.stop()

    def _ensure_frames(self) -> Tuple[List[Image.Image], bool, Tuple[int, int, int]]:
        p = self.palette
        dark = p.mode == "dark"
        prim = _parse_rgb_hex(p.role_color(self._role), (76, 194, 255))
        info = _parse_rgb_hex(p.info, (56, 189, 248))
        key = (dark, prim, info, SPINNER_FRAME_COUNT)
        if self._frames_cache_key != key or not self._frames:
            self._frames = build_timer_dial_frames(
                dark=dark,
                primary_rgb=prim,
                info_rgb=info,
                num_frames=SPINNER_FRAME_COUNT,
            )
            self._frames_cache_key = key
        return self._frames, dark, prim

    def start(
        self,
        *,
        initial_pct: float = 5.0,
        initial_ceiling: Optional[float] = 16.0,
        interval_ms: Optional[int] = None,
    ) -> None:
        """Start uninterrupted 30 FPS rotation and stage-ceiling progress gliding."""
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
        self._pct = max(0.0, min(99.0, float(initial_pct)))
        self._pct_ceil = (
            float(initial_ceiling)
            if initial_ceiling is not None
            else default_stage_pct_ceiling(self._pct)
        )
        self._frame_idx = 0
        self._redraw()
        self._anim_job = self.after(self._interval_ms, self._tick)

    def stop(self) -> None:
        """Stop the timer animation loop."""
        self._running = False
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

    def reset(self) -> None:
        """Stop and reset frame index, elapsed timer, and percentage to 0."""
        self.stop()
        self._frame_idx = 0
        self._pct = 0.0
        self._pct_ceil = 16.0
        self._elapsed_override = 0.0
        self._redraw()

    def set_progress(
        self,
        pct: float,
        *,
        ceiling: Optional[float] = None,
        elapsed_sec: Optional[float] = None,
    ) -> None:
        """Advance progress monotonically and update the smooth stage ceiling target."""
        new_pct = max(0.0, min(100.0, float(pct)))
        if self._running:
            self._pct = max(self._pct, new_pct)
        else:
            self._pct = new_pct
        target_ceil = (
            float(ceiling)
            if ceiling is not None
            else default_stage_pct_ceiling(self._pct)
        )
        self._pct_ceil = max(self._pct, min(99.0, target_ceil))
        if elapsed_sec is not None:
            self._elapsed_override = max(0.0, float(elapsed_sec))
        self._redraw()

    def step_frame(self) -> None:
        """Advance one animation frame and glide percentage toward the stage ceiling."""
        self._frame_idx = (self._frame_idx + 1) % SPINNER_FRAME_COUNT
        if self._pct < self._pct_ceil:
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
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        frames, dark, prim = self._ensure_frames()
        dial = frames[self._frame_idx % len(frames)]
        badge_im = render_timer_overlay_badge(
            dial,
            elapsed_sec=self.elapsed_sec,
            pct=self._pct,
            dark=dark,
            primary_rgb=prim,
            pill_cache=self._pill_cache,
        )
        self._photo = ImageTk.PhotoImage(badge_im, master=self.winfo_toplevel())
        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        cx, cy = w // 2, h // 2
        existing = self.find_withtag("timer_badge")
        if existing:
            self.coords(existing[0], cx, cy)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(cx, cy, image=self._photo, anchor="center", tags=("timer_badge",))


class ModernBusyOverlay:
    """Non-blocking animated chronograph timer overlay controller for one or more `tk.Canvas` widgets.

    Draws a centered 168x188 high-DPI rotating timer medallion + live readout pill (`tag="busy_overlay"`)
    exclusively on the target canvases (leaving excluded/reference canvases untouched), ticks at 30 FPS
    (`interval_ms=33`), glides percentage smoothly between stage ceilings so the readout never stalls,
    and optionally synchronizes a `ModernProgressBar`.
    """

    def __init__(
        self,
        root: tk.Misc,
        canvases: Sequence[tk.Canvas] = (),
        *,
        progress_bar: Optional[Any] = None,
        bootstyle: str = "primary",
        interval_ms: int = 33,
        tag: str = "busy_overlay",
        stage_ceilings: Sequence[Tuple[float, float]] = DEFAULT_STAGE_CEILINGS,
        animation: str = "timer",
        stream_direction: str = "db_to_pc",
        stream_status: Optional[str] = None,
        source_label: str = "Database",
        target_label: str = "Computer",
        long_running_threshold_sec: float = 3.0,
    ) -> None:
        self.root = root
        self._canvases: List[tk.Canvas] = list(canvases)
        self._progress_bar = progress_bar
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._interval_ms = max(16, int(interval_ms))
        self._tag = tag
        self._stage_ceilings = tuple(stage_ceilings)
        self._animation = (animation or "timer").strip().lower()
        self._stream_direction = normalize_stream_direction(stream_direction)
        self._stream_status = stream_status
        self._source_label = source_label
        self._target_label = target_label
        self._long_running_threshold_sec = max(0.0, float(long_running_threshold_sec))

        self._active = False
        self._start_t = 0.0
        self._pct = 5.0
        self._pct_ceil = 16.0
        self._frame_idx = 0
        self._anim_job: Optional[str] = None
        self._cache_key: Optional[Tuple[bool, Tuple[int, int, int], Tuple[int, int, int], int]] = None
        self._frames: List[Image.Image] = []
        self._stream_cache_key: Optional[Tuple[Any, ...]] = None
        self._stream_frames: List[Image.Image] = []
        self._pill_cache: Dict[Tuple[Any, ...], Image.Image] = {}
        self._stream_pill_cache: Dict[Tuple[Any, ...], Image.Image] = {}
        self._photo: Optional[ImageTk.PhotoImage] = None

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def pct(self) -> float:
        return self._pct

    @property
    def pct_ceiling(self) -> float:
        return self._pct_ceil

    @property
    def frame_index(self) -> int:
        return self._frame_idx

    @property
    def photo(self) -> Optional[ImageTk.PhotoImage]:
        return self._photo

    def set_canvases(self, canvases: Sequence[tk.Canvas]) -> None:
        self._canvases = list(canvases)

    def set_animation(self, animation: str) -> None:
        """Set overlay animation mode: `'timer'`, `'data_stream'`, or `'auto'`."""
        self._animation = (animation or "timer").strip().lower()
        if self._active:
            self.render_and_push_frame()

    def set_stream_direction(self, direction: str, status_text: Optional[str] = None) -> None:
        """Update the Database <-> Computer stream direction and optional status text."""
        self._stream_direction = normalize_stream_direction(direction)
        if status_text is not None:
            self._stream_status = status_text
        self._stream_cache_key = None
        if self._active:
            self.render_and_push_frame()

    def stage_ceiling_for(self, pct: float) -> float:
        return default_stage_pct_ceiling(pct, self._stage_ceilings)

    def _ensure_frames(self) -> Tuple[List[Image.Image], bool, Tuple[int, int, int]]:
        p = ThemeManager.instance().palette
        dark = p.mode == "dark"
        prim = _parse_rgb_hex(p.role_color(self._role), (76, 194, 255))
        info = _parse_rgb_hex(p.info, (56, 189, 248))
        key = (dark, prim, info, SPINNER_FRAME_COUNT)
        if self._cache_key != key or not self._frames:
            self._frames = build_timer_dial_frames(
                dark=dark,
                primary_rgb=prim,
                info_rgb=info,
                num_frames=SPINNER_FRAME_COUNT,
            )
            self._cache_key = key
        return self._frames, dark, prim

    def _ensure_stream_frames(self) -> Tuple[List[Image.Image], bool, Tuple[int, int, int]]:
        p = ThemeManager.instance().palette
        dark = p.mode == "dark"
        prim = _parse_rgb_hex(p.role_color(self._role), (76, 194, 255))
        info = _parse_rgb_hex(p.info, (56, 189, 248))
        key = (
            dark,
            prim,
            info,
            self._stream_direction,
            self._source_label,
            self._target_label,
            DATA_STREAM_FRAME_COUNT,
        )
        if self._stream_cache_key != key or not self._stream_frames:
            self._stream_frames = build_data_stream_frames(
                dark=dark,
                primary_rgb=prim,
                info_rgb=info,
                direction=self._stream_direction,
                source_label=self._source_label,
                target_label=self._target_label,
                num_frames=DATA_STREAM_FRAME_COUNT,
            )
            self._stream_cache_key = key
        return self._stream_frames, dark, prim

    def apply_to_canvases(self, canvases: Optional[Sequence[tk.Canvas]] = None) -> None:
        """Create or update the centered `busy_overlay` canvas item on each target canvas."""
        if self._photo is None:
            return
        targets = self._canvases if canvases is None else canvases
        for cv in targets:
            try:
                if not cv.winfo_exists():
                    continue
                cw = cv.winfo_width()
                ch = cv.winfo_height()
                if cw <= 10:
                    cw = max(240, cv.winfo_reqwidth())
                if ch <= 10:
                    ch = max(220, cv.winfo_reqheight())
                cx, cy = cw // 2, ch // 2
                existing = cv.find_withtag(self._tag)
                if existing:
                    cv.coords(existing[0], cx, cy)
                    cv.itemconfigure(existing[0], image=self._photo)
                    cv.tag_raise(self._tag)
                else:
                    cv.create_image(
                        cx,
                        cy,
                        image=self._photo,
                        anchor="center",
                        tags=(self._tag,),
                    )
            except tk.TclError:
                continue

    def render_and_push_frame(self) -> Optional[ImageTk.PhotoImage]:
        """Render the current chronograph or data-stream frame + status pill and push it onto target canvases."""
        try:
            if not self._active or not self.root.winfo_exists():
                return None
            elapsed = max(0.0, time.perf_counter() - self._start_t)
            use_stream = self._animation == "data_stream" or (
                self._animation == "auto" and elapsed >= self._long_running_threshold_sec
            )
            if use_stream:
                stream_frames, dark, prim = self._ensure_stream_frames()
                s_frame = stream_frames[self._frame_idx % len(stream_frames)]
                status = (
                    self._stream_status
                    if self._stream_status is not None
                    else default_stream_status(self._stream_direction)
                )
                badge_im = render_data_stream_overlay_badge(
                    s_frame,
                    elapsed_sec=elapsed,
                    pct=self._pct,
                    status_text=status,
                    dark=dark,
                    primary_rgb=prim,
                    show_pill=True,
                    pill_cache=self._stream_pill_cache,
                )
            else:
                frames, dark, prim = self._ensure_frames()
                dial = frames[self._frame_idx % len(frames)]
                badge_im = render_timer_overlay_badge(
                    dial,
                    elapsed_sec=elapsed,
                    pct=self._pct,
                    dark=dark,
                    primary_rgb=prim,
                    pill_cache=self._pill_cache,
                )
            self._photo = ImageTk.PhotoImage(badge_im, master=self.root)
            self.apply_to_canvases()
            return self._photo
        except tk.TclError:
            return None

    def start(
        self,
        *,
        initial_pct: float = 5.0,
        initial_ceiling: float = 16.0,
        canvases: Optional[Sequence[tk.Canvas]] = None,
    ) -> None:
        """Start the 30 FPS busy overlay animation and render frame 0 immediately."""
        if canvases is not None:
            self._canvases = list(canvases)
        if self._anim_job is not None:
            try:
                self.root.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        self._active = True
        self._start_t = time.perf_counter()
        self._pct = float(initial_pct)
        self._pct_ceil = float(initial_ceiling)
        self._frame_idx = 0
        if self._progress_bar is not None:
            try:
                self._progress_bar.set(int(round(self._pct)))
            except Exception:
                pass
        self.render_and_push_frame()
        try:
            self._anim_job = self.root.after(self._interval_ms, self._tick)
        except tk.TclError:
            self._anim_job = None

    def set_progress(self, pct: float, *, ceiling: Optional[float] = None) -> float:
        """Update progress monotonically and advance the stage ceiling target."""
        clamped = max(self._pct, min(99.0, float(pct)))
        self._pct = clamped
        target_ceil = self.stage_ceiling_for(clamped) if ceiling is None else float(ceiling)
        self._pct_ceil = max(self._pct_ceil, min(99.0, target_ceil))
        if self._progress_bar is not None:
            try:
                self._progress_bar.set(int(round(clamped)))
            except Exception:
                pass
        if self._active:
            self.render_and_push_frame()
        return self._pct

    def _tick(self) -> None:
        self._anim_job = None
        try:
            if not self._active or not self.root.winfo_exists():
                return
            self._frame_idx = (self._frame_idx + 1) % SPINNER_FRAME_COUNT
            if self._pct < self._pct_ceil:
                prev_i = int(round(self._pct))
                step = max(0.22, (self._pct_ceil - self._pct) * 0.055)
                self._pct = min(self._pct_ceil, self._pct + step)
                new_i = int(round(self._pct))
                if new_i != prev_i and self._progress_bar is not None:
                    try:
                        self._progress_bar.set(new_i)
                    except Exception:
                        pass
            self.render_and_push_frame()
            self._anim_job = self.root.after(self._interval_ms, self._tick)
        except tk.TclError:
            self._anim_job = None

    def stop(self, extra_canvases: Sequence[tk.Canvas] = ()) -> None:
        """Stop the animation loop and remove `busy_overlay` items from all canvases."""
        self._active = False
        if self._anim_job is not None:
            try:
                self.root.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        seen: set[int] = set()
        for cv in (*self._canvases, *extra_canvases):
            if id(cv) in seen:
                continue
            seen.add(id(cv))
            try:
                if cv.winfo_exists():
                    cv.delete(self._tag)
            except tk.TclError:
                pass
        self._photo = None


# ── Uninterrupted Execution Engine (GIL-Free Subprocess IPC + TaskRunner) ────


def _read_exact_bytes(pipe: Any, n: int) -> bytes:
    """Read exactly `n` bytes from a binary pipe, or return truncated bytes on EOF."""
    buf = bytearray()
    while len(buf) < n:
        chunk = pipe.read(n - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def write_ipc_frame(pipe: Any, payload: Any) -> None:
    """Serialize `payload` with a 4-byte big-endian length prefix onto a binary pipe."""
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    pipe.write(struct.pack(">I", len(data)))
    pipe.write(data)
    pipe.flush()


def read_ipc_frame(pipe: Any) -> Any:
    """Read and deserialize one 4-byte length-prefixed frame from a binary pipe."""
    hdr = _read_exact_bytes(pipe, 4)
    if not hdr:
        raise EOFError("Subprocess worker pipe closed.")
    if len(hdr) < 4:
        raise EOFError("Truncated subprocess worker frame header.")
    (length,) = struct.unpack(">I", hdr)
    body = _read_exact_bytes(pipe, length)
    if len(body) < length:
        raise EOFError("Truncated subprocess worker frame body.")
    return pickle.loads(body)


def run_subprocess_worker_loop(
    handlers: Mapping[str, Callable[..., Any]],
    *,
    init_fn: Optional[Callable[[], None]] = None,
) -> int:
    """Run a persistent subprocess loop that executes GIL-heavy native tasks over binary stdio IPC.

    Why this is essential for uninterrupted ModernTtk timers:
    Python's `threading.Thread` shares the single process GIL. When a native C/Rust extension
    (such as `vtracer.convert_pixels` or `resvg_py.svg_to_bytes`) runs for 0.5–1.5s without
    releasing the GIL, Tkinter's `after(33, ...)` timer freezes mid-spin (e.g. around 35%).
    Running those native calls inside this persistent child process keeps the main GUI process
    100% GIL-free so `ModernActivityTimer` and `ModernBusyOverlay` spin at a rock-solid 30 FPS.
    """
    in_pipe = sys.stdin.buffer
    out_pipe = sys.stdout.buffer
    if sys.stderr is not None:
        sys.stdout = sys.stderr

    if init_fn is not None:
        try:
            init_fn()
        except Exception:
            pass

    while True:
        try:
            req = read_ipc_frame(in_pipe)
        except EOFError:
            return 0
        except Exception as exc:
            write_ipc_frame(out_pipe, (False, f"{type(exc).__name__}: {exc}"))
            continue

        op = req[0] if isinstance(req, (tuple, list)) and req else ""
        args = req[1:] if isinstance(req, (tuple, list)) and len(req) > 1 else ()
        try:
            if op == "ping":
                write_ipc_frame(out_pipe, (True, "pong"))
            elif op == "shutdown":
                write_ipc_frame(out_pipe, (True, None))
                return 0
            elif op in handlers:
                res = handlers[op](*args)
                write_ipc_frame(out_pipe, (True, res))
            else:
                write_ipc_frame(out_pipe, (False, f"Unknown worker op: {op!r}"))
        except Exception as exc:
            write_ipc_frame(out_pipe, (False, f"{type(exc).__name__}: {exc}"))


class ModernSubprocessWorker:
    """Thread-safe persistent subprocess client for offloading GIL-holding C/Rust extensions."""

    def __init__(
        self,
        *,
        script_path: Optional[str | Path] = None,
        worker_flag: str = "--native-svg-worker",
        auto_atexit: bool = True,
    ) -> None:
        self._script_path = Path(script_path).resolve() if script_path is not None else None
        self._worker_flag = worker_flag
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen[bytes]] = None
        if auto_atexit:
            atexit.register(self.shutdown)

    @staticmethod
    def should_offload() -> bool:
        """Return True when called from a background thread so the GUI main thread's GIL stays free."""
        return threading.current_thread() is not threading.main_thread()

    def _close_proc_unlocked(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        for pipe in (proc.stdin, proc.stdout):
            if pipe is not None:
                try:
                    pipe.close()
                except Exception:
                    pass
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=0.5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _spawn_unlocked(self) -> subprocess.Popen[bytes]:
        self._close_proc_unlocked()
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, self._worker_flag]
        else:
            target = self._script_path or Path(sys.argv[0]).resolve()
            cmd = [sys.executable, str(target), self._worker_flag]
        kw: Dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        proc = subprocess.Popen(cmd, **kw)
        self._proc = proc
        return proc

    def request(self, payload: Tuple[Any, ...]) -> Any:
        """Send a request tuple `(op, *args)` to the persistent worker subprocess and return the result."""
        with self._lock:
            last_exc: Optional[BaseException] = None
            for attempt in range(2):
                proc = self._proc
                if proc is None or proc.poll() is not None or attempt > 0:
                    proc = self._spawn_unlocked()
                try:
                    assert proc.stdin is not None and proc.stdout is not None
                    write_ipc_frame(proc.stdin, payload)
                    ok, val = read_ipc_frame(proc.stdout)
                except (OSError, EOFError, BrokenPipeError, struct.error, pickle.UnpicklingError) as exc:
                    last_exc = exc
                    self._close_proc_unlocked()
                    continue
                if not ok:
                    raise RuntimeError(str(val))
                return val
            raise last_exc if last_exc is not None else EOFError("Subprocess worker failed.")

    def prewarm(self) -> bool:
        """Spawn and ping the persistent subprocess worker so the first task has zero startup lag."""
        try:
            return self.request(("ping",)) == "pong"
        except Exception:
            return False

    def shutdown(self) -> None:
        """Gracefully terminate the persistent worker subprocess."""
        with self._lock:
            proc = self._proc
            if proc is not None and proc.poll() is None and proc.stdin is not None and proc.stdout is not None:
                try:
                    write_ipc_frame(proc.stdin, ("shutdown",))
                    read_ipc_frame(proc.stdout)
                    proc.wait(timeout=0.5)
                except Exception:
                    pass
            self._close_proc_unlocked()


class ModernTaskRunner:
    """High-level coordinator that runs background tasks while keeping `ModernBusyOverlay` uninterrupted.

    Combines:
    - A versioned background `threading.Thread`
    - A non-blocking `queue.SimpleQueue` polled every `poll_ms=25` ms on the Tkinter thread
    - Automatic coordination with `ModernBusyOverlay` (or `ModernActivityTimer`) so progress milestones
      glide smoothly and superseded runs are cleanly ignored.
    """

    def __init__(
        self,
        root: tk.Misc,
        *,
        overlay: Optional[ModernBusyOverlay] = None,
        progress_bar: Optional[Any] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        poll_ms: int = 25,
    ) -> None:
        self.root = root
        self.overlay = overlay
        self.progress_bar = progress_bar
        self.status_callback = status_callback
        self.poll_ms = max(10, int(poll_ms))
        self._queue: "queue.SimpleQueue[Tuple[str, int, Any]]" = queue.SimpleQueue()
        self._token = 0
        self._busy = False
        self._poll_job: Optional[str] = None
        self._on_done: Dict[int, Callable[[Any], None]] = {}
        self._on_error: Dict[int, Callable[[BaseException], None]] = {}

    @property
    def is_busy(self) -> bool:
        return self._busy

    def start(
        self,
        task_fn: Callable[[Callable[[float, str], None]], Any],
        *,
        on_done: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[BaseException], None]] = None,
        initial_message: str = "Working...",
    ) -> int:
        """Launch `task_fn(progress_cb)` on a daemon thread and animate the busy overlay uninterrupted."""
        self._token += 1
        token = self._token
        self._busy = True
        if on_done is not None:
            self._on_done[token] = on_done
        if on_error is not None:
            self._on_error[token] = on_error

        if self.status_callback is not None and initial_message:
            self.status_callback(initial_message)
        if self.overlay is not None:
            self.overlay.start(initial_pct=5.0, initial_ceiling=16.0)
        elif self.progress_bar is not None:
            try:
                self.progress_bar.set(5)
            except Exception:
                pass

        def _progress_cb(pct: float, msg: str = "") -> None:
            self._queue.put(("progress", token, (float(pct), str(msg))))

        def _worker() -> None:
            try:
                res = task_fn(_progress_cb)
                self._queue.put(("done", token, res))
            except BaseException as exc:
                self._queue.put(("error", token, exc))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        self._ensure_polling()
        return token

    def _ensure_polling(self) -> None:
        if self._poll_job is None and self.root.winfo_exists():
            try:
                self._poll_job = self.root.after(self.poll_ms, self._poll_step)
            except tk.TclError:
                self._poll_job = None

    def _poll_step(self) -> None:
        self._poll_job = None
        self.drain_queue()
        if self._busy and self.root.winfo_exists():
            try:
                self._poll_job = self.root.after(self.poll_ms, self._poll_step)
            except tk.TclError:
                self._poll_job = None

    def drain_queue(self) -> None:
        """Process all pending progress/completion messages from the worker queue immediately."""
        while True:
            try:
                kind, token, payload = self._queue.get_nowait()
            except queue.Empty:
                break

            if token != self._token:
                self._on_done.pop(token, None)
                self._on_error.pop(token, None)
                continue

            if kind == "progress":
                pct, msg = payload
                if self.overlay is not None:
                    self.overlay.set_progress(pct)
                elif self.progress_bar is not None:
                    try:
                        self.progress_bar.set(int(round(pct)))
                    except Exception:
                        pass
                if msg and self.status_callback is not None:
                    self.status_callback(msg)
            elif kind == "error":
                self._busy = False
                if self.overlay is not None:
                    self.overlay.stop()
                if self.progress_bar is not None:
                    try:
                        self.progress_bar.set(0)
                    except Exception:
                        pass
                err_cb = self._on_error.pop(token, None)
                self._on_done.pop(token, None)
                if err_cb is not None:
                    err_cb(payload)
            elif kind == "done":
                self._busy = False
                if self.overlay is not None:
                    self.overlay.stop()
                if self.progress_bar is not None:
                    try:
                        self.progress_bar.set(100)
                    except Exception:
                        pass
                done_cb = self._on_done.pop(token, None)
                self._on_error.pop(token, None)
                if done_cb is not None:
                    done_cb(payload)

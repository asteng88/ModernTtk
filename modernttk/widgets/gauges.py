"""Rich supersampled gauge widget suite for ModernTtk.

Provides 6 distinct theme-reactive, animated gauge widgets alongside `ModernMeter`:
- `ModernSemiGauge` / `SemiGauge` / `ArcGauge` (180° half-circle executive KPI arch gauge with optional zone bands & target tick)
- `ModernSpeedometer` / `Speedometer` / `DialGauge` (240° instrument dial with major/minor ticks, zone arc, animated tapered needle & readout pill)
- `ModernSegmentedGauge` / `SegmentedGauge` / `LedGauge` (Discrete LED-segment arc or bar meter with semantic color progression)
- `ModernLinearGauge` / `LinearGauge` / `BulletGauge` (Horizontal/vertical bullet & scale gauge with range bands, benchmark target marker & ticks)
- `ModernLiquidGauge` / `LiquidGauge` / `TankGauge` (Circular glass orb with 30 FPS animated dual-sine-wave liquid fill & contrast-aware text)
- `ModernMultiRingGauge` / `MultiRingGauge` / `ActivityRings` (Concentric multi-metric activity rings with live legend)
"""

from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageTk

from ..themes import ThemePalette
from ..utils import blend_colors, contrast_text_color, hex_to_rgb
from .base import ThemedWidgetMixin


def _load_gauge_font(size_px: int, *, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


def _format_gauge_value(
    value: float,
    prefix: str = "",
    suffix: str = "%",
    decimals: int = 0,
) -> str:
    if decimals <= 0:
        num = f"{int(round(value)):,}"
    else:
        num = f"{value:,.{decimals}f}"
    return f"{prefix}{num}{suffix}"


def _resolve_threshold_role(
    value: float,
    base_role: str,
    thresholds: Sequence[Tuple[float, str]],
) -> str:
    role = base_role
    for thresh_val, thresh_role in sorted(thresholds, key=lambda item: item[0]):
        if value >= thresh_val:
            role = thresh_role
    return role


class _AnimatedGaugeBase(tk.Canvas, ThemedWidgetMixin):
    """Shared animation, value clamping, threshold resolution, and cleanup base for scalar gauges."""

    def __init__(
        self,
        master: Optional[tk.Misc],
        *,
        value: float,
        minimum: float,
        maximum: float,
        bootstyle: str,
        textprefix: str,
        textsuffix: str,
        subtext: str,
        decimals: int,
        thresholds: Optional[Sequence[Tuple[float, str]]],
        width: int,
        height: int,
        **kwargs,
    ) -> None:
        self._min = float(minimum)
        self._max = float(maximum) if maximum > minimum else self._min + 1.0
        self._value = max(self._min, min(self._max, float(value)))
        self._target_value = self._value
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._prefix = textprefix
        self._suffix = textsuffix
        self._subtext = subtext
        self._decimals = max(0, int(decimals))
        self._thresholds: List[Tuple[float, str]] = list(thresholds) if thresholds else []
        self._anim_job: Optional[str] = None
        self._photo: Optional[ImageTk.PhotoImage] = None

        super().__init__(
            master,
            width=int(width),
            height=int(height),
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Destroy>", self._on_destroy_anim, add="+")

    def _on_destroy_anim(self, e: tk.Event) -> None:
        if e.widget is self and self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

    @property
    def ratio(self) -> float:
        return max(0.0, min(1.0, (self._value - self._min) / (self._max - self._min)))

    def get(self) -> float:
        return self._target_value

    def set(
        self,
        value: float,
        *,
        subtext: Optional[str] = None,
        bootstyle: Optional[str] = None,
        animate: bool = True,
    ) -> None:
        self._target_value = max(self._min, min(self._max, float(value)))
        if subtext is not None:
            self._subtext = subtext
        if bootstyle is not None:
            self._role = bootstyle.split("-")[0]

        span = self._max - self._min
        if not animate or abs(self._target_value - self._value) <= span * 0.003:
            self._value = self._target_value
            self._redraw()
            return
        self._step_animation()

    def _step_animation(self) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        if not self.winfo_exists():
            return
        diff = self._target_value - self._value
        span = self._max - self._min
        if abs(diff) <= max(0.05, span * 0.003):
            self._value = self._target_value
            self._redraw()
            return
        self._value += diff * 0.25
        self._redraw()
        try:
            self._anim_job = self.after(16, self._step_animation)
        except tk.TclError:
            self._anim_job = None

    def _active_role(self) -> str:
        return _resolve_threshold_role(self._value, self._role, self._thresholds)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:  # pragma: no cover - implemented by subclasses
        raise NotImplementedError


# ── 1. ModernSemiGauge (180° Half-Circle Arch KPI Gauge) ─────────────────────


class ModernSemiGauge(_AnimatedGaugeBase):
    """Supersampled 180° half-circle executive KPI gauge with optional zone bands and target marker."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 68.0,
        minimum: float = 0.0,
        maximum: float = 100.0,
        width: int = 210,
        height: int = 128,
        thickness: int = 16,
        bootstyle: str = "primary",
        textprefix: str = "",
        textsuffix: str = "%",
        subtext: str = "",
        decimals: int = 0,
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        target: Optional[float] = None,
        show_minmax: bool = True,
        **kwargs,
    ) -> None:
        self._thickness = max(6, int(thickness))
        self._target_marker = target
        self._show_minmax = bool(show_minmax)
        super().__init__(
            master,
            value=value,
            minimum=minimum,
            maximum=maximum,
            bootstyle=bootstyle,
            textprefix=textprefix,
            textsuffix=textsuffix,
            subtext=subtext,
            decimals=decimals,
            thresholds=thresholds,
            width=width,
            height=height,
            **kwargs,
        )
        self._redraw()

    def set_target(self, target: Optional[float]) -> None:
        self._target_marker = target
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(120, self.winfo_width(), int(self["width"]))
        h = max(84, self.winfo_height(), int(self["height"]))
        scale = 3
        W, H = w * scale, h * scale

        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        track_rgba = (*hex_to_rgb(p.surface_alt), 255)
        accent_hex = p.role_color(self._active_role())
        accent_rgba = (*hex_to_rgb(accent_hex), 255)

        img = Image.new("RGBA", (W, H), bg_rgba)
        draw = ImageDraw.Draw(img)

        th = self._thickness * scale
        cap_r = th / 2.0
        bottom_margin = (26 if self._show_minmax else 14) * scale
        avail_r = min((W - 28 * scale) / 2.0, H - bottom_margin - 10 * scale)
        outer_r = max(24 * scale, avail_r)
        cx = W / 2.0
        cy = H - bottom_margin
        bbox = [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r]
        mid_r = outer_r - th / 2.0

        def _cap(deg: float, col: Tuple[int, int, int, int]) -> None:
            rad = math.radians(deg)
            x = cx + mid_r * math.cos(rad)
            y = cy + mid_r * math.sin(rad)
            draw.ellipse([x - cap_r, y - cap_r, x + cap_r, y + cap_r], fill=col)

        # Background 180° arch (180° = left, 360° = right in Pillow screen coords)
        draw.arc(bbox, start=180, end=360, fill=track_rgba, width=th)
        _cap(180.0, track_rgba)
        _cap(360.0, track_rgba)

        # Active fill arc
        r_val = self.ratio
        if r_val > 0.004:
            end_deg = 180.0 + 180.0 * r_val
            draw.arc(bbox, start=180.0, end=end_deg, fill=accent_rgba, width=th)
            _cap(180.0, accent_rgba)
            _cap(end_deg, accent_rgba)

        # Optional benchmark target marker tick
        if self._target_marker is not None:
            t_ratio = max(0.0, min(1.0, (self._target_marker - self._min) / (self._max - self._min)))
            t_rad = math.radians(180.0 + 180.0 * t_ratio)
            r_in = outer_r - th - 4 * scale
            r_out = outer_r + 4 * scale
            marker_col = (*hex_to_rgb(p.fg), 235)
            draw.line(
                [
                    (cx + r_in * math.cos(t_rad), cy + r_in * math.sin(t_rad)),
                    (cx + r_out * math.cos(t_rad), cy + r_out * math.sin(t_rad)),
                ],
                fill=marker_col,
                width=max(2, int(2.4 * scale)),
            )

        # Centered value readout + subtext
        val_str = _format_gauge_value(self._value, self._prefix, self._suffix, self._decimals)
        val_font = _load_gauge_font(max(14, int(outer_r * 0.28)), bold=True)
        v_box = draw.textbbox((0, 0), val_str, font=val_font)
        vw, vh = v_box[2] - v_box[0], v_box[3] - v_box[1]
        val_y = cy - outer_r * 0.42 - vh / 2.0
        draw.text(
            (cx - vw / 2.0 - v_box[0], val_y - v_box[1]),
            val_str,
            font=val_font,
            fill=(*hex_to_rgb(p.fg), 255),
        )

        if self._subtext:
            sub_font = _load_gauge_font(max(9, int(10 * scale)), bold=True)
            s_box = draw.textbbox((0, 0), self._subtext, font=sub_font)
            sw = s_box[2] - s_box[0]
            draw.text(
                (cx - sw / 2.0 - s_box[0], cy - 10 * scale - s_box[1]),
                self._subtext,
                font=sub_font,
                fill=(*hex_to_rgb(p.fg_muted), 255),
            )

        if self._show_minmax:
            mm_font = _load_gauge_font(max(8, int(9 * scale)), bold=False)
            mm_col = (*hex_to_rgb(p.fg_muted), 220)
            min_s = _format_gauge_value(self._min, "", "", 0)
            max_s = _format_gauge_value(self._max, "", "", 0)
            mb1 = draw.textbbox((0, 0), min_s, font=mm_font)
            mb2 = draw.textbbox((0, 0), max_s, font=mm_font)
            draw.text(
                (cx - mid_r - (mb1[2] - mb1[0]) / 2.0 - mb1[0], cy + 7 * scale - mb1[1]),
                min_s,
                font=mm_font,
                fill=mm_col,
            )
            draw.text(
                (cx + mid_r - (mb2[2] - mb2[0]) / 2.0 - mb2[0], cy + 7 * scale - mb2[1]),
                max_s,
                font=mm_font,
                fill=mm_col,
            )

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((w, h), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))


# ── 2. ModernSpeedometer (240° Instrument Needle Dial Gauge) ─────────────────


class ModernSpeedometer(_AnimatedGaugeBase):
    """Supersampled 240° automotive/telemetry dial gauge with ticks, color zones, and animated needle."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 64.0,
        minimum: float = 0.0,
        maximum: float = 100.0,
        size: int = 196,
        bootstyle: str = "primary",
        textprefix: str = "",
        textsuffix: str = "%",
        subtext: str = "Throughput",
        decimals: int = 0,
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        zones: Optional[Sequence[Tuple[float, float, str]]] = None,
        major_ticks: int = 5,
        minor_ticks: int = 4,
        **kwargs,
    ) -> None:
        self._size = max(120, int(size))
        self._zones = list(zones) if zones is not None else [
            (0.0, 0.60, "success"),
            (0.60, 0.85, "warning"),
            (0.85, 1.0, "danger"),
        ]
        self._major_ticks = max(2, int(major_ticks))
        self._minor_ticks = max(0, int(minor_ticks))
        super().__init__(
            master,
            value=value,
            minimum=minimum,
            maximum=maximum,
            bootstyle=bootstyle,
            textprefix=textprefix,
            textsuffix=textsuffix,
            subtext=subtext,
            decimals=decimals,
            thresholds=thresholds,
            width=self._size,
            height=self._size,
            **kwargs,
        )
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(self._size, self.winfo_width())
        h = max(self._size, self.winfo_height())
        s_px = min(w, h)
        scale = 3
        S = s_px * scale
        cx = S / 2.0
        cy = S / 2.0

        dark = p.mode == "dark"
        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        img = Image.new("RGBA", (S, S), bg_rgba)
        draw = ImageDraw.Draw(img)

        outer_r = S * 0.45
        face_fill = (*hex_to_rgb(p.surface), 255)
        rim_col = (*hex_to_rgb(p.border_strong), 255)
        draw.ellipse(
            [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
            fill=face_fill,
            outline=rim_col,
            width=max(2, int(1.6 * scale)),
        )

        # 240° sweep: 150° (bottom-left) clockwise to 390° (bottom-right)
        start_deg = 150.0
        sweep_deg = 240.0
        arc_r = outer_r * 0.86
        arc_w = max(4, int(outer_r * 0.11))
        arc_box = [cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r]

        # Track background
        track_col = (*hex_to_rgb(p.surface_alt), 255)
        draw.arc(arc_box, start=start_deg, end=start_deg + sweep_deg, fill=track_col, width=arc_w)

        # Colored zone bands
        for z_start, z_end, z_role in self._zones:
            # Support both normalized [0..1] and raw [min..max] zone coordinates
            if z_end > 1.01 or z_start > 1.01:
                u0 = max(0.0, min(1.0, (z_start - self._min) / (self._max - self._min)))
                u1 = max(0.0, min(1.0, (z_end - self._min) / (self._max - self._min)))
            else:
                u0 = max(0.0, min(1.0, float(z_start)))
                u1 = max(0.0, min(1.0, float(z_end)))
            if u1 <= u0:
                continue
            z_hex = p.role_color(z_role)
            z_col = (*hex_to_rgb(z_hex), 220 if dark else 235)
            draw.arc(
                arc_box,
                start=start_deg + sweep_deg * u0,
                end=start_deg + sweep_deg * u1,
                fill=z_col,
                width=arc_w,
            )

        # Major and minor ticks + scale numbers
        total_steps = (self._major_ticks - 1) * (self._minor_ticks + 1)
        tick_outer = arc_r - arc_w - 3 * scale
        tick_font = _load_gauge_font(max(8, int(outer_r * 0.125)), bold=False)
        for step_i in range(total_steps + 1):
            u = step_i / float(max(1, total_steps))
            ang = math.radians(start_deg + sweep_deg * u)
            is_major = (step_i % (self._minor_ticks + 1)) == 0
            tick_len = (10 if is_major else 5.5) * scale
            tick_in = tick_outer - tick_len
            t_col = (*hex_to_rgb(p.fg if is_major else p.fg_muted), 230 if is_major else 150)
            draw.line(
                [
                    (cx + tick_in * math.cos(ang), cy + tick_in * math.sin(ang)),
                    (cx + tick_outer * math.cos(ang), cy + tick_outer * math.sin(ang)),
                ],
                fill=t_col,
                width=max(1, int((1.8 if is_major else 1.0) * scale)),
            )
            if is_major:
                lbl_val = self._min + u * (self._max - self._min)
                lbl_txt = f"{int(round(lbl_val))}"
                lb = draw.textbbox((0, 0), lbl_txt, font=tick_font)
                lw, lh = lb[2] - lb[0], lb[3] - lb[1]
                lr = tick_in - 11 * scale
                lx = cx + lr * math.cos(ang) - lw / 2.0 - lb[0]
                ly = cy + lr * math.sin(ang) - lh / 2.0 - lb[1]
                draw.text((lx, ly), lbl_txt, font=tick_font, fill=(*hex_to_rgb(p.fg_muted), 230))

        # Tapered animated needle + subtle shadow
        needle_deg = start_deg + sweep_deg * self.ratio
        rad = math.radians(needle_deg)
        nx, ny = math.cos(rad), math.sin(rad)
        px_v, py_v = -ny, nx
        tip_len = tick_outer - 2 * scale
        tail_len = 13 * scale
        base_hw = 3.2 * scale
        tip_hw = 0.8 * scale

        def _needle_poly(ox: float, oy: float) -> List[Tuple[float, float]]:
            return [
                (cx + ox - nx * tail_len + px_v * (base_hw * 0.75), cy + oy - ny * tail_len + py_v * (base_hw * 0.75)),
                (cx + ox + nx * tip_len + px_v * tip_hw, cy + oy + ny * tip_len + py_v * tip_hw),
                (cx + ox + nx * tip_len - px_v * tip_hw, cy + oy + ny * tip_len - py_v * tip_hw),
                (cx + ox - nx * tail_len - px_v * (base_hw * 0.75), cy + oy - ny * tail_len - py_v * (base_hw * 0.75)),
            ]

        draw.polygon(_needle_poly(1.5 * scale, 2.2 * scale), fill=(0, 0, 0, 70 if dark else 40))
        accent_hex = p.role_color(self._active_role())
        needle_col = (*hex_to_rgb(accent_hex), 255)
        draw.polygon(_needle_poly(0.0, 0.0), fill=needle_col)

        # Center pivot cap
        piv_r = 7.5 * scale
        draw.ellipse(
            [cx - piv_r, cy - piv_r, cx + piv_r, cy + piv_r],
            fill=needle_col,
        )
        inner_r = 3.5 * scale
        draw.ellipse(
            [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
            fill=face_fill,
        )

        # Digital readout pill + subtext in lower quadrant
        val_str = _format_gauge_value(self._value, self._prefix, self._suffix, self._decimals)
        val_font = _load_gauge_font(max(12, int(outer_r * 0.21)), bold=True)
        vb = draw.textbbox((0, 0), val_str, font=val_font)
        vw, vh = vb[2] - vb[0], vb[3] - vb[1]
        pill_y = cy + outer_r * 0.42
        pw = max(vw + 18 * scale, 54 * scale)
        ph = vh + 9 * scale
        draw.rounded_rectangle(
            [cx - pw / 2.0, pill_y - ph / 2.0, cx + pw / 2.0, pill_y + ph / 2.0],
            radius=ph / 2.0,
            fill=(*hex_to_rgb(p.surface_alt), 245),
            outline=(*hex_to_rgb(p.border), 210),
            width=max(1, scale),
        )
        draw.text(
            (cx - vw / 2.0 - vb[0], pill_y - vh / 2.0 - vb[1] - 0.5 * scale),
            val_str,
            font=val_font,
            fill=(*hex_to_rgb(p.fg), 255),
        )

        if self._subtext:
            sub_font = _load_gauge_font(max(8, int(outer_r * 0.13)), bold=True)
            sb = draw.textbbox((0, 0), self._subtext, font=sub_font)
            sw = sb[2] - sb[0]
            draw.text(
                (cx - sw / 2.0 - sb[0], pill_y + ph / 2.0 + 4 * scale - sb[1]),
                self._subtext,
                font=sub_font,
                fill=(*hex_to_rgb(p.fg_muted), 235),
            )

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((s_px, s_px), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))


# ── 3. ModernSegmentedGauge (LED Block Arc or Bar Meter) ─────────────────────


class ModernSegmentedGauge(_AnimatedGaugeBase):
    """Discrete LED-segment gauge supporting radial `'arc'` and horizontal `'bar'` modes."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 74.0,
        minimum: float = 0.0,
        maximum: float = 100.0,
        style: str = "arc",  # "arc" or "bar"
        segments: int = 18,
        size: int = 168,
        width: Optional[int] = None,
        height: Optional[int] = None,
        bootstyle: str = "primary",
        gradient_roles: Optional[Sequence[str]] = ("success", "warning", "danger"),
        textprefix: str = "",
        textsuffix: str = "%",
        subtext: str = "Load",
        decimals: int = 0,
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        **kwargs,
    ) -> None:
        self._mode = "bar" if (style or "").strip().lower() == "bar" else "arc"
        self._segments = max(4, min(40, int(segments)))
        self._gradient_roles = list(gradient_roles) if gradient_roles else []
        w_def = (260 if self._mode == "bar" else size) if width is None else int(width)
        h_def = (66 if self._mode == "bar" else size) if height is None else int(height)
        super().__init__(
            master,
            value=value,
            minimum=minimum,
            maximum=maximum,
            bootstyle=bootstyle,
            textprefix=textprefix,
            textsuffix=textsuffix,
            subtext=subtext,
            decimals=decimals,
            thresholds=thresholds,
            width=w_def,
            height=h_def,
            **kwargs,
        )
        self._redraw()

    def _segment_color(self, idx: int, total: int, p: ThemePalette) -> str:
        if not self._gradient_roles:
            return p.role_color(self._active_role())
        if len(self._gradient_roles) == 1:
            return p.role_color(self._gradient_roles[0])
        u = idx / float(max(1, total - 1))
        if len(self._gradient_roles) == 3:
            if u < 0.62:
                return p.role_color(self._gradient_roles[0])
            if u < 0.84:
                return p.role_color(self._gradient_roles[1])
            return p.role_color(self._gradient_roles[2])
        pos = min(len(self._gradient_roles) - 1, int(u * len(self._gradient_roles)))
        return p.role_color(self._gradient_roles[pos])

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(80, self.winfo_width(), int(self["width"]))
        h = max(48, self.winfo_height(), int(self["height"]))
        scale = 3
        W, H = w * scale, h * scale

        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        off_rgba = (*hex_to_rgb(p.surface_alt), 255)
        img = Image.new("RGBA", (W, H), bg_rgba)
        draw = ImageDraw.Draw(img)

        lit_count = int(round(self.ratio * self._segments))
        val_str = _format_gauge_value(self._value, self._prefix, self._suffix, self._decimals)

        if self._mode == "bar":
            pad_x = 8 * scale
            # Header row
            hdr_font = _load_gauge_font(10 * scale, bold=True)
            val_font = _load_gauge_font(11 * scale, bold=True)
            if self._subtext:
                draw.text((pad_x, 4 * scale), self._subtext, font=hdr_font, fill=(*hex_to_rgb(p.fg_muted), 255))
            vb = draw.textbbox((0, 0), val_str, font=val_font)
            vw = vb[2] - vb[0]
            draw.text((W - pad_x - vw - vb[0], 3 * scale), val_str, font=val_font, fill=(*hex_to_rgb(p.fg), 255))

            # LED bar segments
            gap = 4 * scale
            top_y = 26 * scale
            bot_y = max(top_y + 14 * scale, H - 10 * scale)
            avail_w = W - 2 * pad_x - gap * (self._segments - 1)
            seg_w = max(3 * scale, avail_w / float(self._segments))
            rad = min(4 * scale, seg_w / 2.0)

            for i in range(self._segments):
                sx0 = pad_x + i * (seg_w + gap)
                sx1 = sx0 + seg_w
                col = (*hex_to_rgb(self._segment_color(i, self._segments, p)), 255) if i < lit_count else off_rgba
                draw.rounded_rectangle([sx0, top_y, sx1, bot_y], radius=rad, fill=col)
        else:
            S = min(W, H)
            cx = W / 2.0
            cy = H / 2.0
            outer_r = S * 0.44
            inner_r = S * 0.32
            start_deg = 135.0
            sweep_deg = 270.0
            step_deg = sweep_deg / float(self._segments)
            gap_deg = min(4.2, step_deg * 0.28)

            for i in range(self._segments):
                a0 = math.radians(start_deg + i * step_deg + gap_deg / 2.0)
                a1 = math.radians(start_deg + (i + 1) * step_deg - gap_deg / 2.0)
                pts = [
                    (cx + inner_r * math.cos(a0), cy + inner_r * math.sin(a0)),
                    (cx + outer_r * math.cos(a0), cy + outer_r * math.sin(a0)),
                    (cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1)),
                    (cx + inner_r * math.cos(a1), cy + inner_r * math.sin(a1)),
                ]
                col = (*hex_to_rgb(self._segment_color(i, self._segments, p)), 255) if i < lit_count else off_rgba
                draw.polygon(pts, fill=col)

            val_font = _load_gauge_font(max(14, int(S * 0.14)), bold=True)
            vb = draw.textbbox((0, 0), val_str, font=val_font)
            vw, vh = vb[2] - vb[0], vb[3] - vb[1]
            y_off = -7 * scale if self._subtext else 0
            draw.text(
                (cx - vw / 2.0 - vb[0], cy + y_off - vh / 2.0 - vb[1]),
                val_str,
                font=val_font,
                fill=(*hex_to_rgb(p.fg), 255),
            )
            if self._subtext:
                sub_font = _load_gauge_font(max(9, int(S * 0.068)), bold=True)
                sb = draw.textbbox((0, 0), self._subtext, font=sub_font)
                sw = sb[2] - sb[0]
                draw.text(
                    (cx - sw / 2.0 - sb[0], cy + vh / 2.0 + 2 * scale - sb[1]),
                    self._subtext,
                    font=sub_font,
                    fill=(*hex_to_rgb(p.fg_muted), 235),
                )

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((w, h), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))


# ── 4. ModernLinearGauge (Executive Bullet & Scale Gauge) ────────────────────


class ModernLinearGauge(_AnimatedGaugeBase):
    """Horizontal executive bullet & scale gauge with range bands, benchmark target marker, and tick labels."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 78.0,
        minimum: float = 0.0,
        maximum: float = 100.0,
        target: Optional[float] = 85.0,
        ranges: Optional[Sequence[float]] = (0.55, 0.82, 1.0),
        title: str = "Service Level",
        bootstyle: str = "primary",
        textprefix: str = "",
        textsuffix: str = "%",
        decimals: int = 0,
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        ticks: int = 5,
        width: int = 320,
        height: int = 74,
        **kwargs,
    ) -> None:
        self._target_marker = target
        self._ranges = list(ranges) if ranges else []
        self._ticks = max(2, int(ticks))
        super().__init__(
            master,
            value=value,
            minimum=minimum,
            maximum=maximum,
            bootstyle=bootstyle,
            textprefix=textprefix,
            textsuffix=textsuffix,
            subtext=title,
            decimals=decimals,
            thresholds=thresholds,
            width=width,
            height=height,
            **kwargs,
        )
        self._redraw()

    def set_target(self, target: Optional[float]) -> None:
        self._target_marker = target
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(160, self.winfo_width(), int(self["width"]))
        h = max(62, self.winfo_height(), int(self["height"]))
        scale = 3
        W, H = w * scale, h * scale

        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        img = Image.new("RGBA", (W, H), bg_rgba)
        draw = ImageDraw.Draw(img)

        pad_x = 12 * scale
        bar_x0 = pad_x
        bar_x1 = W - pad_x
        bar_w = max(20 * scale, bar_x1 - bar_x0)

        # Top header: title on left, formatted value on right
        title_font = _load_gauge_font(10 * scale, bold=True)
        val_font = _load_gauge_font(11 * scale, bold=True)
        if self._subtext:
            draw.text((bar_x0, 4 * scale), self._subtext, font=title_font, fill=(*hex_to_rgb(p.fg), 255))
        val_str = _format_gauge_value(self._value, self._prefix, self._suffix, self._decimals)
        vb = draw.textbbox((0, 0), val_str, font=val_font)
        vw = vb[2] - vb[0]
        accent_hex = p.role_color(self._active_role())
        draw.text((bar_x1 - vw - vb[0], 3 * scale), val_str, font=val_font, fill=(*hex_to_rgb(accent_hex), 255))

        # Qualitative background range bands (bullet chart style)
        track_y0 = 24 * scale
        track_h = 18 * scale
        track_y1 = track_y0 + track_h
        r_track = 5 * scale

        draw.rounded_rectangle(
            [bar_x0, track_y0, bar_x1, track_y1],
            radius=r_track,
            fill=(*hex_to_rgb(p.surface_alt), 255),
        )

        if self._ranges:
            dark = p.mode == "dark"
            band_shades = (
                (blend_colors(p.surface_alt, p.border_strong, 0.45),
                 blend_colors(p.surface_alt, p.border_strong, 0.25),
                 p.surface_alt)
                if dark
                else (blend_colors(p.surface_alt, p.border_strong, 0.35),
                      blend_colors(p.surface_alt, p.border_strong, 0.16),
                      p.surface_alt)
            )
            sorted_r = sorted(self._ranges, reverse=True)
            for idx, r_end in enumerate(sorted_r):
                u = (r_end - self._min) / (self._max - self._min) if r_end > 1.01 else float(r_end)
                u = max(0.0, min(1.0, u))
                bx = bar_x0 + bar_w * u
                shade = band_shades[min(len(band_shades) - 1, len(sorted_r) - 1 - idx)]
                if bx > bar_x0 + 2 * scale:
                    draw.rounded_rectangle(
                        [bar_x0, track_y0, bx, track_y1],
                        radius=r_track,
                        fill=(*hex_to_rgb(shade), 255),
                    )

        # Primary measure bar centered inside the range band
        meas_pad = 4 * scale
        meas_w = bar_w * self.ratio
        if meas_w > 2 * scale:
            draw.rounded_rectangle(
                [bar_x0, track_y0 + meas_pad, bar_x0 + meas_w, track_y1 - meas_pad],
                radius=3 * scale,
                fill=(*hex_to_rgb(accent_hex), 255),
            )

        # Benchmark target marker line
        if self._target_marker is not None:
            tu = max(0.0, min(1.0, (self._target_marker - self._min) / (self._max - self._min)))
            tx = bar_x0 + bar_w * tu
            draw.rounded_rectangle(
                [tx - 1.6 * scale, track_y0 - 3 * scale, tx + 1.6 * scale, track_y1 + 3 * scale],
                radius=max(1, int(1.4 * scale)),
                fill=(*hex_to_rgb(p.fg), 245),
            )

        # Tick marks and scale labels
        tick_font = _load_gauge_font(8 * scale, bold=False)
        tick_col = (*hex_to_rgb(p.fg_muted), 210)
        for i in range(self._ticks):
            u = i / float(max(1, self._ticks - 1))
            tx = bar_x0 + bar_w * u
            draw.line([(tx, track_y1 + 3 * scale), (tx, track_y1 + 7 * scale)], fill=tick_col, width=max(1, scale))
            lbl = f"{int(round(self._min + u * (self._max - self._min)))}"
            lb = draw.textbbox((0, 0), lbl, font=tick_font)
            lw = lb[2] - lb[0]
            lx = max(bar_x0, min(bar_x1 - lw, tx - lw / 2.0)) - lb[0]
            draw.text((lx, track_y1 + 9 * scale - lb[1]), lbl, font=tick_font, fill=tick_col)

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((w, h), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))


# ── 5. ModernLiquidGauge (Animated Wave-Fill Circular Tank Gauge) ────────────


class ModernLiquidGauge(_AnimatedGaugeBase):
    """Circular glass-orb tank gauge with continuous 30 FPS dual-sine-wave liquid fill."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 62.0,
        minimum: float = 0.0,
        maximum: float = 100.0,
        size: int = 160,
        bootstyle: str = "info",
        textprefix: str = "",
        textsuffix: str = "%",
        subtext: str = "Storage",
        decimals: int = 0,
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        animate_wave: bool = True,
        wave_interval_ms: int = 40,
        **kwargs,
    ) -> None:
        self._size = max(96, int(size))
        self._wave_phase = 0.0
        self._animate_wave = bool(animate_wave)
        self._wave_interval_ms = max(20, int(wave_interval_ms))
        self._wave_job: Optional[str] = None
        super().__init__(
            master,
            value=value,
            minimum=minimum,
            maximum=maximum,
            bootstyle=bootstyle,
            textprefix=textprefix,
            textsuffix=textsuffix,
            subtext=subtext,
            decimals=decimals,
            thresholds=thresholds,
            width=self._size,
            height=self._size,
            **kwargs,
        )
        self.bind("<Destroy>", self._on_destroy_wave, add="+")
        self._redraw()
        if self._animate_wave:
            self.start_wave()

    def _on_destroy_wave(self, e: tk.Event) -> None:
        if e.widget is self:
            self.stop_wave()

    def start_wave(self) -> None:
        self.stop_wave()
        self._animate_wave = True
        self._tick_wave()

    def stop_wave(self) -> None:
        self._animate_wave = False
        if self._wave_job is not None:
            try:
                self.after_cancel(self._wave_job)
            except tk.TclError:
                pass
            self._wave_job = None

    def _tick_wave(self) -> None:
        self._wave_job = None
        if not self._animate_wave or not self.winfo_exists():
            return
        self._wave_phase = (self._wave_phase + 0.14) % (2.0 * math.pi)
        if self.winfo_ismapped():
            self._redraw()
        try:
            self._wave_job = self.after(self._wave_interval_ms, self._tick_wave)
        except tk.TclError:
            self._wave_job = None

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(self._size, self.winfo_width())
        h = max(self._size, self.winfo_height())
        s_px = min(w, h)
        scale = 2
        S = s_px * scale
        cx = S / 2.0
        cy = S / 2.0

        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        img = Image.new("RGBA", (S, S), bg_rgba)

        outer_r = S * 0.45
        inner_r = outer_r - 5.5 * scale
        accent_hex = p.role_color(self._active_role())
        back_wave_hex = blend_colors(accent_hex, p.surface_alt, 0.42)

        # Render liquid waves onto an internal RGBA layer and clip to inner circle
        liquid = Image.new("RGBA", (S, S), (*hex_to_rgb(p.surface_alt), 255))
        ldraw = ImageDraw.Draw(liquid)

        r_val = self.ratio
        # Water level Y inside the inner circle
        y_top = cy - inner_r
        y_bot = cy + inner_r
        level_y = y_bot - (y_bot - y_top) * r_val
        amp = (4.5 * scale) * math.sin(math.pi * max(0.05, min(0.95, r_val)))

        x_start = int(cx - inner_r - 2)
        x_end = int(cx + inner_r + 2)
        step = max(2, scale * 2)

        # Back wave (offset phase, softer tint)
        pts_back: List[Tuple[float, float]] = [(x_start, S)]
        for x in range(x_start, x_end + step, step):
            u = (x - x_start) / float(max(1, x_end - x_start))
            wy = level_y + amp * 0.85 * math.sin(u * 2.0 * math.pi * 1.4 - self._wave_phase * 0.85 + 1.3)
            pts_back.append((x, wy))
        pts_back.append((x_end, S))
        ldraw.polygon(pts_back, fill=(*hex_to_rgb(back_wave_hex), 220))

        # Front wave (primary accent)
        pts_front: List[Tuple[float, float]] = [(x_start, S)]
        for x in range(x_start, x_end + step, step):
            u = (x - x_start) / float(max(1, x_end - x_start))
            wy = level_y + amp * math.sin(u * 2.0 * math.pi * 1.6 + self._wave_phase)
            pts_front.append((x, wy))
        pts_front.append((x_end, S))
        ldraw.polygon(pts_front, fill=(*hex_to_rgb(accent_hex), 245))

        # Circular mask for inner tank
        mask = Image.new("L", (S, S), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=255)
        img.paste(liquid, (0, 0), mask)

        draw = ImageDraw.Draw(img)
        # Outer glowing bezel ring
        draw.ellipse(
            [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
            outline=(*hex_to_rgb(accent_hex), 230),
            width=max(2, int(2.6 * scale)),
        )
        # Subtle glass top-left specular highlight arc
        hi_r = inner_r - 4 * scale
        draw.arc(
            [cx - hi_r, cy - hi_r, cx + hi_r, cy + hi_r],
            start=205,
            end=260,
            fill=(255, 255, 255, 110 if p.mode == "dark" else 160),
            width=max(2, int(2.2 * scale)),
        )

        # Contrast-aware text color depending on whether liquid covers the center
        val_color_hex = contrast_text_color(accent_hex) if r_val >= 0.54 else p.fg
        sub_color_hex = contrast_text_color(accent_hex) if r_val >= 0.36 else p.fg_muted

        val_str = _format_gauge_value(self._value, self._prefix, self._suffix, self._decimals)
        val_font = _load_gauge_font(max(14, int(S * 0.165)), bold=True)
        vb = draw.textbbox((0, 0), val_str, font=val_font)
        vw, vh = vb[2] - vb[0], vb[3] - vb[1]
        y_off = -7 * scale if self._subtext else 0
        draw.text(
            (cx - vw / 2.0 - vb[0], cy + y_off - vh / 2.0 - vb[1]),
            val_str,
            font=val_font,
            fill=(*hex_to_rgb(val_color_hex), 255),
        )
        if self._subtext:
            sub_font = _load_gauge_font(max(9, int(S * 0.072)), bold=True)
            sb = draw.textbbox((0, 0), self._subtext, font=sub_font)
            sw = sb[2] - sb[0]
            draw.text(
                (cx - sw / 2.0 - sb[0], cy + vh / 2.0 + 1 * scale - sb[1]),
                self._subtext,
                font=sub_font,
                fill=(*hex_to_rgb(sub_color_hex), 235),
            )

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((s_px, s_px), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))


# ── 6. ModernMultiRingGauge (Concentric Activity Rings Gauge) ────────────────


class ModernMultiRingGauge(tk.Canvas, ThemedWidgetMixin):
    """Concentric multi-metric activity rings gauge with smooth animated sweeps and optional legend.

    `rings` is a sequence of dicts or tuples:
    `{"label": "CPU", "value": 72, "maximum": 100, "bootstyle": "primary"}`
    (or `(label, value, bootstyle)`).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        rings: Optional[Sequence[Any]] = None,
        size: int = 172,
        ring_width: int = 11,
        ring_gap: int = 5,
        show_legend: bool = True,
        show_center_avg: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ) -> None:
        default_rings = [
            {"label": "Availability", "value": 92.0, "maximum": 100.0, "bootstyle": "primary"},
            {"label": "Performance", "value": 81.0, "maximum": 100.0, "bootstyle": "success"},
            {"label": "Quality", "value": 96.0, "maximum": 100.0, "bootstyle": "info"},
        ]
        raw = rings if rings is not None else default_rings
        self._rings: List[Dict[str, Any]] = [self._normalize_ring(r) for r in raw[:4]]
        self._size = max(110, int(size))
        self._ring_width = max(5, int(ring_width))
        self._ring_gap = max(2, int(ring_gap))
        self._show_legend = bool(show_legend)
        self._show_center_avg = bool(show_center_avg)
        self._anim_job: Optional[str] = None
        self._photo: Optional[ImageTk.PhotoImage] = None

        w_def = (self._size + 132 if self._show_legend else self._size) if width is None else int(width)
        h_def = self._size if height is None else int(height)

        super().__init__(
            master,
            width=w_def,
            height=h_def,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()
        self.bind("<Configure>", lambda _e: self._redraw())
        self.bind("<Destroy>", self._on_destroy_anim, add="+")
        self._redraw()

    @staticmethod
    def _normalize_ring(item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            val = float(item.get("value", 0.0))
            mx = max(1.0, float(item.get("maximum", 100.0)))
            clamped = max(0.0, min(mx, val))
            return {
                "label": str(item.get("label", "Metric")),
                "value": clamped,
                "target": clamped,
                "maximum": mx,
                "role": str(item.get("bootstyle", "primary")).split("-")[0],
            }
        label = str(item[0])
        val = float(item[1])
        role = str(item[2]).split("-")[0] if len(item) > 2 else "primary"
        mx = max(1.0, float(item[3])) if len(item) > 3 else 100.0
        clamped = max(0.0, min(mx, val))
        return {"label": label, "value": clamped, "target": clamped, "maximum": mx, "role": role}

    def _on_destroy_anim(self, e: tk.Event) -> None:
        if e.widget is self and self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

    def get_values(self) -> List[float]:
        return [r["target"] for r in self._rings]

    def set_ring(self, index_or_label: int | str, value: float, *, animate: bool = True) -> None:
        """Update a single ring by 0-based index or label name."""
        target_ring = None
        if isinstance(index_or_label, int):
            if 0 <= index_or_label < len(self._rings):
                target_ring = self._rings[index_or_label]
        else:
            for r in self._rings:
                if r["label"].lower() == index_or_label.lower():
                    target_ring = r
                    break
        if target_ring is None:
            return
        target_ring["target"] = max(0.0, min(target_ring["maximum"], float(value)))
        if not animate:
            target_ring["value"] = target_ring["target"]
            self._redraw()
        else:
            self._step_animation()

    def set_values(self, values: Sequence[float], *, animate: bool = True) -> None:
        """Update all rings from a sequence of values."""
        for r, v in zip(self._rings, values):
            r["target"] = max(0.0, min(r["maximum"], float(v)))
            if not animate:
                r["value"] = r["target"]
        if animate:
            self._step_animation()
        else:
            self._redraw()

    def _step_animation(self) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        if not self.winfo_exists():
            return
        still_moving = False
        for r in self._rings:
            diff = r["target"] - r["value"]
            if abs(diff) <= 0.35:
                r["value"] = r["target"]
            else:
                r["value"] += diff * 0.25
                still_moving = True
        self._redraw()
        if still_moving:
            try:
                self._anim_job = self.after(16, self._step_animation)
            except tk.TclError:
                self._anim_job = None

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        if not self.winfo_exists():
            return
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)

        w = max(110, self.winfo_width(), int(self["width"]))
        h = max(110, self.winfo_height(), int(self["height"]))
        scale = 3
        W, H = w * scale, h * scale

        bg_rgba = (*hex_to_rgb(parent_bg), 255)
        track_rgba = (*hex_to_rgb(p.surface_alt), 255)
        img = Image.new("RGBA", (W, H), bg_rgba)
        draw = ImageDraw.Draw(img)

        dial_s = min(H, W - (126 * scale if self._show_legend else 0))
        dial_s = max(90 * scale, dial_s)
        cx = (dial_s / 2.0) + (6 * scale if self._show_legend else (W - dial_s) / 2.0)
        cy = H / 2.0

        rw = self._ring_width * scale
        rg = self._ring_gap * scale
        outer_r = dial_s * 0.45

        def _cap(rad_mid: float, deg: float, cap_r: float, col: Tuple[int, int, int, int]) -> None:
            rad = math.radians(deg)
            x = cx + rad_mid * math.cos(rad)
            y = cy + rad_mid * math.sin(rad)
            draw.ellipse([x - cap_r, y - cap_r, x + cap_r, y + cap_r], fill=col)

        ratios: List[float] = []
        for idx, ring in enumerate(self._rings):
            r_out = outer_r - idx * (rw + rg)
            if r_out <= rw + 6 * scale:
                break
            bbox = [cx - r_out, cy - r_out, cx + r_out, cy + r_out]
            draw.arc(bbox, start=0, end=360, fill=track_rgba, width=rw)

            ratio = max(0.0, min(1.0, ring["value"] / ring["maximum"]))
            ratios.append(ratio)
            if ratio > 0.004:
                col = (*hex_to_rgb(p.role_color(ring["role"])), 255)
                start_deg = 270.0
                end_deg = start_deg + 359.5 * ratio
                draw.arc(bbox, start=start_deg, end=end_deg, fill=col, width=rw)
                mid_r = r_out - rw / 2.0
                _cap(mid_r, start_deg, rw / 2.0, col)
                _cap(mid_r, end_deg, rw / 2.0, col)

        if self._show_center_avg and ratios:
            avg_pct = int(round((sum(ratios) / len(ratios)) * 100.0))
            avg_str = f"{avg_pct}%"
            c_font = _load_gauge_font(max(11, int(dial_s * 0.105)), bold=True)
            cb = draw.textbbox((0, 0), avg_str, font=c_font)
            cw, ch = cb[2] - cb[0], cb[3] - cb[1]
            draw.text(
                (cx - cw / 2.0 - cb[0], cy - ch / 2.0 - cb[1]),
                avg_str,
                font=c_font,
                fill=(*hex_to_rgb(p.fg), 255),
            )

        if self._show_legend and self._rings:
            leg_x = cx + outer_r + 16 * scale
            row_h = 28 * scale
            total_leg_h = len(self._rings) * row_h
            start_y = cy - total_leg_h / 2.0 + 4 * scale
            lbl_font = _load_gauge_font(9 * scale, bold=False)
            val_font = _load_gauge_font(10 * scale, bold=True)
            for idx, ring in enumerate(self._rings):
                ry = start_y + idx * row_h
                dot_r = 4.2 * scale
                col = (*hex_to_rgb(p.role_color(ring["role"])), 255)
                draw.ellipse([leg_x, ry + 3 * scale, leg_x + dot_r * 2, ry + 3 * scale + dot_r * 2], fill=col)
                pct_val = int(round((ring["value"] / ring["maximum"]) * 100.0))
                draw.text(
                    (leg_x + dot_r * 2 + 7 * scale, ry - 1 * scale),
                    ring["label"],
                    font=lbl_font,
                    fill=(*hex_to_rgb(p.fg_muted), 255),
                )
                draw.text(
                    (leg_x + dot_r * 2 + 7 * scale, ry + 11 * scale),
                    f"{pct_val}%",
                    font=val_font,
                    fill=(*hex_to_rgb(p.fg), 255),
                )

        resample = getattr(Image, "Resampling", Image).LANCZOS
        out = img.resize((w, h), resample=resample)
        self._photo = ImageTk.PhotoImage(out, master=self.winfo_toplevel())
        existing = self.find_withtag("gauge_img")
        if existing:
            self.coords(existing[0], w // 2, h // 2)
            self.itemconfigure(existing[0], image=self._photo)
        else:
            self.create_image(w // 2, h // 2, image=self._photo, anchor="center", tags=("gauge_img",))

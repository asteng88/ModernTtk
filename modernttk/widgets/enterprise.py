"""Enterprise & Analytics components inspired by the Capacity (RCCP) project:

- ModernMetricCard (KPI tile with title, big value, delta badge, and accent indicator)
- ModernProgressDialog (Modal progress dialog with live status message, percentage, and Windows close-button lock)
- ModernSplash (Glassmorphic rounded startup splash screen with radial glow, vector dial, and smooth progress)
- ModernStatusBar (Bottom application bar with status text, selection Sum/Average stats, and custom right slot)
- ModernScrollableFrame (Scrollable viewport container with mousewheel support and auto-hiding ModernScrollbar)
- ModernPanedWindow (Modern split-view sash container)
- style_matplotlib_figure / style_matplotlib_toolbar / style_tksheet (Live theme adapters for Matplotlib & tksheet)
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from typing import Any, Callable, Optional, Sequence

from PIL import Image, ImageDraw, ImageTk

from ..style import ThemeManager
from ..themes import ThemePalette
from ..utils import blend_colors, create_rounded_rect_image, hex_to_rgb
from .base import ModernFrame, ModernLabel, ThemedWidgetMixin
from .datastream import ModernDataStream
from .feedback import ModernProgressBar
from .table import ModernScrollbar
from .timer import ModernActivityTimer


class ModernMetricCard(tk.Canvas, ThemedWidgetMixin):
    """Elevated KPI metric card displaying a title, large metric value, optional delta/subtitle, and semantic accent bar.

    Inspired by the Capacity vs. Load KPI summary tiles in `StaffingOptimizerTab`.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Metric",
        value: str = "0.00",
        delta: Optional[str] = None,
        icon: Optional[str] = None,
        bootstyle: str = "primary",
        surface_role: str = "surface",
        width: int = 210,
        height: int = 92,
        **kwargs,
    ) -> None:
        self._title = title
        self._value = value
        self._delta = delta
        self._icon = icon
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._surface_role = surface_role

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            relief="flat",
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font_title = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1), weight="bold")
        self._font_val = tkfont.Font(family=p.font_family, size=p.font_size + 6, weight="bold")
        self._font_delta = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")

        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def set_metric(
        self,
        value: Optional[str] = None,
        delta: Optional[str] = None,
        bootstyle: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        """Update the KPI metric value, delta badge, or semantic color role dynamically."""
        if value is not None:
            self._value = value
        if delta is not None:
            self._delta = delta
        if bootstyle is not None:
            self._role = bootstyle.split("-")[0]
        if title is not None:
            self._title = title
        self._redraw()

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        surf = getattr(p, self._surface_role, p.surface)
        accent = p.role_color(self._role)

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            p.radius_lg,
            fill_hex=surf,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw")

        # Left vertical accent pill bar
        pill_h = max(24, h - 28)
        self._bar_img = create_rounded_rect_image(
            4,
            pill_h,
            2,
            fill_hex=accent,
            bg_hex=surf,
        )
        self.create_image(12, (h - pill_h) // 2, image=self._bar_img, anchor="nw")

        # Title
        self.create_text(
            26,
            24,
            text=self._title.upper(),
            fill=p.fg_muted,
            font=self._font_title,
            anchor="w",
        )

        # Optional top-right icon
        if self._icon:
            self.create_text(
                w - 16,
                24,
                text=self._icon,
                fill=accent,
                font=self._font_title,
                anchor="e",
            )

        # Large value
        self.create_text(
            26,
            54,
            text=self._value,
            fill=p.fg,
            font=self._font_val,
            anchor="w",
        )

        # Optional delta pill on bottom right
        if self._delta:
            dw = self._font_delta.measure(self._delta) + 14
            dh = 20
            dx = w - dw - 14
            dy = h - dh - 14
            self._delta_img = create_rounded_rect_image(
                dw,
                dh,
                dh // 2,
                fill_hex=p.role_subtle_bg(self._role),
                bg_hex=surf,
            )
            self.create_image(dx, dy, image=self._delta_img, anchor="nw")
            self.create_text(
                dx + dw // 2,
                dy + dh // 2,
                text=self._delta,
                fill=accent,
                font=self._font_delta,
            )


class ModernScrollableFrame(ModernFrame):
    """Scrollable viewport container with mousewheel support and auto-hiding `ModernScrollbar`.

    Inspired by `setup_responsive_dialog_layout` in Capacity's `app/ui_layout.py`.
    Place child widgets inside `scroll_frame.body`.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        surface_role: str = "surface",
        padding: int = 8,
        **kwargs,
    ) -> None:
        self._body_role = surface_role
        super().__init__(master, surface_role=surface_role, **kwargs)

        p = self.palette
        bg_col = getattr(p, surface_role, p.surface)

        self._canvas = tk.Canvas(self, bg=bg_col, bd=0, highlightthickness=0)
        self._scrollbar = ModernScrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self.body = ModernFrame(self._canvas, surface_role=surface_role, padx=padding, pady=padding)
        self._win_id = self._canvas.create_window((0, 0), window=self.body, anchor="nw")

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y", padx=(4, 0))

        self.body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_wheel)
        self._canvas.bind("<Leave>", self._unbind_wheel)

    def _on_body_configure(self, _e: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e: tk.Event) -> None:
        self._canvas.itemconfigure(self._win_id, width=e.width)

    def _bind_wheel(self, _e: tk.Event) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_wheel(self, _e: tk.Event) -> None:
        try:
            self.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    def _on_mousewheel(self, e: tk.Event) -> None:
        if not self._canvas.winfo_exists():
            return
        bbox = self._canvas.bbox("all")
        if bbox and (bbox[3] - bbox[1] > self._canvas.winfo_height()):
            self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_theme_changed(self, palette: ThemePalette) -> None:
        super()._on_theme_changed(palette)
        bg_col = getattr(palette, self._body_role, palette.surface)
        self._canvas.configure(bg=bg_col)


class ModernStatusBar(ModernFrame):
    """Bottom application status bar with status label, selection Sum/Average statistics, and custom right slot.

    Directly inspired by `create_status_frame` and `update_selection_stats` in `capacity.py`.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        status_text: str = "Status: Ready",
        show_stats: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(master, surface_role="surface_alt", padx=14, pady=5, **kwargs)

        self._status_lbl = ModernLabel(
            self,
            text=status_text,
            surface_role="surface_alt",
            font_size_delta=-1,
        )
        self._status_lbl.pack(side="left")

        self.right_frame = ModernFrame(self, surface_role="surface_alt")
        self.right_frame.pack(side="right")

        self._sum_lbl: Optional[ModernLabel] = None
        self._avg_lbl: Optional[ModernLabel] = None
        self._count_lbl: Optional[ModernLabel] = None

        if show_stats:
            self._count_lbl = ModernLabel(
                self.right_frame,
                text="Selected: 0",
                surface_role="surface_alt",
                muted=True,
                font_size_delta=-1,
            )
            self._count_lbl.pack(side="left", padx=(0, 14))

            self._sum_lbl = ModernLabel(
                self.right_frame,
                text="Sum: --",
                surface_role="surface_alt",
                muted=True,
                font_size_delta=-1,
            )
            self._sum_lbl.pack(side="left", padx=(0, 14))

            self._avg_lbl = ModernLabel(
                self.right_frame,
                text="Average: --",
                surface_role="surface_alt",
                muted=True,
                font_size_delta=-1,
            )
            self._avg_lbl.pack(side="left")

    def set_status(self, text: str) -> None:
        self._status_lbl.configure(text=text)

    def update_stats(self, values: Sequence[float | int | str]) -> None:
        """Calculate and display Count, Sum, and Average for a list of numeric cell values."""
        nums: list[float] = []
        for v in values:
            try:
                clean = str(v).split()[0].replace(",", "").replace("%", "")
                nums.append(float(clean))
            except (ValueError, TypeError, IndexError):
                continue

        if self._count_lbl:
            self._count_lbl.configure(text=f"Selected: {len(values)}")
        if nums:
            total = sum(nums)
            avg = total / len(nums)
            if self._sum_lbl:
                self._sum_lbl.configure(text=f"Sum: {total:,.2f}")
            if self._avg_lbl:
                self._avg_lbl.configure(text=f"Average: {avg:,.2f}")
        else:
            if self._sum_lbl:
                self._sum_lbl.configure(text="Sum: --")
            if self._avg_lbl:
                self._avg_lbl.configure(text="Average: --")


class ModernProgressDialog:
    """Modal progress dialog with live status text, animated chronograph timer or data stream, percentage bar, and close lock.

    Directly inspired by `ProgressDialog` in Capacity's `app/data_source_tab.py`.
    Supports `animation="timer"` (default), `animation="data_stream"` (Database <-> Computer
    streaming animation), `animation="auto"` (starts with chronograph timer and smoothly
    transitions to `ModernDataStream` if processing exceeds `long_running_threshold_sec`),
    or `animation="none"`.
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str = "Processing",
        message: str = "Please wait...",
        bootstyle: str = "primary",
        show_timer: bool = True,
        animation: Optional[str] = None,
        stream_direction: str = "db_to_pc",
        source_label: str = "Database",
        target_label: str = "Computer",
        long_running_threshold_sec: float = 3.0,
    ) -> None:
        self._destroyed = False
        self._bootstyle = bootstyle
        self._stream_direction = stream_direction
        self._source_label = source_label
        self._target_label = target_label
        self._switch_job: Optional[str] = None
        p = ThemeManager.instance().palette

        if animation is None:
            anim_mode = "timer" if show_timer else "none"
        else:
            anim_mode = animation.strip().lower()
        self._anim_mode = anim_mode

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent.winfo_toplevel())
        self.dialog.grab_set()
        self.dialog.configure(bg=p.surface)
        self.dialog.resizable(False, False)
        ThemeManager._apply_windows_titlebar_mode(self.dialog, p.mode == "dark")

        w = 460
        if anim_mode == "data_stream":
            h = 300
        elif anim_mode in ("timer", "auto"):
            h = 335
        else:
            h = 150
        root = parent.winfo_toplevel()
        root.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        self.dialog.geometry(f"{w}x{h}+{max(20, x)}+{max(20, y)}")

        container = ModernFrame(self.dialog, surface_role="surface", padx=24, pady=20)
        container.pack(fill="both", expand=True)

        self._anim_host = ModernFrame(container, surface_role="surface")
        if anim_mode != "none":
            self._anim_host.pack(anchor="center", pady=(0, 10))

        self.timer: Optional[ModernActivityTimer] = None
        self.data_stream: Optional[ModernDataStream] = None

        if anim_mode == "data_stream":
            self.data_stream = ModernDataStream(
                self._anim_host,
                direction=stream_direction,
                bootstyle=bootstyle,
                source_label=source_label,
                target_label=target_label,
                pct=0.0,
                autostart=True,
            )
            self.data_stream.pack(anchor="center")
        elif anim_mode in ("timer", "auto"):
            self.timer = ModernActivityTimer(
                self._anim_host,
                bootstyle=bootstyle,
                autostart=True,
            )
            self.timer.pack(anchor="center")
            if anim_mode == "auto":
                delay_ms = max(200, int(round(max(0.0, float(long_running_threshold_sec)) * 1000.0)))
                self._switch_job = self.dialog.after(delay_ms, self._switch_to_data_stream)

        self._msg_lbl = ModernLabel(
            container,
            text=message,
            surface_role="surface",
            bold=True,
            anchor="w",
        )
        self._msg_lbl.pack(fill="x", pady=(0, 14))

        self._progress = ModernProgressBar(
            container,
            value=0,
            bootstyle=bootstyle,
            show_percent=True,
            width=w - 48,
            height=20,
        )
        self._progress.pack(fill="x")

        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        self.dialog.update()

    def _switch_to_data_stream(self) -> None:
        self._switch_job = None
        if self._destroyed or not self.dialog.winfo_exists() or self.data_stream is not None:
            return
        cur_pct = self._progress.get()
        start_t = self.timer._start_t if self.timer is not None else None
        if self.timer is not None:
            self.timer.stop()
            self.timer.destroy()
            self.timer = None
        self.data_stream = ModernDataStream(
            self._anim_host,
            direction=self._stream_direction,
            bootstyle=self._bootstyle,
            source_label=self._source_label,
            target_label=self._target_label,
            pct=cur_pct,
            autostart=True,
        )
        if start_t is not None:
            self.data_stream._start_t = start_t
        self.data_stream.pack(anchor="center")
        self.dialog.update_idletasks()

    def set_stream_direction(self, direction: str, status_text: Optional[str] = None) -> None:
        """Update the Database <-> Computer streaming direction (e.g. `'db_to_pc'`, `'pc_to_db'`, `'bidirectional'`)."""
        self._stream_direction = direction
        if self.data_stream is not None:
            self.data_stream.set_direction(direction, status_text=status_text)

    def update(self, value: float, message: Optional[str] = None) -> None:
        if self._destroyed or not self.dialog.winfo_exists():
            return
        self._progress.set(value)
        if self.timer is not None:
            self.timer.set_progress(value)
        if self.data_stream is not None:
            self.data_stream.set_progress(value)
        if message is not None:
            self._msg_lbl.configure(text=message)
        self.dialog.update_idletasks()

    def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        if self._switch_job is not None:
            try:
                self.dialog.after_cancel(self._switch_job)
            except tk.TclError:
                pass
            self._switch_job = None
        if self.timer is not None:
            self.timer.stop()
        if self.data_stream is not None:
            self.data_stream.stop()
        try:
            self.dialog.grab_release()
        except tk.TclError:
            pass
        if self.dialog.winfo_exists():
            self.dialog.destroy()


class ModernSplash:
    """Glassmorphic anti-aliased rounded splash screen with ambient glow, vector dial icon, and 60fps progress bar.

    Directly inspired by `SplashScreen` in Capacity's `app/splash.py`.
    """

    def __init__(
        self,
        root: tk.Misc,
        title: str = "ModernTtk Application",
        subtitle: str = "Initializing workspace & theme engine...",
        version: str = "v1.0.0",
        footer: str = "",
        bootstyle: str = "primary",
    ) -> None:
        self.root = root
        self._card_w = 440
        self._card_h = 400
        self._finished = False

        p = ThemeManager.instance().palette
        accent = p.role_color(bootstyle.split("-")[0])

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self._transparent_key = "#000001"
        try:
            self.top.configure(bg=self._transparent_key)
            self.top.attributes("-transparentcolor", self._transparent_key)
        except tk.TclError:
            self._transparent_key = "black"
            self.top.configure(bg=self._transparent_key)

        self.top.attributes("-topmost", True)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - self._card_w) // 2
        y = (sh - self._card_h) // 2
        self.top.geometry(f"{self._card_w}x{self._card_h}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.top,
            width=self._card_w,
            height=self._card_h,
            highlightthickness=0,
            bd=0,
            bg=self._transparent_key,
        )
        self.canvas.pack(fill="both", expand=True)

        self._bg_photo = self._render_card(accent)
        self.canvas.create_image(self._card_w // 2, self._card_h // 2, image=self._bg_photo)

        self.canvas.create_text(
            self._card_w // 2,
            200,
            text=title,
            fill="#FFFFFF",
            font=(p.font_family, 18, "bold"),
        )
        self.canvas.create_text(
            self._card_w // 2,
            230,
            text=subtitle,
            fill="#94A3B8",
            font=(p.font_family, 9),
        )

        self._x1 = 55
        self._x2 = self._card_w - 55
        self._y_bar = 285

        self.canvas.create_line(
            self._x1, self._y_bar, self._x2, self._y_bar,
            width=7, fill="#1E293B", capstyle="round",
        )
        self._fill_line = self.canvas.create_line(
            self._x1, self._y_bar, self._x1 + 1, self._y_bar,
            width=7, fill=accent, capstyle="round",
        )

        self._status_id = self.canvas.create_text(
            self._x1, 312,
            text="Starting...",
            fill=accent,
            font=(p.font_family, 9, "bold"),
            anchor="w",
        )
        self._pct_id = self.canvas.create_text(
            self._x2, 312,
            text="0%",
            fill="#E2E8F0",
            font=(p.font_family, 9, "bold"),
            anchor="e",
        )
        self.canvas.create_text(
            self._card_w // 2, 348,
            text=version,
            fill=accent,
            font=(p.font_family, 8, "bold"),
        )
        if footer:
            self.canvas.create_text(
                self._card_w // 2, 374,
                text=footer,
                fill="#64748B",
                font=(p.font_family, 8),
            )
        self.top.update()

    def _render_card(self, accent_hex: str) -> ImageTk.PhotoImage:
        img = Image.new("RGBA", (self._card_w, self._card_h), (0, 0, 1, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [2, 2, self._card_w - 3, self._card_h - 3],
            radius=24,
            fill=(15, 23, 42, 255),
            outline=(51, 65, 85, 255),
            width=1,
        )
        cx, cy = self._card_w // 2, 105
        ar, ag, ab = hex_to_rgb(accent_hex)
        for r in range(65, 10, -5):
            alpha = int(28 * (1 - r / 65))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(ar, ag, ab, alpha))

        # Vector gauge dial icon
        box = [cx - 40, cy - 40, cx + 40, cy + 40]
        draw.ellipse(box, fill=(30, 41, 59, 255), outline=(ar, ag, ab, 255), width=3)
        draw.arc(box, start=135, end=405, fill=(ar, ag, ab, 255), width=5)
        draw.line([cx, cy, cx + 18, cy - 18], fill=(255, 255, 255, 255), width=3)
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 255, 255, 255))
        return ImageTk.PhotoImage(img)

    def update_progress(self, percent: float, message: str = "") -> None:
        if self._finished or not self.top.winfo_exists():
            return
        pct = max(0.0, min(100.0, float(percent)))
        cur_x2 = self._x1 + max(2, int((self._x2 - self._x1) * (pct / 100.0)))
        self.canvas.coords(self._fill_line, self._x1, self._y_bar, cur_x2, self._y_bar)
        self.canvas.itemconfigure(self._pct_id, text=f"{int(pct)}%")
        if message:
            self.canvas.itemconfigure(self._status_id, text=message)
        self.top.update()

    def finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        if self.top.winfo_exists():
            self.top.destroy()


# ── Theme Adapters for Matplotlib, tksheet, and Responsive Layouts ───────────

def style_matplotlib_figure(
    fig: Any,
    axes: Any = None,
    palette: Optional[ThemePalette] = None,
) -> ThemePalette:
    """Apply the active ModernTtk theme palette to a Matplotlib `Figure` and its `Axes`."""
    p = palette or ThemeManager.instance().palette
    fig.patch.set_facecolor(p.surface)

    if axes is None:
        ax_list = fig.get_axes()
    elif isinstance(axes, (list, tuple)):
        ax_list = list(axes)
    else:
        ax_list = [axes]

    for ax in ax_list:
        ax.set_facecolor(p.surface)
        ax.tick_params(axis="x", colors=p.fg_muted)
        ax.tick_params(axis="y", colors=p.fg_muted)
        ax.xaxis.label.set_color(p.fg_muted)
        ax.yaxis.label.set_color(p.fg_muted)
        ax.title.set_color(p.fg)
        ax.grid(True, alpha=0.25, color=p.border)
        if "top" in ax.spines:
            ax.spines["top"].set_visible(False)
        if "right" in ax.spines:
            ax.spines["right"].set_visible(False)
        if "left" in ax.spines:
            ax.spines["left"].set_color(p.border)
        if "bottom" in ax.spines:
            ax.spines["bottom"].set_color(p.border)
        leg = ax.get_legend()
        if leg is not None:
            frame = leg.get_frame()
            frame.set_facecolor(p.surface_alt)
            frame.set_edgecolor(p.border)
            for txt in leg.get_texts():
                txt.set_color(p.fg)
    return p


def style_matplotlib_toolbar(toolbar: Any, palette: Optional[ThemePalette] = None) -> None:
    """Style a Matplotlib `NavigationToolbar2Tk` to blend seamlessly with ModernTtk's palette."""
    if toolbar is None:
        return
    p = palette or ThemeManager.instance().palette
    try:
        toolbar.configure(background=p.surface)
    except Exception:
        pass
    for child in toolbar.winfo_children():
        wclass = child.winfo_class()
        try:
            if wclass in ("Button", "Checkbutton"):
                opts = {
                    "background": p.surface,
                    "activebackground": p.surface_hover,
                    "relief": "flat",
                    "borderwidth": 0,
                    "highlightthickness": 0,
                }
                if wclass == "Checkbutton":
                    opts["selectcolor"] = p.surface_hover
                child.configure(**opts)
            elif wclass == "Frame":
                child.configure(background=p.border)
            elif wclass == "Label":
                child.configure(background=p.surface, foreground=p.fg_muted)
            else:
                child.configure(background=p.surface)
        except Exception:
            pass


_SWITCH_IMG_CACHE: dict[tuple, ImageTk.PhotoImage] = {}


def _get_switch_photo(
    is_on: bool,
    on_hex: str,
    off_hex: str,
    border_hex: str,
    thumb_on_hex: str,
    thumb_off_hex: str,
    track_w: int = 38,
    track_h: int = 20,
) -> ImageTk.PhotoImage:
    key = (is_on, on_hex, off_hex, border_hex, thumb_on_hex, thumb_off_hex, track_w, track_h)
    if key in _SWITCH_IMG_CACHE:
        return _SWITCH_IMG_CACHE[key]

    scale = 4
    W, H = track_w * scale, track_h * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    track_fill = (*hex_to_rgb(on_hex if is_on else off_hex), 255)
    track_border = (*hex_to_rgb(on_hex if is_on else border_hex), 255)
    r = H // 2
    draw.rounded_rectangle([2, 2, W - 3, H - 3], radius=r, fill=track_fill, outline=track_border, width=scale)

    thumb_d = (track_h - 6) * scale
    pad = 3 * scale
    tx = (W - thumb_d - pad) if is_on else pad
    ty = (H - thumb_d) // 2
    thumb_col = (*hex_to_rgb(thumb_on_hex if is_on else thumb_off_hex), 255)
    draw.ellipse([tx, ty, tx + thumb_d, ty + thumb_d], fill=thumb_col)

    resample = getattr(Image, "Resampling", Image).LANCZOS
    pil_small = img.resize((track_w, track_h), resample=resample)
    photo = ImageTk.PhotoImage(pil_small)
    _SWITCH_IMG_CACHE[key] = photo
    return photo


def enable_tksheet_switches(sheet: Any) -> None:
    """Replace native `tksheet` square checkboxes with ModernTtk pill on/off toggle switches."""
    mt = getattr(sheet, "MT", None)
    if mt is None or getattr(mt, "_mtk_switches_enabled", False):
        return
    mt._mtk_switches_enabled = True
    mt._mtk_switch_refs = []

    orig_redraw = mt.redraw_grid_and_text

    def _wrapped_redraw(*args, **kwargs):
        res = orig_redraw(*args, **kwargs)
        try:
            mt.delete("mtk_switch")
            if not getattr(mt, "disp_checkbox", None) and not getattr(mt, "col_options", None) and not getattr(mt, "cell_options", None):
                return res
            # Hide native tksheet square checkbox polygons
            for cid in list(getattr(mt, "disp_checkbox", {}).keys()):
                mt.itemconfig(cid, state="hidden")
                mt.disp_checkbox[cid] = False

            p = ThemeManager.instance().palette
            on_img = _get_switch_photo(
                True,
                on_hex=p.primary,
                off_hex=p.surface_alt,
                border_hex=p.border_strong,
                thumb_on_hex=p.role_text("primary"),
                thumb_off_hex=p.fg_muted if p.mode == "light" else p.fg,
            )
            off_img = _get_switch_photo(
                False,
                on_hex=p.primary,
                off_hex=p.surface_alt,
                border_hex=p.border_strong,
                thumb_on_hex=p.role_text("primary"),
                thumb_off_hex=p.fg_muted if p.mode == "light" else p.fg,
            )
            mt._mtk_switch_refs = [on_img, off_img]

            # Extract visible row/col ranges from args or kwargs
            text_start_row = kwargs.get("text_start_row", args[17] if len(args) > 17 else 0)
            text_end_row = kwargs.get("text_end_row", args[18] if len(args) > 18 else 0)
            text_start_col = kwargs.get("text_start_col", args[19] if len(args) > 19 else 0)
            text_end_col = kwargs.get("text_end_col", args[20] if len(args) > 20 else 0)

            for r in range(text_start_row, text_end_row):
                datarn = r if mt.all_rows_displayed else mt.displayed_rows[r]
                y1 = mt.row_positions[r]
                y2 = mt.row_positions[r + 1]
                cy = int((y1 + y2) / 2)
                for c in range(text_start_col, text_end_col):
                    datacn = c if mt.all_columns_displayed else mt.displayed_columns[c]
                    if mt.get_cell_kwargs(datarn, datacn, key="checkbox"):
                        x1 = mt.col_positions[c]
                        x2 = mt.col_positions[c + 1]
                        cx = int((x1 + x2) / 2)
                        try:
                            is_on = bool(mt.data[datarn][datacn])
                        except Exception:
                            is_on = False
                        mt.create_image(
                            cx,
                            cy,
                            image=on_img if is_on else off_img,
                            anchor="center",
                            tags=("mtk_switch", "lift"),
                        )
            mt.lift("mtk_switch")
        except Exception:
            pass
        return res

    mt.redraw_grid_and_text = _wrapped_redraw

    def _on_mt_click_release(event: tk.Event) -> None:
        try:
            r = mt.identify_row(y=event.y, allow_end=False)
            c = mt.identify_col(x=event.x, allow_end=False)
            if r is None or c is None:
                return
            datarn = mt.datarn(r)
            datacn = mt.datacn(c)
            if not mt.get_cell_kwargs(datarn, datacn, key="checkbox"):
                return
            canvasx = mt.canvasx(event.x)
            canvasy = mt.canvasy(event.y)
            # Only trigger if outside tksheet's built-in top-left checkbox hit box (which tksheet already toggled)
            already_toggled = (
                canvasx < mt.col_positions[c] + mt.table_txt_height + 4
                and canvasy < mt.row_positions[r] + mt.table_txt_height + 4
            )
            if not already_toggled:
                mt.click_checkbox(r=r, c=c, datarn=datarn, datacn=datacn)
        except Exception:
            pass

    mt.bind("<ButtonRelease-1>", _on_mt_click_release, add="+")


def style_tksheet(sheet: Any, palette: Optional[ThemePalette] = None) -> None:
    """Apply the active ModernTtk theme palette to a `tksheet.Sheet` spreadsheet widget."""
    if sheet is None:
        return
    p = palette or ThemeManager.instance().palette
    try:
        enable_tksheet_switches(sheet)
        sheet.set_options(
            table_bg=p.surface,
            table_fg=p.fg,
            table_grid_fg=p.divider,
            table_selected_cells_border_fg=p.primary,
            table_selected_cells_bg=p.role_subtle_bg("primary"),
            table_selected_cells_fg=p.fg,
            header_bg=p.surface_alt,
            header_fg=p.fg,
            header_grid_fg=p.border,
            header_selected_cells_bg=p.surface_hover,
            header_selected_cells_fg=p.primary,
            index_bg=p.surface_alt,
            index_fg=p.fg_muted,
            index_grid_fg=p.border,
            top_left_bg=p.surface_alt,
            frame_bg=p.surface,
            outline_thickness=1,
            outline_color=p.border,
        )
        sheet.refresh()
    except Exception:
        pass


def bind_responsive_sections(
    container: tk.Widget,
    sections: Sequence[tk.Widget],
    breakpoint: int = 850,
) -> None:
    """Lay out section frames inline when wide enough and stack them vertically when narrow."""
    state = {"mode": None}

    def relayout(event: Optional[tk.Event] = None) -> None:
        width = event.width if event is not None else container.winfo_width()
        mode = "stacked" if width < breakpoint else "inline"
        if mode == state["mode"]:
            return
        state["mode"] = mode
        for section in sections:
            section.pack_forget()
        if mode == "stacked":
            for section in sections:
                section.pack(side="top", anchor="w", padx=4, pady=2)
        else:
            for section in sections:
                section.pack(side="left", padx=4, pady=2)

    container.bind("<Configure>", relayout, add="+")
    container.after_idle(relayout)

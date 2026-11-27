"""Advanced dashboard, form, and container widgets for ModernTtk:

- ModernMeter (Supersampled radial progress / arc gauge with animated sweeps & threshold colors)
- ModernText / ModernTextarea (Rounded multi-line text / code / log box with line numbers & scrollbar)
- ModernAccordion / ModernExpander (Windows 11 Settings-style collapsible card container)
- ModernTagInput / ModernChips (Multi-tag removable pill chip input selector)
"""

from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageTk

from ..icons import AVAILABLE_ICONS, create_icon_image
from ..themes import ThemePalette
from ..utils import create_rounded_rect_image, hex_to_rgb
from .base import ModernFrame, ModernLabel, ThemedWidgetMixin
from .table import ModernScrollbar

_METER_CACHE: Dict[Tuple, ImageTk.PhotoImage] = {}


@lru_cache(maxsize=256)
def _render_meter_arc_pil(
    size: int,
    thickness: int,
    ratio: float,
    arcrange: int,
    arcoffset: int,
    track_hex: str,
    fill_hex: str,
    bg_hex: str,
    scale: int = 4,
) -> Image.Image:
    """Render a 4x supersampled anti-aliased radial gauge arc with rounded endcaps."""
    s = max(32, size) * scale
    th = max(4, thickness) * scale
    pad = th // 2 + 4 * scale

    bg_rgba = (*hex_to_rgb(bg_hex), 255)
    track_rgba = (*hex_to_rgb(track_hex), 255)
    fill_rgba = (*hex_to_rgb(fill_hex), 255)

    img = Image.new("RGBA", (s, s), bg_rgba)
    draw = ImageDraw.Draw(img)

    bbox = [pad, pad, s - pad, s - pad]
    cx = s / 2.0
    cy = s / 2.0
    radius = (s - 2 * pad) / 2.0 - th / 2.0
    cap_r = th / 2.0

    def _draw_cap(deg: float, color_rgba: Tuple[int, int, int, int]) -> None:
        rad = math.radians(deg)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        draw.ellipse([x - cap_r, y - cap_r, x + cap_r, y + cap_r], fill=color_rgba)

    start_deg = float(arcoffset)
    end_deg = float(arcoffset + arcrange)

    # Background track arc
    draw.arc(bbox, start=start_deg, end=end_deg, fill=track_rgba, width=th)
    if arcrange < 360:
        _draw_cap(start_deg, track_rgba)
        _draw_cap(end_deg, track_rgba)

    # Active foreground arc
    clamped = max(0.0, min(1.0, ratio))
    if clamped > 0.005:
        active_end = start_deg + arcrange * clamped
        draw.arc(bbox, start=start_deg, end=active_end, fill=fill_rgba, width=th)
        _draw_cap(start_deg, fill_rgba)
        _draw_cap(active_end, fill_rgba)

    resample = getattr(Image, "Resampling", Image).LANCZOS
    return img.resize((max(32, size), max(32, size)), resample=resample)


def _get_meter_photo(
    size: int,
    thickness: int,
    ratio: float,
    arcrange: int,
    arcoffset: int,
    track_hex: str,
    fill_hex: str,
    bg_hex: str,
) -> ImageTk.PhotoImage:
    r_bucket = round(ratio, 3)
    key = (int(size), int(thickness), r_bucket, int(arcrange), int(arcoffset), track_hex, fill_hex, bg_hex)
    if key not in _METER_CACHE:
        pil_img = _render_meter_arc_pil(*key)
        _METER_CACHE[key] = ImageTk.PhotoImage(pil_img)
    return _METER_CACHE[key]


class ModernMeter(tk.Canvas, ThemedWidgetMixin):
    """Supersampled anti-aliased radial gauge (`ttkbootstrap.Meter` hybrid replacement).

    Features smooth animated value transitions, center metric display, subtext label,
    optional interactive click/drag adjustment, and automatic semantic color thresholds.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 65.0,
        maximum: float = 100.0,
        size: int = 165,
        thickness: int = 13,
        arcrange: int = 260,
        arcoffset: int = 140,
        bootstyle: str = "primary",
        textprefix: str = "",
        textsuffix: str = "%",
        subtext: str = "",
        thresholds: Optional[Sequence[Tuple[float, str]]] = None,
        interactive: bool = False,
        command: Optional[Callable[[float], None]] = None,
        **kwargs,
    ) -> None:
        self._value = max(0.0, min(maximum, value))
        self._target_value = self._value
        self._maximum = max(1.0, maximum)
        self._size = size
        self._thickness = thickness
        self._arcrange = arcrange
        self._arcoffset = arcoffset
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._prefix = textprefix
        self._suffix = textsuffix
        self._subtext = subtext
        self._thresholds = list(thresholds) if thresholds else []
        self._interactive = interactive
        self._command = command
        self._anim_job: Optional[str] = None

        super().__init__(
            master,
            width=size,
            height=size,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if interactive else "arrow",
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font_val = tkfont.Font(family=p.font_family, size=max(14, int(size * 0.14)), weight="bold")
        self._font_sub = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1), weight="bold")

        if interactive:
            self.bind("<ButtonPress-1>", self._on_pointer)
            self.bind("<B1-Motion>", self._on_pointer)
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def get(self) -> float:
        return self._target_value

    def set(
        self,
        value: float,
        subtext: Optional[str] = None,
        bootstyle: Optional[str] = None,
        animate: bool = True,
        notify: bool = False,
    ) -> None:
        """Set the meter value (with optional smooth animation)."""
        self._target_value = max(0.0, min(self._maximum, value))
        if subtext is not None:
            self._subtext = subtext
        if bootstyle is not None:
            self._role = bootstyle.split("-")[0]

        if notify and self._command is not None:
            self._command(self._target_value)

        if not animate or abs(self._target_value - self._value) < 0.5:
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
        if abs(diff) <= 0.4:
            self._value = self._target_value
            self._redraw()
            return

        self._value += diff * 0.28
        self._redraw()
        self._anim_job = self.after(16, self._step_animation)

    def _on_pointer(self, e: tk.Event) -> None:
        w = max(self.winfo_width(), self._size)
        h = max(self.winfo_height(), self._size)
        dx = e.x - w / 2.0
        dy = e.y - h / 2.0
        deg = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
        rel = (deg - self._arcoffset + 360.0) % 360.0
        if rel <= self._arcrange:
            ratio = rel / float(self._arcrange)
        elif rel > self._arcrange + (360 - self._arcrange) / 2.0:
            ratio = 0.0
        else:
            ratio = 1.0
        self.set(ratio * self._maximum, animate=False, notify=True)

    def _resolve_active_role(self) -> str:
        role = self._role
        for thresh_val, thresh_role in sorted(self._thresholds, key=lambda x: x[0]):
            if self._value >= thresh_val:
                role = thresh_role
        return role

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), self._size)
        h = max(self.winfo_height(), self._size)
        s = min(w, h)

        active_role = self._resolve_active_role()
        accent = p.role_color(active_role)
        ratio = self._value / self._maximum

        self._arc_img = _get_meter_photo(
            s,
            self._thickness,
            ratio,
            self._arcrange,
            self._arcoffset,
            p.surface_alt,
            accent,
            parent_bg,
        )
        self.create_image(w // 2, h // 2, image=self._arc_img, anchor="center")

        val_str = (
            f"{self._prefix}{int(round(self._value))}{self._suffix}"
            if float(self._maximum).is_integer()
            else f"{self._prefix}{self._value:.1f}{self._suffix}"
        )
        cy = h // 2 - (8 if self._subtext else 0)
        self.create_text(w // 2, cy, text=val_str, fill=p.fg, font=self._font_val, anchor="center")

        if self._subtext:
            self.create_text(
                w // 2,
                cy + int(self._size * 0.17),
                text=self._subtext,
                fill=p.fg_muted,
                font=self._font_sub,
                anchor="center",
            )


class ModernText(ModernFrame):
    """Anti-aliased rounded multi-line text / code / log editor.

    Features an accent focus border ring, integrated `ModernScrollbar`, optional line-number gutter,
    placeholder text, and semantic colored log helpers (`append_log(msg, level='INFO')`).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "",
        line_numbers: bool = False,
        readonly: bool = False,
        monospace: bool = False,
        bootstyle: str = "primary",
        width: int = 420,
        height: int = 160,
        **kwargs,
    ) -> None:
        self._placeholder = placeholder
        self._show_lines = line_numbers
        self._readonly = readonly
        self._monospace = monospace
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._is_focused = False
        self._showing_placeholder = False
        self._req_w = width
        self._req_h = height

        super().__init__(master, width=width, height=height, **kwargs)
        self.pack_propagate(False)

        p = self.palette
        fam = "Consolas" if monospace else p.font_family
        self._font = tkfont.Font(family=fam, size=p.font_size)

        self._bg_canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        self._bg_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self._inner = tk.Frame(self, bd=0, highlightthickness=0)
        self._inner.pack(fill="both", expand=True, padx=6, pady=6)

        self._gutter: Optional[tk.Canvas] = None
        if line_numbers:
            self._gutter = tk.Canvas(self._inner, width=36, bd=0, highlightthickness=0)
            self._gutter.pack(side="left", fill="y", padx=(2, 4))

        self.text = tk.Text(
            self._inner,
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=self._font,
            wrap="word",
            undo=True,
            padx=6,
            pady=4,
        )
        self.scrollbar = ModernScrollbar(self._inner, orient="vertical", command=self._on_scroll_cmd)
        self.text.configure(yscrollcommand=self._on_text_yscroll)

        self.scrollbar.pack(side="right", fill="y", padx=(4, 0))
        self.text.pack(side="left", fill="both", expand=True)

        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)
        self.text.bind("<KeyRelease>", lambda e: self._update_line_numbers())
        self.text.bind("<MouseWheel>", lambda e: self.after(10, self._update_line_numbers))
        self._bg_canvas.bind("<Configure>", lambda e: self._redraw())

        if placeholder:
            self._activate_placeholder()
        elif readonly:
            self.text.configure(state="disabled")

        self._redraw()

    def _on_scroll_cmd(self, *args) -> None:
        self.text.yview(*args)
        self._update_line_numbers()

    def _on_text_yscroll(self, first: str, last: str) -> None:
        self.scrollbar.set(first, last)
        self._update_line_numbers()

    def get(self) -> str:
        if self._showing_placeholder:
            return ""
        return self.text.get("1.0", "end-1c")

    def set(self, content: str) -> None:
        was_disabled = str(self.text["state"]) == "disabled"
        self.text.configure(state="normal")
        self._showing_placeholder = False
        self.text.delete("1.0", "end")
        if content:
            self.text.insert("1.0", content)
            self.text.configure(fg=self.palette.input_fg)
        elif not self._is_focused and self._placeholder:
            self._activate_placeholder()
        if was_disabled or self._readonly:
            self.text.configure(state="disabled")
        self._update_line_numbers()

    def clear(self) -> None:
        self.set("")

    def append_log(self, message: str, level: str = "INFO") -> None:
        """Append a styled log line ('INFO', 'SUCCESS', 'WARNING', 'ERROR') and auto-scroll."""
        was_disabled = str(self.text["state"]) == "disabled"
        self.text.configure(state="normal")
        if self._showing_placeholder:
            self._showing_placeholder = False
            self.text.delete("1.0", "end")

        lvl = level.upper().strip()
        tag = f"log_{lvl}"
        content = self.text.get("1.0", "end-1c")
        prefix = "\n" if content else ""
        self.text.insert("end", f"{prefix}[{lvl}] {message}", (tag,))
        self.text.see("end")
        if was_disabled or self._readonly:
            self.text.configure(state="disabled")
        self._update_line_numbers()

    def _activate_placeholder(self) -> None:
        if not self._placeholder:
            return
        self._showing_placeholder = True
        self.text.configure(state="normal", fg=self.palette.fg_subtle)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", self._placeholder)
        if self._readonly:
            self.text.configure(state="disabled")

    def _on_focus_in(self, _e: tk.Event) -> None:
        self._is_focused = True
        if self._showing_placeholder and not self._readonly:
            self._showing_placeholder = False
            self.text.delete("1.0", "end")
            self.text.configure(fg=self.palette.input_fg)
        self._redraw()

    def _on_focus_out(self, _e: tk.Event) -> None:
        self._is_focused = False
        if not self.get().strip() and self._placeholder and not self._readonly:
            self._activate_placeholder()
        self._redraw()

    def _update_line_numbers(self) -> None:
        if self._gutter is None or not self.winfo_exists():
            return
        p = self.palette
        self._gutter.delete("all")
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self._gutter.create_text(
                30,
                y + 2,
                anchor="ne",
                text=linenum,
                fill=p.fg_subtle,
                font=self._font,
            )
            i = self.text.index(f"{i}+1line")

    def _on_theme_changed(self, palette: ThemePalette) -> None:
        super()._on_theme_changed(palette)
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        self._bg_canvas.configure(bg=parent_bg)
        self._bg_canvas.delete("all")

        w = max(self._bg_canvas.winfo_width(), self._req_w)
        h = max(self._bg_canvas.winfo_height(), self._req_h)

        accent = p.role_color(self._role)
        border_col = accent if self._is_focused else p.input_border
        border_w = 2 if self._is_focused else 1

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            p.radius_md,
            fill_hex=p.input_bg,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
            bottom_border_hex=accent if self._is_focused else p.border_strong,
        )
        self._bg_canvas.create_image(0, 0, image=self._bg_img, anchor="nw")

        self._inner.configure(bg=p.input_bg)
        self.text.configure(
            bg=p.input_bg,
            fg=p.fg_subtle if self._showing_placeholder else p.input_fg,
            insertbackground=p.fg,
            selectbackground=accent,
            selectforeground=p.role_text(self._role),
        )
        # Configure semantic log level tags
        self.text.tag_configure("log_INFO", foreground=p.info)
        self.text.tag_configure("log_SUCCESS", foreground=p.success)
        self.text.tag_configure("log_WARNING", foreground=p.warning)
        self.text.tag_configure("log_ERROR", foreground=p.danger)

        if self._gutter is not None:
            self._gutter.configure(bg=p.surface_alt)
            self._update_line_numbers()


class ModernAccordion(ModernFrame):
    """Windows 11 Fluent Settings-style collapsible expander card (`ModernExpander` / `ModernAccordion`).

    Displays a rounded clickable header with icon, title, subtitle, and chevron (`▾` / `▸`).
    Place child widgets inside `expander.body`.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Section Title",
        subtitle: str = "",
        icon: Optional[str] = None,
        expanded: bool = True,
        bootstyle: str = "primary",
        surface_role: str = "surface",
        padding: int = 16,
        on_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ) -> None:
        self._title = title
        self._subtitle = subtitle
        self._icon = icon
        self._expanded = expanded
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._card_role = surface_role
        self._padding = padding
        self._on_toggle = on_toggle
        self._header_hovered = False

        super().__init__(master, **kwargs)

        self._bg_canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        self._bg_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self._header_h = 54 if subtitle else 44
        self._header = tk.Canvas(
            self,
            height=self._header_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self._header.pack(fill="x", padx=2, pady=(2, 0))

        self._divider = tk.Frame(self, height=1, bd=0)
        self.body = ModernFrame(self, surface_role=surface_role, padx=padding, pady=padding)

        if self._expanded:
            self._divider.pack(fill="x", padx=12)
            self.body.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        p = self.palette
        self._font_title = tkfont.Font(family=p.font_family, size=p.font_size, weight="bold")
        self._font_sub = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1))

        self._header.bind("<Enter>", lambda e: self._set_hover(True))
        self._header.bind("<Leave>", lambda e: self._set_hover(False))
        self._header.bind("<ButtonRelease-1>", lambda e: self.toggle())
        self._header.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def expand(self) -> None:
        if not self._expanded:
            self._expanded = True
            self._divider.pack(fill="x", padx=12)
            self.body.pack(fill="both", expand=True, padx=2, pady=(0, 2))
            self._redraw()
            if self._on_toggle:
                self._on_toggle(True)

    def collapse(self) -> None:
        if self._expanded:
            self._expanded = False
            self._divider.pack_forget()
            self.body.pack_forget()
            self._redraw()
            if self._on_toggle:
                self._on_toggle(False)

    def toggle(self) -> None:
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def _set_hover(self, hov: bool) -> None:
        self._header_hovered = hov
        self._redraw()

    def _on_theme_changed(self, palette: ThemePalette) -> None:
        super()._on_theme_changed(palette)
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        surf = getattr(p, self._card_role, p.surface)
        self._bg_canvas.configure(bg=parent_bg)
        self._bg_canvas.delete("all")

        w = max(40, self.winfo_width())
        h = max(self._header_h + 4, self.winfo_height())

        self._card_img = create_rounded_rect_image(
            w,
            h,
            p.radius_lg,
            fill_hex=surf,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
            bottom_border_hex=p.border_strong,
        )
        self._bg_canvas.create_image(0, 0, image=self._card_img, anchor="nw")
        self._divider.configure(bg=p.divider)

        # Draw header contents
        hw = max(40, self._header.winfo_width())
        hh = self._header_h
        self._header.configure(bg=surf)
        self._header.delete("all")

        accent = p.role_color(self._role)
        left_x = 16
        if self._icon:
            if self._icon.lower().strip() in AVAILABLE_ICONS:
                self._ic_img = create_icon_image(self._icon, size=18, color=accent)
                self._header.create_image(left_x, hh // 2, image=self._ic_img, anchor="w")
            else:
                self._header.create_text(left_x, hh // 2, text=self._icon, fill=accent, font=self._font_title, anchor="w")
            left_x += 28

        if self._subtitle:
            self._header.create_text(left_x, hh // 2 - 8, text=self._title, fill=p.fg, font=self._font_title, anchor="w")
            self._header.create_text(left_x, hh // 2 + 10, text=self._subtitle, fill=p.fg_muted, font=self._font_sub, anchor="w")
        else:
            self._header.create_text(left_x, hh // 2, text=self._title, fill=p.fg, font=self._font_title, anchor="w")

        chev_name = "chevron_up" if self._expanded else "chevron_down"
        chev_col = accent if self._header_hovered else p.fg_muted
        self._chev_img = create_icon_image(chev_name, size=16, color=chev_col)
        self._header.create_image(hw - 18, hh // 2, image=self._chev_img, anchor="e")


class ModernTagInput(tk.Canvas, ThemedWidgetMixin):
    """Rounded multi-tag chip input selector (`ModernChips` / `ModernTagInput`).

    Renders removable pill chips with a clickable `✕` icon and an inline text entry
    where pressing `<Return>` or `,` adds a new tag.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        tags: Sequence[str] = (),
        placeholder: str = "Add tag + Enter...",
        bootstyle: str = "primary",
        on_change: Optional[Callable[[List[str]], None]] = None,
        width: int = 360,
        height: int = 42,
        **kwargs,
    ) -> None:
        self._tags: List[str] = list(tags)
        self._placeholder = placeholder
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._on_change = on_change
        self._is_focused = False
        self._chip_Hitboxes: List[Tuple[int, int, int, int, str]] = []
        self._chip_imgs: List[ImageTk.PhotoImage] = []

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="xterm",
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1), weight="bold")
        self._entry_font = tkfont.Font(family=p.font_family, size=p.font_size)

        self._var = tk.StringVar()
        self._entry = tk.Entry(
            self,
            textvariable=self._var,
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=self._entry_font,
        )
        self._entry_win = self.create_window(12, height // 2, window=self._entry, anchor="w")

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Return>", self._on_submit_key)
        self._entry.bind("<comma>", self._on_submit_key)
        self._entry.bind("<BackSpace>", self._on_backspace)
        self.bind("<ButtonRelease-1>", self._on_canvas_click)
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get(self) -> List[str]:
        return list(self._tags)

    def set(self, tags: Sequence[str], notify: bool = False) -> None:
        self._tags = list(tags)
        self._redraw()
        if notify and self._on_change:
            self._on_change(self.get())

    def add_tag(self, tag: str, notify: bool = True) -> None:
        clean = tag.strip().rstrip(",").strip()
        if clean and clean not in self._tags:
            self._tags.append(clean)
            self._redraw()
            if notify and self._on_change:
                self._on_change(self.get())

    def remove_tag(self, tag: str, notify: bool = True) -> None:
        if tag in self._tags:
            self._tags.remove(tag)
            self._redraw()
            if notify and self._on_change:
                self._on_change(self.get())

    def _on_focus_in(self, _e: tk.Event) -> None:
        self._is_focused = True
        self._redraw()

    def _on_focus_out(self, _e: tk.Event) -> None:
        self._is_focused = False
        val = self._var.get().strip().rstrip(",")
        if val:
            self._var.set("")
            self.add_tag(val)
        else:
            self._redraw()

    def _on_submit_key(self, _e: tk.Event) -> str:
        val = self._var.get().strip().rstrip(",")
        self._var.set("")
        if val:
            self.add_tag(val)
        return "break"

    def _on_backspace(self, _e: tk.Event) -> None:
        if not self._var.get() and self._tags:
            self.remove_tag(self._tags[-1])

    def _on_canvas_click(self, e: tk.Event) -> None:
        for x1, y1, x2, y2, tag in self._chip_Hitboxes:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self.remove_tag(tag)
                return
        self._entry.focus_set()

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("chip_item")
        self.delete("bg_img")
        self._chip_Hitboxes.clear()
        self._chip_imgs.clear()

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))

        accent = p.role_color(self._role)
        border_col = accent if self._is_focused else p.input_border
        border_w = 2 if self._is_focused else 1

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            p.radius_md,
            fill_hex=p.input_bg,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
            bottom_border_hex=accent if self._is_focused else p.border_strong,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw", tags="bg_img")
        self.tag_lower("bg_img")

        x_cursor = 10
        cy = h // 2
        chip_h = max(22, h - 16)
        subtle_bg = p.role_subtle_bg(self._role)

        for tag in self._tags:
            label_str = f"{tag}  ✕"
            tw = self._font.measure(label_str) + 18
            if x_cursor + tw > w - 70:
                break
            c_img = create_rounded_rect_image(
                tw,
                chip_h,
                chip_h // 2,
                fill_hex=subtle_bg,
                border_hex=accent,
                border_width=1,
                bg_hex=p.input_bg,
            )
            self._chip_imgs.append(c_img)
            y1 = cy - chip_h // 2
            self.create_image(x_cursor, y1, image=c_img, anchor="nw", tags="chip_item")
            self.create_text(
                x_cursor + tw // 2,
                cy,
                text=label_str,
                fill=accent,
                font=self._font,
                tags="chip_item",
            )
            self._chip_Hitboxes.append((x_cursor, y1, x_cursor + tw, y1 + chip_h, tag))
            x_cursor += tw + 6

        self._entry.configure(
            bg=p.input_bg,
            fg=p.input_fg,
            insertbackground=p.fg,
            selectbackground=accent,
            selectforeground=p.role_text(self._role),
        )
        self.coords(self._entry_win, x_cursor + 2, cy)
        self.itemconfigure(self._entry_win, width=max(50, w - x_cursor - 14))


# Ergonomic aliases
ModernTextarea = ModernText
ModernExpander = ModernAccordion
ModernChips = ModernTagInput

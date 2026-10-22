"""Modern containers and navigation widgets: ModernCard, ModernSegmentedButton, ModernBadge, ModernTooltip."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, List, Optional, Sequence

from ..themes import ThemePalette
from ..utils import create_rounded_rect_image
from .base import ModernFrame, ModernLabel, ThemedWidgetMixin


class ModernCard(tk.Canvas, ThemedWidgetMixin):
    """Elevated rounded surface card container with optional title, subtitle, and inner content frame.

    Place child widgets inside `card.body` (a `ModernFrame` whose background automatically tracks the card surface).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        padding: int = 18,
        radius: Optional[int] = None,
        surface_role: str = "surface",
        **kwargs,
    ) -> None:
        self._title = title
        self._subtitle = subtitle
        self._padding = padding
        self._custom_radius = radius
        self._surface_role = surface_role

        super().__init__(
            master,
            bd=0,
            highlightthickness=0,
            relief="flat",
            **kwargs,
        )
        self._init_themed()

        self._container = ModernFrame(self, surface_role=self._surface_role)
        self._header_frame: Optional[ModernFrame] = None
        self._title_lbl: Optional[ModernLabel] = None
        self._sub_lbl: Optional[ModernLabel] = None

        if title or subtitle:
            self._header_frame = ModernFrame(self._container, surface_role=self._surface_role)
            self._header_frame.pack(fill="x", pady=(0, 12))
            if title:
                self._title_lbl = ModernLabel(
                    self._header_frame,
                    text=title,
                    surface_role=self._surface_role,
                    font_size_delta=2,
                    bold=True,
                    anchor="w",
                )
                self._title_lbl.pack(fill="x")
            if subtitle:
                self._sub_lbl = ModernLabel(
                    self._header_frame,
                    text=subtitle,
                    surface_role=self._surface_role,
                    muted=True,
                    font_size_delta=-1,
                    anchor="w",
                )
                self._sub_lbl.pack(fill="x", pady=(2, 0))

        self.body = ModernFrame(self._container, surface_role=self._surface_role)
        self.body.pack(fill="both", expand=True)

        self._win_id = self.create_window(padding, padding, window=self._container, anchor="nw")

        self._container.bind("<Configure>", self._on_inner_configure)
        self.bind("<Configure>", self._on_canvas_configure)

    @property
    def surface_color(self) -> str:
        return getattr(self.palette, self._surface_role, self.palette.surface)

    def _on_inner_configure(self, _e: tk.Event) -> None:
        req_w = self._container.winfo_reqwidth() + self._padding * 2
        req_h = self._container.winfo_reqheight() + self._padding * 2
        if self.winfo_reqwidth() != req_w or self.winfo_reqheight() != req_h:
            super().configure(width=req_w, height=req_h)
        self._redraw()

    def _on_canvas_configure(self, e: tk.Event) -> None:
        inner_w = max(10, e.width - self._padding * 2)
        self.itemconfigure(self._win_id, width=inner_w)
        self._redraw()

    def _on_theme_changed(self, _p: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("card_bg")

        w = max(self.winfo_width(), self.winfo_reqwidth(), 40)
        h = max(self.winfo_height(), self.winfo_reqheight(), 40)
        r = self._custom_radius if self._custom_radius is not None else p.radius_lg
        surf_bg = getattr(p, self._surface_role, p.surface)

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            r,
            fill_hex=surf_bg,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
            bottom_border_hex=p.border_strong,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw", tags="card_bg")
        self.tag_lower("card_bg")


class ModernSegmentedButton(tk.Canvas, ThemedWidgetMixin):
    """Animated pill/rounded segmented control (tab switcher) with sliding indicator."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Sequence[str] = ("Tab 1", "Tab 2"),
        default: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        bootstyle: str = "primary",
        pill: bool = False,
        height: int = 36,
        **kwargs,
    ) -> None:
        self._values: List[str] = list(values)
        self._selected = default if default is not None else (self._values[0] if self._values else "")
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._pill = pill

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size, weight="bold")
        seg_w = max((self._font.measure(v) + 32 for v in self._values), default=80)
        self._seg_w = max(76, seg_w)
        total_w = self._seg_w * len(self._values) + 8

        idx = self._values.index(self._selected) if self._selected in self._values else 0
        self._anim_idx = float(idx)
        self._hover_idx: Optional[int] = None
        self._anim_job: Optional[str] = None

        super().__init__(
            master,
            width=total_w,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self._init_themed()

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get(self) -> str:
        return self._selected

    def set(self, value: str, notify: bool = False) -> None:
        if value not in self._values:
            return
        self._selected = value
        target_idx = float(self._values.index(value))
        self._animate_to(target_idx)
        if notify and self._command is not None:
            self._command(value)

    def _animate_to(self, target: float) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        diff = target - self._anim_idx
        if abs(diff) <= 0.08:
            self._anim_idx = target
            self._redraw()
            return

        self._anim_idx += diff * 0.38
        self._redraw()
        self._anim_job = self.after(14, lambda: self._animate_to(target))

    def _set_hover(self, idx: Optional[int]) -> None:
        if self._hover_idx != idx:
            self._hover_idx = idx
            self._redraw()

    def _on_motion(self, e: tk.Event) -> None:
        if not self._values:
            return
        w = max(self.winfo_width(), int(self["width"]))
        seg_w = (w - 8) / len(self._values)
        idx = int((e.x - 4) // seg_w)
        if 0 <= idx < len(self._values):
            self._set_hover(idx)
        else:
            self._set_hover(None)

    def _on_click(self, e: tk.Event) -> None:
        if not self._values:
            return
        w = max(self.winfo_width(), int(self["width"]))
        seg_w = (w - 8) / len(self._values)
        idx = int((e.x - 4) // seg_w)
        if 0 <= idx < len(self._values):
            self.set(self._values[idx], notify=True)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        outer_r = h // 2 if self._pill else p.radius_md + 2
        inner_r = (h - 6) // 2 if self._pill else p.radius_md

        self._track_img = create_rounded_rect_image(
            w,
            h,
            outer_r,
            fill_hex=p.surface_alt,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._track_img, anchor="nw")

        if not self._values:
            return

        seg_w = (w - 6) / len(self._values)
        pill_x = int(3 + self._anim_idx * seg_w)
        pill_w = int(seg_w)
        pill_h = h - 6

        accent = p.role_color(self._role)
        self._pill_img = create_rounded_rect_image(
            pill_w,
            pill_h,
            inner_r,
            fill_hex=accent,
            bg_hex=p.surface_alt,
        )
        self.create_image(pill_x, 3, image=self._pill_img, anchor="nw")

        for i, val in enumerate(self._values):
            cx = int(3 + (i + 0.5) * seg_w)
            is_sel = val == self._selected
            fg = p.role_text(self._role) if is_sel else (p.fg if self._hover_idx == i else p.fg_muted)
            self.create_text(cx, h // 2, text=val, fill=fg, font=self._font)


class ModernBadge(tk.Canvas, ThemedWidgetMixin):
    """Compact semantic status pill/tag badge."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        bootstyle: str = "primary",
        variant: str = "subtle",  # "subtle", "filled", "outline"
        pill: bool = True,
        height: int = 24,
        padx: int = 10,
        **kwargs,
    ) -> None:
        parts = bootstyle.lower().split("-")
        self._role = parts[0] if parts else "primary"
        if "filled" in parts:
            variant = "filled"
        elif "outline" in parts:
            variant = "outline"
        elif "subtle" in parts:
            variant = "subtle"

        self._text = text
        self._variant = variant
        self._pill = pill
        self._padx = padx

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1), weight="bold")
        w = self._font.measure(text) + padx * 2

        super().__init__(
            master,
            width=w,
            height=height,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def set_text(self, text: str, bootstyle: Optional[str] = None) -> None:
        self._text = text
        if bootstyle:
            self._role = bootstyle.split("-")[0]
        w = self._font.measure(text) + self._padx * 2
        super().configure(width=w)
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
        r = h // 2 if self._pill else p.radius_sm
        base = p.role_color(self._role)

        if self._variant == "filled":
            fill_col = base
            border_col = None
            bw = 0
            fg = p.role_text(self._role)
        elif self._variant == "outline":
            fill_col = parent_bg
            border_col = base
            bw = 1
            fg = base
        else:
            fill_col = p.role_subtle_bg(self._role)
            border_col = base
            bw = 1
            fg = base

        self._img = create_rounded_rect_image(
            w,
            h,
            r,
            fill_hex=fill_col,
            border_hex=border_col,
            border_width=bw,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._img, anchor="nw")
        self.create_text(w // 2, h // 2, text=self._text, fill=fg, font=self._font)


class ModernTooltip:
    """Modern floating themed tooltip attached to any Tkinter/ModernTkk widget."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 350) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._tip_win: Optional[tk.Toplevel] = None
        self._job: Optional[str] = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e: tk.Event) -> None:
        self._cancel()
        self._job = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def _show(self) -> None:
        if self._tip_win is not None or not self.widget.winfo_exists():
            return
        from ..style import ThemeManager
        p = ThemeManager.instance().palette

        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        win = tk.Toplevel(self.widget)
        win.wm_overrideredirect(True)
        win.configure(bg=p.border_strong, padx=1, pady=1)
        lbl = tk.Label(
            win,
            text=self.text,
            bg=p.surface_alt,
            fg=p.fg,
            font=(p.font_family, p.font_size - 1),
            padx=10,
            pady=5,
        )
        lbl.pack()
        win.update_idletasks()
        tw = win.winfo_reqwidth()
        win.geometry(f"+{max(4, x - tw // 2)}+{y}")
        self._tip_win = win

    def _hide(self, _e: Optional[tk.Event] = None) -> None:
        self._cancel()
        if self._tip_win is not None:
            try:
                self._tip_win.destroy()
            except tk.TclError:
                pass
            self._tip_win = None


class ModernNotebook(ModernFrame):
    """Modern tabbed notebook container with animated tab indicator, icons, and optional closeable tabs.

    Supports both:
    - `tab_frame = notebook.add("Settings", icon="⚙")` (creates and returns a themed `ModernFrame`)
    - `notebook.add(existing_frame, text="Settings", icon="⚙")` (`ttk.Notebook`-compatible signature)

    Variants (`variant=`):
    - `"underline"` (default): Clean modern tab bar with a sliding rounded accent indicator bar underneath.
    - `"pills"`: Segmented rounded pill tabs inside an elevated track.
    - `"cards"`: Elevated rounded card tabs attached to a surface content container.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        bootstyle: str = "primary",
        variant: str = "underline",  # "underline", "pills", or "cards"
        closeable: bool = False,
        on_tab_change: Optional[Callable[[str], None]] = None,
        tab_height: int = 40,
        surface_role: str = "surface",
        **kwargs,
    ) -> None:
        parts = bootstyle.lower().split("-")
        self._role = parts[0] if parts else "primary"
        if "pills" in parts or "pill" in parts:
            variant = "pills"
        elif "cards" in parts or "card" in parts:
            variant = "cards"
        elif "underline" in parts:
            variant = "underline"

        self._variant = variant
        self._closeable = closeable
        self._on_tab_change = on_tab_change
        self._tab_h = tab_height
        self._body_surface_role = surface_role

        super().__init__(master, **kwargs)

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size, weight="bold")
        self._font_badge = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")

        # Tab bar canvas
        self._tab_bar = tk.Canvas(
            self,
            height=self._tab_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self._tab_bar.pack(fill="x", pady=(0, 8 if variant == "pills" else 0))

        # Content container
        self._content_card = ModernCard(
            self,
            padding=16,
            surface_role=surface_role,
        )
        self._content_card.pack(fill="both", expand=True)

        # Tab metadata list: dicts with {title, frame, icon, badge, closeable}
        self._tabs: List[dict] = []
        self._active_idx: int = 0
        self._anim_x: float = 0.0
        self._anim_w: float = 80.0
        self._hover_idx: Optional[int] = None
        self._hover_close_idx: Optional[int] = None
        self._anim_job: Optional[str] = None
        self._tab_bounds: List[ tuple[int, int, int, int] ] = []
        self._close_bounds: List[ Optional[tuple[int, int, int, int]] ] = []
        self._imgs: List[tk.PhotoImage] = []

        self._tab_bar.bind("<Motion>", self._on_motion)
        self._tab_bar.bind("<Leave>", self._on_leave)
        self._tab_bar.bind("<ButtonRelease-1>", self._on_click)
        self._tab_bar.bind("<Configure>", lambda e: self._redraw_tabs(animate=False))

    def add(
        self,
        child_or_title: tk.Widget | str,
        text: Optional[str] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        closeable: Optional[bool] = None,
    ) -> ModernFrame | tk.Widget:
        """Add a new tab and return its content frame."""
        if isinstance(child_or_title, str):
            title = child_or_title
            frame = ModernFrame(self._content_card.body, surface_role=self._body_surface_role)
        else:
            frame = child_or_title
            title = text or f"Tab {len(self._tabs) + 1}"

        is_closeable = self._closeable if closeable is None else closeable
        self._tabs.append({
            "title": title,
            "frame": frame,
            "icon": icon,
            "badge": badge,
            "closeable": is_closeable,
        })

        if len(self._tabs) == 1:
            self._active_idx = 0
            frame.pack(fill="both", expand=True)
            self._compute_tab_layout()
            if self._tab_bounds:
                x1, _, x2, _ = self._tab_bounds[0]
                self._anim_x = float(x1)
                self._anim_w = float(x2 - x1)
        else:
            frame.pack_forget()

        self._redraw_tabs(animate=False)
        return frame

    def tab(self, title: str) -> ModernFrame | tk.Widget:
        """Return the content frame for a tab by its title (creates it if not found)."""
        for item in self._tabs:
            if item["title"] == title:
                return item["frame"]
        return self.add(title)

    def select(self, index_or_title: int | str, notify: bool = True) -> None:
        """Switch to a tab by index or title."""
        if not self._tabs:
            return
        target_idx = self._active_idx
        if isinstance(index_or_title, int):
            if 0 <= index_or_title < len(self._tabs):
                target_idx = index_or_title
        else:
            for i, item in enumerate(self._tabs):
                if item["title"] == index_or_title:
                    target_idx = i
                    break

        if target_idx == self._active_idx and self._tabs[target_idx]["frame"].winfo_ismapped():
            return

        for i, item in enumerate(self._tabs):
            if i == target_idx:
                item["frame"].pack(fill="both", expand=True)
            else:
                item["frame"].pack_forget()

        self._active_idx = target_idx
        self._compute_tab_layout()
        if 0 <= target_idx < len(self._tab_bounds):
            tx1, _, tx2, _ = self._tab_bounds[target_idx]
            self._animate_indicator(float(tx1), float(tx2 - tx1))
        else:
            self._redraw_tabs(animate=False)

        if notify and self._on_tab_change is not None:
            self._on_tab_change(self._tabs[target_idx]["title"])

    def close_tab(self, index: int) -> None:
        """Close and remove a tab by index."""
        if not (0 <= index < len(self._tabs)) or len(self._tabs) <= 1:
            return
        removed = self._tabs.pop(index)
        removed["frame"].pack_forget()
        if self._active_idx >= len(self._tabs):
            self._active_idx = len(self._tabs) - 1
        self.select(self._active_idx, notify=True)
        self._redraw_tabs(animate=False)

    def get_selected_title(self) -> str:
        if not self._tabs:
            return ""
        return self._tabs[self._active_idx]["title"]

    def _animate_indicator(self, target_x: float, target_w: float) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        dx = target_x - self._anim_x
        dw = target_w - self._anim_w
        if abs(dx) <= 1.5 and abs(dw) <= 1.5:
            self._anim_x = target_x
            self._anim_w = target_w
            self._redraw_tabs(animate=False)
            return

        self._anim_x += dx * 0.42
        self._anim_w += dw * 0.42
        self._redraw_tabs(animate=True)
        self._anim_job = self.after(14, lambda: self._animate_indicator(target_x, target_w))

    def _compute_tab_layout(self) -> None:
        self._tab_bounds.clear()
        self._close_bounds.clear()
        cur_x = 6
        h = self._tab_h
        for item in self._tabs:
            label = f"{item['icon']}  {item['title']}" if item["icon"] else item["title"]
            tw = self._font.measure(label)
            extra = 0
            if item["badge"]:
                extra += self._font_badge.measure(str(item["badge"])) + 20
            if item["closeable"] and len(self._tabs) > 1:
                extra += 22
            tab_w = max(84, tw + 34 + extra)
            x1, x2 = cur_x, cur_x + tab_w
            self._tab_bounds.append((x1, 3, x2, h - 3))
            if item["closeable"] and len(self._tabs) > 1:
                cx = x2 - 16
                cy = h // 2
                self._close_bounds.append((cx - 8, cy - 8, cx + 8, cy + 8))
            else:
                self._close_bounds.append(None)
            cur_x = x2 + 6

    def _on_motion(self, e: tk.Event) -> None:
        hov_tab: Optional[int] = None
        hov_close: Optional[int] = None
        for i, (x1, y1, x2, y2) in enumerate(self._tab_bounds):
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                hov_tab = i
                cb = self._close_bounds[i]
                if cb and cb[0] <= e.x <= cb[2] and cb[1] <= e.y <= cb[3]:
                    hov_close = i
                break
        if hov_tab != self._hover_idx or hov_close != self._hover_close_idx:
            self._hover_idx = hov_tab
            self._hover_close_idx = hov_close
            self._redraw_tabs(animate=False)

    def _on_leave(self, _e: tk.Event) -> None:
        if self._hover_idx is not None or self._hover_close_idx is not None:
            self._hover_idx = None
            self._hover_close_idx = None
            self._redraw_tabs(animate=False)

    def _on_click(self, e: tk.Event) -> None:
        for i, (x1, y1, x2, y2) in enumerate(self._tab_bounds):
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                cb = self._close_bounds[i]
                if cb and cb[0] <= e.x <= cb[2] and cb[1] <= e.y <= cb[3]:
                    self.close_tab(i)
                    return
                self.select(i, notify=True)
                return

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        super()._on_theme_changed(_palette)
        self._redraw_tabs(animate=False)

    def _redraw_tabs(self, animate: bool = False) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        self._tab_bar.configure(bg=parent_bg)
        self._tab_bar.delete("all")
        self._imgs.clear()

        if not self._tabs:
            return

        self._compute_tab_layout()
        if not animate and 0 <= self._active_idx < len(self._tab_bounds):
            ax1, _, ax2, _ = self._tab_bounds[self._active_idx]
            self._anim_x = float(ax1)
            self._anim_w = float(ax2 - ax1)

        w = max(self._tab_bar.winfo_width(), self._tab_bounds[-1][2] + 12)
        h = self._tab_h
        accent = p.role_color(self._role)

        if self._variant == "pills":
            track_w = self._tab_bounds[-1][2] + 6
            track_img = create_rounded_rect_image(
                track_w,
                h,
                p.radius_md + 2,
                fill_hex=p.surface_alt,
                border_hex=p.border,
                border_width=1,
                bg_hex=parent_bg,
            )
            self._imgs.append(track_img)
            self._tab_bar.create_image(0, 0, image=track_img, anchor="nw")

            pill_img = create_rounded_rect_image(
                int(self._anim_w),
                h - 6,
                p.radius_md,
                fill_hex=accent,
                bg_hex=p.surface_alt,
            )
            self._imgs.append(pill_img)
            self._tab_bar.create_image(int(self._anim_x), 3, image=pill_img, anchor="nw")
        elif self._variant == "underline":
            self._tab_bar.create_line(0, h - 1, w, h - 1, fill=p.divider, width=1)

        for i, item in enumerate(self._tabs):
            x1, y1, x2, y2 = self._tab_bounds[i]
            tw = x2 - x1
            th = y2 - y1
            is_sel = i == self._active_idx
            is_hov = i == self._hover_idx

            if self._variant == "underline":
                if is_hov and not is_sel:
                    hov_img = create_rounded_rect_image(
                        tw,
                        th - 4,
                        p.radius_sm,
                        fill_hex=p.surface_hover,
                        bg_hex=parent_bg,
                    )
                    self._imgs.append(hov_img)
                    self._tab_bar.create_image(x1, y1, image=hov_img, anchor="nw")
                fg = accent if is_sel else (p.fg if is_hov else p.fg_muted)
            elif self._variant == "cards":
                fill_col = p.surface if is_sel else (p.surface_hover if is_hov else p.surface_alt)
                border_col = accent if is_sel else p.border
                card_img = create_rounded_rect_image(
                    tw,
                    th,
                    p.radius_md,
                    fill_hex=fill_col,
                    border_hex=border_col,
                    border_width=1,
                    bg_hex=parent_bg,
                )
                self._imgs.append(card_img)
                self._tab_bar.create_image(x1, y1, image=card_img, anchor="nw")
                fg = accent if is_sel else (p.fg if is_hov else p.fg_muted)
            else:  # pills
                fg = p.role_text(self._role) if is_sel else (p.fg if is_hov else p.fg_muted)

            label = f"{item['icon']}  {item['title']}" if item["icon"] else item["title"]
            text_x = x1 + 16
            self._tab_bar.create_text(
                text_x,
                h // 2,
                text=label,
                fill=fg,
                font=self._font,
                anchor="w",
            )

            # Optional badge pill inside the tab
            if item["badge"]:
                lw = self._font.measure(label)
                bx = text_x + lw + 8
                bw = self._font_badge.measure(str(item["badge"])) + 12
                bh = 18
                b_fill = p.role_text(self._role) if (self._variant == "pills" and is_sel) else p.role_subtle_bg(self._role)
                b_fg = accent
                b_img = create_rounded_rect_image(
                    bw,
                    bh,
                    bh // 2,
                    fill_hex=b_fill,
                    bg_hex=accent if (self._variant == "pills" and is_sel) else parent_bg,
                )
                self._imgs.append(b_img)
                self._tab_bar.create_image(bx, (h - bh) // 2, image=b_img, anchor="nw")
                self._tab_bar.create_text(
                    bx + bw // 2,
                    h // 2,
                    text=str(item["badge"]),
                    fill=b_fg,
                    font=self._font_badge,
                )

            # Optional close button
            cb = self._close_bounds[i]
            if cb is not None:
                cx = (cb[0] + cb[2]) // 2
                cy = (cb[1] + cb[3]) // 2
                close_col = p.danger if self._hover_close_idx == i else fg
                self._tab_bar.create_text(cx, cy, text="✕", fill=close_col, font=self._font_badge)

        if self._variant == "underline":
            ind_w = max(24, int(self._anim_w - 20))
            ind_x = int(self._anim_x + 10)
            ind_img = create_rounded_rect_image(
                ind_w,
                4,
                2,
                fill_hex=accent,
                bg_hex=parent_bg,
            )
            self._imgs.append(ind_img)
            self._tab_bar.create_image(ind_x, h - 5, image=ind_img, anchor="nw")


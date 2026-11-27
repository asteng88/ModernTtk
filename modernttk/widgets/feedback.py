"""Modern feedback and continuous control widgets: ModernProgressBar, ModernSlider, ModernToast, ModernDialog."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional

from ..themes import ThemePalette
from ..utils import create_circle_image, create_rounded_rect_image
from .base import ThemedWidgetMixin
from .buttons import ModernButton


class ModernProgressBar(tk.Canvas, ThemedWidgetMixin):
    """Smooth rounded progress bar supporting determinate percentage, optional text label, and indeterminate animation."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 0.0,
        maximum: float = 100.0,
        bootstyle: str = "primary",
        mode: str = "determinate",  # "determinate" or "indeterminate"
        show_percent: bool = False,
        width: int = 240,
        height: int = 12,
        **kwargs,
    ) -> None:
        length = kwargs.pop("length", None)
        if length is not None:
            width = int(length)
        kwargs.pop("style", None)
        kwargs.pop("orient", None)
        variable: Optional[tk.Variable] = kwargs.pop("variable", None)

        self._variable = variable
        if variable is not None:
            try:
                value = float(variable.get())
            except Exception:
                pass
        self._value = value
        self._maximum = max(1.0, maximum)
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._mode = mode
        self._show_percent = show_percent
        self._ind_pos = 0.0
        self._anim_job: Optional[str] = None
        self._trace_id: Optional[str] = None

        if show_percent and height < 20:
            height = 20

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            **kwargs,
        )
        self._init_themed()

        if self._variable is not None:
            self._trace_id = self._variable.trace_add("write", self._on_var_changed)
            self.bind("<Destroy>", self._on_cleanup_var, add="+")

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")

        self.bind("<Configure>", lambda e: self._redraw())
        if self._mode == "indeterminate":
            self.start()
        else:
            self._redraw()

    def _on_var_changed(self, *_args) -> None:
        if self._variable is not None:
            try:
                self._value = max(0.0, min(self._maximum, float(self._variable.get())))
                self._redraw()
            except Exception:
                pass

    def _on_cleanup_var(self, e: tk.Event) -> None:
        if e.widget is self and self._variable is not None and self._trace_id:
            try:
                self._variable.trace_remove("write", self._trace_id)
            except Exception:
                pass

    def get(self) -> float:
        return self._value

    def set(self, value: float) -> None:
        self._value = max(0.0, min(self._maximum, float(value)))
        if self._variable is not None:
            try:
                self._variable.set(self._value)
            except Exception:
                pass
        self._redraw()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        if "value" in kwargs:
            self.set(float(kwargs.pop("value")))
        if "maximum" in kwargs:
            self._maximum = max(1.0, float(kwargs.pop("maximum")))
        if "mode" in kwargs:
            new_mode = str(kwargs.pop("mode"))
            if new_mode == "indeterminate":
                self.start()
            else:
                self.stop()
        if "bootstyle" in kwargs:
            self._role = str(kwargs.pop("bootstyle")).split("-")[0]
        if "length" in kwargs:
            kwargs["width"] = int(kwargs.pop("length"))
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "value":
            return self._value
        if key == "maximum":
            return self._maximum
        if key == "mode":
            return self._mode
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

    def start(self, interval_ms: int = 20) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        self._mode = "indeterminate"
        self._step_indeterminate(interval_ms)

    def stop(self) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        self._mode = "determinate"
        self._redraw()

    def _step_indeterminate(self, interval_ms: int) -> None:
        if not self.winfo_exists() or self._mode != "indeterminate":
            return
        self._ind_pos = (self._ind_pos + 0.025) % 1.0
        self._redraw()
        self._anim_job = self.after(interval_ms, lambda: self._step_indeterminate(interval_ms))

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        r = h // 2

        self._track_img = create_rounded_rect_image(
            w,
            h,
            r,
            fill_hex=p.surface_alt,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._track_img, anchor="nw")

        accent = p.role_color(self._role)

        if self._mode == "indeterminate":
            bar_w = max(24, int(w * 0.32))
            travel = w + bar_w
            x1 = int(self._ind_pos * travel) - bar_w
            clip_x1 = max(0, x1)
            clip_x2 = min(w, x1 + bar_w)
            vis_w = clip_x2 - clip_x1
            if vis_w > 4:
                self._bar_img = create_rounded_rect_image(
                    vis_w,
                    h,
                    r,
                    fill_hex=accent,
                    bg_hex=p.surface_alt,
                )
                self.create_image(clip_x1, 0, image=self._bar_img, anchor="nw")
        else:
            ratio = max(0.0, min(1.0, self._value / self._maximum))
            bar_w = int(round(w * ratio))
            if bar_w > 2:
                self._bar_img = create_rounded_rect_image(
                    max(h, bar_w),
                    h,
                    r,
                    fill_hex=accent,
                    bg_hex=p.surface_alt,
                )
                self.create_image(0, 0, image=self._bar_img, anchor="nw")
            if self._show_percent:
                pct_str = f"{int(round(ratio * 100))}%"
                fg = p.role_text(self._role) if ratio > 0.52 else p.fg
                self.create_text(w // 2, h // 2, text=pct_str, fill=fg, font=self._font)


class ModernSlider(tk.Canvas, ThemedWidgetMixin):
    """Smooth modern slider with filled active track, circular thumb, and optional floating value bubble."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        value: float = 50.0,
        command: Optional[Callable[[float], None]] = None,
        bootstyle: str = "primary",
        show_value: bool = True,
        width: int = 240,
        height: int = 34,
        **kwargs,
    ) -> None:
        self._from = from_
        self._to = to if to > from_ else from_ + 1.0
        self._value = max(self._from, min(self._to, value))
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._show_value = show_value
        self._is_hovered = False
        self._is_dragging = False

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 1), weight="bold")

        self.bind("<Enter>", lambda e: self._set_state(hovered=True))
        self.bind("<Leave>", lambda e: self._set_state(hovered=False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get(self) -> float:
        return self._value

    def set(self, value: float, notify: bool = False) -> None:
        self._value = max(self._from, min(self._to, value))
        self._redraw()
        if notify and self._command is not None:
            self._command(self._value)

    def _set_state(self, hovered: bool) -> None:
        self._is_hovered = hovered
        self._redraw()

    def _update_from_x(self, x: int) -> None:
        w = max(self.winfo_width(), int(self["width"]))
        pad_left = 14
        pad_right = 46 if self._show_value else 14
        usable = max(10, w - pad_left - pad_right)
        ratio = max(0.0, min(1.0, (x - pad_left) / usable))
        new_val = self._from + ratio * (self._to - self._from)
        self.set(new_val, notify=True)

    def _on_press(self, e: tk.Event) -> None:
        self.focus_set()
        self._is_dragging = True
        self._update_from_x(e.x)

    def _on_drag(self, e: tk.Event) -> None:
        if self._is_dragging:
            self._update_from_x(e.x)

    def _on_release(self, _e: tk.Event) -> None:
        self._is_dragging = False
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
        cy = h // 2

        pad_left = 14
        pad_right = 46 if self._show_value else 14
        usable = max(16, w - pad_left - pad_right)
        track_h = 6

        self._track_img = create_rounded_rect_image(
            usable,
            track_h,
            track_h // 2,
            fill_hex=p.surface_alt,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(pad_left, cy - track_h // 2, image=self._track_img, anchor="nw")

        ratio = (self._value - self._from) / (self._to - self._from)
        active_w = int(round(usable * ratio))
        accent = p.role_hover(self._role) if (self._is_hovered or self._is_dragging) else p.role_color(self._role)

        if active_w > 2:
            self._active_img = create_rounded_rect_image(
                max(track_h, active_w),
                track_h,
                track_h // 2,
                fill_hex=accent,
                bg_hex=parent_bg,
            )
            self.create_image(pad_left, cy - track_h // 2, image=self._active_img, anchor="nw")

        # Thumb (Fluent style outer accent ring + inner center circle)
        thumb_d = 20 if (self._is_hovered or self._is_dragging) else 18
        tx = pad_left + active_w - thumb_d // 2
        ty = cy - thumb_d // 2

        self._thumb_outer = create_circle_image(
            thumb_d,
            fill_hex=accent,
            bg_hex=parent_bg,
        )
        self.create_image(tx, ty, image=self._thumb_outer, anchor="nw")

        inner_d = 8 if self._is_dragging else 10
        ipad = (thumb_d - inner_d) // 2
        self._thumb_inner = create_circle_image(
            inner_d,
            fill_hex=p.surface,
            bg_hex=accent,
        )
        self.create_image(tx + ipad, ty + ipad, image=self._thumb_inner, anchor="nw")

        if self._show_value:
            val_str = str(int(round(self._value)))
            self.create_text(w - 6, cy, text=val_str, fill=p.fg_muted, font=self._font, anchor="e")


class ModernToast:
    """Non-blocking modern toast notification banner anchored to the bottom-right of the window."""

    _active_toasts: list[tk.Toplevel] = []

    @classmethod
    def show(
        cls,
        master: Optional[tk.Misc] = None,
        title: str = "Notification",
        message: str = "",
        bootstyle: str = "primary",
        duration_ms: int = 3200,
    ) -> tk.Toplevel:
        from ..style import ThemeManager
        root = master.winfo_toplevel() if master is not None else tk._default_root
        p = ThemeManager.instance().palette
        role = bootstyle.split("-")[0] if bootstyle else "primary"
        accent = p.role_color(role)

        icons = {
            "primary": "ℹ",
            "info": "ℹ",
            "success": "✔",
            "warning": "⚠",
            "danger": "✖",
        }
        icon_char = icons.get(role, "✦")

        win = tk.Toplevel(root)
        win.wm_overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=accent, padx=2, pady=2)

        body = tk.Frame(win, bg=p.surface, padx=14, pady=10)
        body.pack(fill="both", expand=True)

        icon_lbl = tk.Label(
            body,
            text=icon_char,
            bg=p.surface,
            fg=accent,
            font=(p.font_family, p.font_size + 4, "bold"),
        )
        icon_lbl.pack(side="left", padx=(0, 12))

        text_frame = tk.Frame(body, bg=p.surface)
        text_frame.pack(side="left", fill="both", expand=True)

        tk.Label(
            text_frame,
            text=title,
            bg=p.surface,
            fg=p.fg,
            font=(p.font_family, p.font_size, "bold"),
            anchor="w",
        ).pack(fill="x")

        if message:
            tk.Label(
                text_frame,
                text=message,
                bg=p.surface,
                fg=p.fg_muted,
                font=(p.font_family, p.font_size - 1),
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

        close_lbl = tk.Label(
            body,
            text="✕",
            bg=p.surface,
            fg=p.fg_muted,
            font=(p.font_family, p.font_size),
            cursor="hand2",
            padx=6,
        )
        close_lbl.pack(side="right", anchor="n")

        def _dismiss() -> None:
            if win in cls._active_toasts:
                cls._active_toasts.remove(win)
            if win.winfo_exists():
                win.destroy()

        close_lbl.bind("<ButtonRelease-1>", lambda e: _dismiss())

        win.update_idletasks()
        tw = max(290, win.winfo_reqwidth())
        th = win.winfo_reqheight()

        cls._active_toasts = [t for t in cls._active_toasts if t.winfo_exists()]
        idx = len(cls._active_toasts)
        cls._active_toasts.append(win)

        if root is not None and root.winfo_exists():
            rx = root.winfo_rootx() + root.winfo_width() - tw - 24
            ry = root.winfo_rooty() + root.winfo_height() - (th + 12) * (idx + 1) - 16
        else:
            rx, ry = 100, 100

        win.geometry(f"{tw}x{th}+{rx}+{ry}")
        if duration_ms > 0:
            win.after(duration_ms, _dismiss)
        return win


class ModernDialog(tk.Toplevel):
    """Modern themed modal dialog with customizable title, message, semantic action buttons, and result return."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Confirm Action",
        message: str = "Are you sure you want to proceed?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        bootstyle: str = "primary",
    ) -> None:
        super().__init__(master)
        from ..style import ThemeManager
        p = ThemeManager.instance().palette
        self.result: bool = False

        self.title(title)
        self.configure(bg=p.surface)
        self.resizable(False, False)
        if master is not None:
            self.transient(master.winfo_toplevel())
        ThemeManager. _apply_windows_titlebar_mode(self, p.mode == "dark")

        container = tk.Frame(self, bg=p.surface, padx=24, pady=20)
        container.pack(fill="both", expand=True)
        container.surface_color = p.surface  # type: ignore[attr-defined]

        tk.Label(
            container,
            text=title,
            bg=p.surface,
            fg=p.fg,
            font=(p.font_family, p.font_size + 3, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            container,
            text=message,
            bg=p.surface,
            fg=p.fg_muted,
            font=(p.font_family, p.font_size),
            wraplength=360,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(8, 20))

        btn_bar = tk.Frame(container, bg=p.surface)
        btn_bar.pack(fill="x")
        btn_bar.surface_color = p.surface  # type: ignore[attr-defined]

        ModernButton(
            btn_bar,
            text=confirm_text,
            bootstyle=bootstyle,
            command=self._on_confirm,
        ).pack(side="right", padx=(8, 0))

        ModernButton(
            btn_bar,
            text=cancel_text,
            bootstyle="secondary",
            variant="outline",
            command=self._on_cancel,
        ).pack(side="right")

        self.update_idletasks()
        w = max(380, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        if master is not None and master.winfo_exists():
            root = master.winfo_toplevel()
            x = root.winfo_rootx() + (root.winfo_width() - w) // 2
            y = root.winfo_rooty() + (root.winfo_height() - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        self.grab_set()

    def _on_confirm(self) -> None:
        self.result = True
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = False
        self.destroy()

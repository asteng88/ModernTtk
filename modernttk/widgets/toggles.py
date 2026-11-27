"""Modern animated toggle switches, rounded checkboxes, and radio buttons for ModernTtk."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Any, Callable, Optional

from ..themes import ThemePalette
from ..utils import (
    blend_colors,
    create_checkbox_image,
    create_circle_image,
    create_rounded_rect_image,
)
from .base import ThemedWidgetMixin


class ModernSwitch(tk.Canvas, ThemedWidgetMixin):
    """Animated pill toggle switch inspired by Windows 11 Fluent Design & Bootstrap switches."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variable: Optional[tk.BooleanVar] = None,
        onvalue: bool = True,
        offvalue: bool = False,
        command: Optional[Callable[[], None]] = None,
        bootstyle: str = "primary",
        state: str = "normal",
        **kwargs,
    ) -> None:
        self._text = text
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._command = command
        self._variable = variable if variable is not None else tk.BooleanVar(value=False)
        if isinstance(self._variable, tk.IntVar) and onvalue is True and offvalue is False:
            self._onvalue = 1
            self._offvalue = 0
        else:
            self._onvalue = onvalue
            self._offvalue = offvalue
        self._state = state

        self._track_w = 42
        self._track_h = 22
        self._progress = 1.0 if bool(self._variable.get()) else 0.0
        self._is_hovered = False
        self._is_pressed = False
        self._anim_job: Optional[str] = None

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        text_w = (self._font.measure(text) + 12) if text else 0
        total_w = self._track_w + text_w + 4
        total_h = max(28, self._track_h + 6)

        super().__init__(
            master,
            width=total_w,
            height=total_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if state == "normal" else "arrow",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        self._trace_id = self._variable.trace_add("write", self._on_var_changed)
        self.bind("<Destroy>", self._on_cleanup, add="+")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Key-space>", lambda e: self.toggle())

        self._redraw()

    def get(self) -> bool:
        return bool(self._variable.get())

    def set(self, value: bool) -> None:
        self._variable.set(value)

    def toggle(self) -> None:
        if self._state == "disabled":
            return
        new_val = self._offvalue if self.get() == bool(self._onvalue) else self._onvalue
        self._variable.set(new_val)
        if self._command is not None:
            self._command()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            text_w = (self._font.measure(self._text) + 12) if self._text else 0
            super().configure(width=self._track_w + text_w + 4)
        if "state" in kwargs:
            self._state = str(kwargs.pop("state"))
            super().configure(cursor="hand2" if self._state == "normal" else "arrow")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "bootstyle" in kwargs:
            self._role = str(kwargs.pop("bootstyle")).split("-")[0]
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

    def _on_var_changed(self, *_args: Any) -> None:
        target = 1.0 if self.get() == self._onvalue else 0.0
        self._animate_to(target)

    def _animate_to(self, target: float) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        diff = target - self._progress
        if abs(diff) <= 0.14:
            self._progress = target
            self._redraw()
            return

        self._progress += diff * 0.42
        self._redraw()
        self._anim_job = self.after(14, lambda: self._animate_to(target))

    def _on_enter(self, _e: tk.Event) -> None:
        if self._state != "disabled":
            self._is_hovered = True
            self._redraw()

    def _on_leave(self, _e: tk.Event) -> None:
        self._is_hovered = False
        self._is_pressed = False
        self._redraw()

    def _on_press(self, _e: tk.Event) -> None:
        if self._state != "disabled":
            self.focus_set()
            self._is_pressed = True
            self._redraw()

    def _on_release(self, e: tk.Event) -> None:
        if self._state != "disabled" and self._is_pressed:
            self._is_pressed = False
            if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
                self.toggle()
            else:
                self._redraw()

    def _on_cleanup(self, e: tk.Event) -> None:
        if e.widget is self and self._trace_id:
            try:
                self._variable.trace_remove("write", self._trace_id)
            except tk.TclError:
                pass

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        h = max(self.winfo_height(), int(self["height"]))
        ty = (h - self._track_h) // 2

        role_col = p.role_hover(self._role) if self._is_hovered else p.role_color(self._role)
        off_fill = p.surface_hover if self._is_hovered else p.surface_alt
        track_fill = blend_colors(off_fill, role_col, self._progress)
        track_border = blend_colors(p.border_strong, role_col, self._progress)

        self._track_img = create_rounded_rect_image(
            self._track_w,
            self._track_h,
            self._track_h // 2,
            fill_hex=track_fill,
            border_hex=track_border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(2, ty, image=self._track_img, anchor="nw")

        # Thumb geometry (expands slightly when pressed or hovered like Windows 11 Fluent)
        thumb_d = 16 if (self._is_hovered or self._is_pressed) else 14
        pad = (self._track_h - thumb_d) // 2
        min_x = 2 + pad
        max_x = 2 + self._track_w - thumb_d - pad
        tx = int(round(min_x + (max_x - min_x) * self._progress))
        thumb_y = ty + pad

        off_thumb = p.fg_muted if p.mode == "light" else p.fg
        on_thumb = p.role_text(self._role)
        thumb_color = blend_colors(off_thumb, on_thumb, self._progress)

        self._thumb_img = create_circle_image(
            thumb_d,
            fill_hex=thumb_color,
            bg_hex=track_fill,
        )
        self.create_image(tx, thumb_y, image=self._thumb_img, anchor="nw")

        if self._text:
            self.create_text(
                self._track_w + 12,
                h // 2,
                text=self._text,
                fill=p.fg_subtle if self._state == "disabled" else p.fg,
                font=self._font,
                anchor="w",
            )


class ModernCheckbox(tk.Canvas, ThemedWidgetMixin):
    """Animated rounded checkbox with smooth checkmark draw-in and indeterminate state."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[], None]] = None,
        bootstyle: str = "primary",
        indeterminate: bool = False,
        state: str = "normal",
        **kwargs,
    ) -> None:
        self._text = text
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._command = command
        self._indeterminate = indeterminate
        self._state = state
        self._variable = variable if variable is not None else tk.BooleanVar(value=False)

        self._box_size = 20
        self._progress = 1.0 if (bool(self._variable.get()) or indeterminate) else 0.0
        self._is_hovered = False
        self._anim_job: Optional[str] = None

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        text_w = (self._font.measure(text) + 10) if text else 0
        total_w = self._box_size + text_w + 6
        total_h = 28

        super().__init__(
            master,
            width=total_w,
            height=total_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if state == "normal" else "arrow",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        self._trace_id = self._variable.trace_add("write", self._on_var_changed)
        self.bind("<Destroy>", self._on_cleanup, add="+")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Key-space>", lambda e: self.toggle())

        self._redraw()

    def get(self) -> bool:
        return bool(self._variable.get())

    def set(self, value: bool) -> None:
        self._indeterminate = False
        self._variable.set(value)

    def set_indeterminate(self, active: bool = True) -> None:
        self._indeterminate = active
        self._animate_to(1.0 if (active or self.get()) else 0.0)

    def toggle(self) -> None:
        if self._state == "disabled":
            return
        self._indeterminate = False
        new_bool = not self.get()
        if isinstance(self._variable, tk.IntVar):
            self._variable.set(1 if new_bool else 0)
        else:
            self._variable.set(new_bool)
        if self._command is not None:
            self._command()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            text_w = (self._font.measure(self._text) + 10) if self._text else 0
            super().configure(width=self._box_size + text_w + 6)
        if "state" in kwargs:
            self._state = str(kwargs.pop("state"))
            super().configure(cursor="hand2" if self._state == "normal" else "arrow")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "bootstyle" in kwargs:
            self._role = str(kwargs.pop("bootstyle")).split("-")[0]
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

    def _on_var_changed(self, *_args: Any) -> None:
        target = 1.0 if (self.get() or self._indeterminate) else 0.0
        self._animate_to(target)

    def _animate_to(self, target: float) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        diff = target - self._progress
        if abs(diff) <= 0.22:
            self._progress = target
            self._redraw()
            return

        self._progress += 0.25 if diff > 0 else -0.25
        self._redraw()
        self._anim_job = self.after(14, lambda: self._animate_to(target))

    def _on_enter(self, _e: tk.Event) -> None:
        if self._state != "disabled":
            self._is_hovered = True
            self._redraw()

    def _on_leave(self, _e: tk.Event) -> None:
        self._is_hovered = False
        self._redraw()

    def _on_click(self, e: tk.Event) -> None:
        if self._state != "disabled" and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.focus_set()
            self.toggle()

    def _on_cleanup(self, e: tk.Event) -> None:
        if e.widget is self and self._trace_id:
            try:
                self._variable.trace_remove("write", self._trace_id)
            except tk.TclError:
                pass

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        h = max(self.winfo_height(), int(self["height"]))
        by = (h - self._box_size) // 2

        role_col = p.role_hover(self._role) if self._is_hovered else p.role_color(self._role)
        off_fill = p.surface_hover if self._is_hovered else p.input_bg
        off_border = p.border_strong if self._is_hovered else p.input_border

        fill_hex = blend_colors(off_fill, role_col, self._progress)
        border_hex = blend_colors(off_border, role_col, self._progress)
        check_hex = p.role_text(self._role)

        self._box_img = create_checkbox_image(
            self._box_size,
            radius=5,
            fill_hex=fill_hex,
            border_hex=border_hex,
            border_width=1,
            check_hex=check_hex,
            check_progress=self._progress,
            indeterminate=self._indeterminate,
            bg_hex=parent_bg,
        )
        self.create_image(2, by, image=self._box_img, anchor="nw")

        if self._text:
            self.create_text(
                self._box_size + 10,
                h // 2,
                text=self._text,
                fill=p.fg_subtle if self._state == "disabled" else p.fg,
                font=self._font,
                anchor="w",
            )


class ModernRadioButton(tk.Canvas, ThemedWidgetMixin):
    """Modern circular radio button with animated inner indicator."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variable: Optional[tk.Variable] = None,
        value: Any = 1,
        command: Optional[Callable[[], None]] = None,
        bootstyle: str = "primary",
        state: str = "normal",
        **kwargs,
    ) -> None:
        self._text = text
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._value = value
        self._command = command
        self._state = state
        self._variable = variable if variable is not None else tk.StringVar(value="")

        self._size = 20
        self._is_hovered = False

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        text_w = (self._font.measure(text) + 10) if text else 0
        total_w = self._size + text_w + 6
        total_h = 28

        super().__init__(
            master,
            width=total_w,
            height=total_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if state == "normal" else "arrow",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        self._trace_id = self._variable.trace_add("write", lambda *_: self._redraw())
        self.bind("<Destroy>", self._on_cleanup, add="+")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Key-space>", lambda e: self.select())

        self._redraw()

    def is_selected(self) -> bool:
        try:
            return str(self._variable.get()) == str(self._value)
        except tk.TclError:
            return False

    def select(self) -> None:
        if self._state == "disabled":
            return
        self._variable.set(self._value)
        if self._command is not None:
            self._command()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            text_w = (self._font.measure(self._text) + 10) if self._text else 0
            super().configure(width=self._size + text_w + 6)
        if "state" in kwargs:
            self._state = str(kwargs.pop("state"))
            super().configure(cursor="hand2" if self._state == "normal" else "arrow")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "bootstyle" in kwargs:
            self._role = str(kwargs.pop("bootstyle")).split("-")[0]
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

    def _on_enter(self, _e: tk.Event) -> None:
        if self._state != "disabled":
            self._is_hovered = True
            self._redraw()

    def _on_leave(self, _e: tk.Event) -> None:
        self._is_hovered = False
        self._redraw()

    def _on_click(self, e: tk.Event) -> None:
        if self._state != "disabled" and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.focus_set()
            self.select()

    def _on_cleanup(self, e: tk.Event) -> None:
        if e.widget is self and self._trace_id:
            try:
                self._variable.trace_remove("write", self._trace_id)
            except tk.TclError:
                pass

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        h = max(self.winfo_height(), int(self["height"]))
        ry = (h - self._size) // 2
        selected = self.is_selected()
        role_col = p.role_hover(self._role) if self._is_hovered else p.role_color(self._role)

        if selected:
            self._outer_img = create_circle_image(
                self._size,
                fill_hex=role_col,
                border_hex=role_col,
                border_width=1,
                bg_hex=parent_bg,
            )
            self.create_image(2, ry, image=self._outer_img, anchor="nw")
            dot_d = 8 if not self._is_hovered else 10
            pad = (self._size - dot_d) // 2
            self._inner_img = create_circle_image(
                dot_d,
                fill_hex=p.role_text(self._role),
                bg_hex=role_col,
            )
            self.create_image(2 + pad, ry + pad, image=self._inner_img, anchor="nw")
        else:
            fill_hex = p.surface_hover if self._is_hovered else p.input_bg
            border_hex = p.border_strong if self._is_hovered else p.input_border
            self._outer_img = create_circle_image(
                self._size,
                fill_hex=fill_hex,
                border_hex=border_hex,
                border_width=1,
                bg_hex=parent_bg,
            )
            self.create_image(2, ry, image=self._outer_img, anchor="nw")

        if self._text:
            self.create_text(
                self._size + 10,
                h // 2,
                text=self._text,
                fill=p.fg_subtle if self._state == "disabled" else p.fg,
                font=self._font,
                anchor="w",
            )

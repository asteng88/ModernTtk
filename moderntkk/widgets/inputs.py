"""Modern rounded input widgets: ModernEntry, ModernSearchBar, ModernPasswordEntry, ModernCombobox, ModernSpinbox."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, List, Optional, Sequence

from ..icons import AVAILABLE_ICONS, create_icon_image
from ..themes import ThemePalette
from ..utils import create_rounded_rect_image
from .base import ThemedWidgetMixin


class ModernEntry(tk.Canvas, ThemedWidgetMixin):
    """Anti-aliased rounded text input with placeholder, prefix/suffix icons, and Windows 11 focus accent."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "",
        textvariable: Optional[tk.StringVar] = None,
        width: int = 240,
        height: int = 38,
        radius: Optional[int] = None,
        bootstyle: str = "primary",
        prefix_icon: Optional[str] = None,
        suffix_icon: Optional[str] = None,
        on_suffix_click: Optional[Callable[[], None]] = None,
        show: str = "",
        state: str = "normal",
        **kwargs,
    ) -> None:
        self._placeholder = placeholder
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._custom_radius = radius
        self._prefix_icon = prefix_icon
        self._suffix_icon = suffix_icon
        self._on_suffix_click = on_suffix_click
        self._real_show = show
        self._state = state
        self._is_focused = False
        self._is_hovered = False
        self._showing_placeholder = False
        self._base_height = height
        self._val_state: Optional[str] = None
        self._val_msg: str = ""

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
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        self._caption_font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        self._var = textvariable if textvariable is not None else tk.StringVar()
        self._entry = tk.Entry(
            self,
            textvariable=self._var,
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=self._font,
            state=state,
        )
        self._entry_win = self.create_window(12, height // 2, window=self._entry, anchor="w")

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Enter>", self._on_enter)
        self._entry.bind("<Leave>", self._on_leave)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_canvas_click)
        self.bind("<Configure>", lambda e: self._redraw())

        if not self._var.get() and self._placeholder:
            self._activate_placeholder()
        else:
            if self._real_show:
                self._entry.configure(show=self._real_show)

        self._redraw()

    @property
    def entry(self) -> tk.Entry:
        """Underlying tk.Entry widget for custom key bindings."""
        return self._entry

    def get(self) -> str:
        if self._showing_placeholder:
            return ""
        return self._entry.get()

    def set(self, value: str) -> None:
        if self._showing_placeholder:
            self._deactivate_placeholder()
        self._var.set(value)
        if not value and not self._is_focused and self._placeholder:
            self._activate_placeholder()
        self._redraw()

    def clear(self) -> None:
        self.set("")

    def set_validation(self, state: Optional[str] = None, message: str = "") -> None:
        """Set or clear a semantic validation state ('error'/'danger', 'warning', 'success', 'info', or None)."""
        if state:
            norm = state.lower().strip()
            self._val_state = "danger" if norm == "error" else norm
            self._val_msg = message
        else:
            self._val_state = None
            self._val_msg = ""
        target_h = self._base_height + (20 if (self._val_state and self._val_msg) else 0)
        super().configure(height=target_h)
        self._redraw()

    def _activate_placeholder(self) -> None:
        if not self._placeholder:
            return
        self._showing_placeholder = True
        self._entry.configure(show="", fg=self.palette.fg_subtle)
        self._var.set(self._placeholder)

    def _deactivate_placeholder(self) -> None:
        if not self._showing_placeholder:
            return
        self._showing_placeholder = False
        if self._var.get() == self._placeholder:
            self._var.set("")
        self._entry.configure(show=self._real_show, fg=self.palette.input_fg)

    def _on_focus_in(self, _e: tk.Event) -> None:
        self._is_focused = True
        if self._showing_placeholder:
            self._deactivate_placeholder()
        self._redraw()

    def _on_focus_out(self, _e: tk.Event) -> None:
        self._is_focused = False
        if not self._var.get() and self._placeholder:
            self._activate_placeholder()
        self._redraw()

    def _on_enter(self, _e: tk.Event) -> None:
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, _e: tk.Event) -> None:
        self._is_hovered = False
        self._redraw()

    def _on_canvas_click(self, e: tk.Event) -> None:
        w = max(self.winfo_width(), int(self["width"]))
        if self._suffix_icon and self._on_suffix_click and e.x >= w - 34:
            self._on_suffix_click()
            return
        self._entry.focus_set()

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("bg_img")
        self.delete("icon_item")
        self.delete("val_item")

        w = max(self.winfo_width(), int(self["width"]))
        box_h = self._base_height
        r = self._custom_radius if self._custom_radius is not None else p.radius_md

        accent = p.role_color(self._val_state if self._val_state else self._role)
        if self._val_state:
            border_col = accent
            bottom_col = accent
            border_w = 2 if (self._is_focused or self._val_state in ("danger", "warning")) else 1
        else:
            border_col = accent if self._is_focused else (p.border_strong if self._is_hovered else p.input_border)
            bottom_col = accent if self._is_focused else p.border_strong
            border_w = 2 if self._is_focused else 1

        self._bg_img = create_rounded_rect_image(
            w,
            box_h,
            r,
            fill_hex=p.input_bg,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
            bottom_border_hex=bottom_col,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw", tags="bg_img")
        self.tag_lower("bg_img")

        left_pad = 12
        right_pad = 12

        if self._prefix_icon:
            ic_col = accent if (self._is_focused or self._val_state) else p.fg_muted
            if self._prefix_icon.lower().strip() in AVAILABLE_ICONS:
                self._pref_img = create_icon_image(self._prefix_icon, size=15, color=ic_col)
                self.create_image(14, box_h // 2, image=self._pref_img, anchor="w", tags="icon_item")
            else:
                self.create_text(
                    14,
                    box_h // 2,
                    text=self._prefix_icon,
                    fill=ic_col,
                    font=self._font,
                    anchor="w",
                    tags="icon_item",
                )
            left_pad = 36

        if self._suffix_icon:
            ic_col = accent if (self._is_focused or self._val_state) else p.fg_muted
            if self._suffix_icon.lower().strip() in AVAILABLE_ICONS:
                self._suff_img = create_icon_image(self._suffix_icon, size=15, color=ic_col)
                self.create_image(w - 14, box_h // 2, image=self._suff_img, anchor="e", tags="icon_item")
            else:
                self.create_text(
                    w - 14,
                    box_h // 2,
                    text=self._suffix_icon,
                    fill=ic_col,
                    font=self._font,
                    anchor="e",
                    tags="icon_item",
                )
            right_pad = 36
        elif self._val_state:
            val_glyphs = {"danger": "✖", "warning": "⚠", "success": "✔", "info": "ℹ"}
            glyph = val_glyphs.get(self._val_state, "●")
            self.create_text(
                w - 14,
                box_h // 2,
                text=glyph,
                fill=accent,
                font=self._font,
                anchor="e",
                tags="val_item",
            )
            right_pad = 34

        if self._val_state and self._val_msg:
            self.create_text(
                6,
                box_h + 10,
                text=self._val_msg,
                fill=accent,
                font=self._caption_font,
                anchor="w",
                tags="val_item",
            )

        self._entry.configure(
            bg=p.input_bg,
            fg=p.fg_subtle if self._showing_placeholder else p.input_fg,
            insertbackground=p.fg,
            selectbackground=accent,
            selectforeground=p.role_text(self._role),
        )
        self.coords(self._entry_win, left_pad, box_h // 2)
        self.itemconfigure(self._entry_win, width=max(30, w - left_pad - right_pad))


class ModernSearchBar(ModernEntry):
    """Rounded search input with magnifying glass icon, clear button, and Enter/search callback."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "Search...",
        on_search: Optional[Callable[[str], None]] = None,
        width: int = 260,
        height: int = 38,
        bootstyle: str = "primary",
        **kwargs,
    ) -> None:
        self._on_search = on_search
        super().__init__(
            master,
            placeholder=placeholder,
            width=width,
            height=height,
            bootstyle=bootstyle,
            prefix_icon="🔍",
            suffix_icon="✕",
            on_suffix_click=self._clear_and_notify,
            **kwargs,
        )
        self.entry.bind("<Return>", lambda e: self._trigger_search())
        self.entry.bind("<KeyRelease>", lambda e: self._on_key())

    def _on_key(self) -> None:
        if self._on_search is not None:
            self._on_search(self.get())

    def _clear_and_notify(self) -> None:
        self.clear()
        if self._on_search is not None:
            self._on_search("")

    def _trigger_search(self) -> None:
        if self._on_search is not None:
            self._on_search(self.get())


class ModernPasswordEntry(ModernEntry):
    """Rounded password input with clickable eye icon to toggle visibility."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "Enter password...",
        width: int = 240,
        height: int = 38,
        bootstyle: str = "primary",
        **kwargs,
    ) -> None:
        self._revealed = False
        super().__init__(
            master,
            placeholder=placeholder,
            width=width,
            height=height,
            bootstyle=bootstyle,
            prefix_icon="🔒",
            suffix_icon="👁",
            on_suffix_click=self.toggle_visibility,
            show="•",
            **kwargs,
        )

    def toggle_visibility(self) -> None:
        self._revealed = not self._revealed
        self._real_show = "" if self._revealed else "•"
        self._suffix_icon = "🙈" if self._revealed else "👁"
        if not self._showing_placeholder:
            self.entry.configure(show=self._real_show)
        self._redraw()


class ModernCombobox(tk.Canvas, ThemedWidgetMixin):
    """Modern rounded dropdown / combobox with a themed popup menu."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Sequence[str] = (),
        default: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        width: int = 200,
        height: int = 38,
        bootstyle: str = "primary",
        **kwargs,
    ) -> None:
        self._values: List[str] = list(values)
        self._selected = default if default is not None else (self._values[0] if self._values else "")
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._is_hovered = False
        self._popup: Optional[tk.Toplevel] = None
        self._base_height = height
        self._val_state: Optional[str] = None
        self._val_msg: str = ""

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
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        self._caption_font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._toggle_popup())
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get(self) -> str:
        return self._selected

    def set(self, value: str, notify: bool = False) -> None:
        self._selected = value
        self._redraw()
        if notify and self._command is not None:
            self._command(value)

    def set_values(self, values: Sequence[str]) -> None:
        self._values = list(values)
        if self._selected not in self._values and self._values:
            self._selected = self._values[0]
        self._redraw()

    def set_validation(self, state: Optional[str] = None, message: str = "") -> None:
        """Set or clear a semantic validation state ('error'/'danger', 'warning', 'success', 'info', or None)."""
        if state:
            norm = state.lower().strip()
            self._val_state = "danger" if norm == "error" else norm
            self._val_msg = message
        else:
            self._val_state = None
            self._val_msg = ""
        target_h = self._base_height + (20 if (self._val_state and self._val_msg) else 0)
        super().configure(height=target_h)
        self._redraw()

    def _set_hover(self, hovered: bool) -> None:
        self._is_hovered = hovered
        self._redraw()

    def _toggle_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
            return

        if not self._values:
            return

        p = self.palette
        w = max(self.winfo_width(), int(self["width"]))
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        pop = tk.Toplevel(self)
        pop.wm_overrideredirect(True)
        pop.configure(bg=p.border_strong, padx=1, pady=1)
        self._popup = pop

        inner = tk.Frame(pop, bg=p.surface, padx=4, pady=4)
        inner.pack(fill="both", expand=True)

        for val in self._values:
            is_sel = val == self._selected
            row = tk.Label(
                inner,
                text=f"  {val}",
                anchor="w",
                bg=p.role_subtle_bg(self._role) if is_sel else p.surface,
                fg=p.role_color(self._role) if is_sel else p.fg,
                font=self._font,
                padx=8,
                pady=6,
                cursor="hand2",
            )
            row.pack(fill="x", pady=1)

            def on_enter(ev, lbl=row, sel=is_sel):
                if not sel:
                    lbl.configure(bg=p.surface_hover)

            def on_leave(ev, lbl=row, sel=is_sel):
                if not sel:
                    lbl.configure(bg=p.surface)

            def on_pick(ev, v=val):
                if self._popup and self._popup.winfo_exists():
                    self._popup.destroy()
                self._popup = None
                self.set(v, notify=True)

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<ButtonRelease-1>", on_pick)

        pop.update_idletasks()
        pop_h = pop.winfo_reqheight()
        pop.geometry(f"{w}x{pop_h}+{x}+{y}")
        pop.focus_force()
        pop.bind("<FocusOut>", lambda e: pop.destroy())
        pop.bind("<Escape>", lambda e: pop.destroy())

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        box_h = self._base_height
        r = p.radius_md

        accent = p.role_color(self._val_state if self._val_state else self._role)
        border_col = accent if (self._is_hovered or self._val_state) else p.input_border
        border_w = 2 if (self._val_state in ("danger", "warning")) else 1
        fill_col = p.surface_hover if self._is_hovered else p.input_bg

        self._bg_img = create_rounded_rect_image(
            w,
            box_h,
            r,
            fill_hex=fill_col,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
            bottom_border_hex=accent if self._val_state else p.border_strong,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw")

        self.create_text(
            14,
            box_h // 2,
            text=self._selected,
            fill=p.input_fg,
            font=self._font,
            anchor="w",
        )
        self.create_text(
            w - 14,
            box_h // 2,
            text="▾",
            fill=accent if self._val_state else p.fg_muted,
            font=self._font,
            anchor="e",
        )
        if self._val_state and self._val_msg:
            self.create_text(
                6,
                box_h + 10,
                text=self._val_msg,
                fill=accent,
                font=self._caption_font,
                anchor="w",
            )


class ModernSpinbox(tk.Canvas, ThemedWidgetMixin):
    """Modern rounded numeric spinbox with integrated '-' and '+' steppers."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0,
        to: float = 100,
        step: float = 1,
        value: float = 0,
        command: Optional[Callable[[float], None]] = None,
        width: int = 136,
        height: int = 38,
        bootstyle: str = "primary",
        **kwargs,
    ) -> None:
        self._from = from_
        self._to = to
        self._step = step
        self._val = value
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._hover_zone: Optional[str] = None  # "minus", "plus", or None

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
        self._font = tkfont.Font(family=p.font_family, size=p.font_size, weight="bold")

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_zone(None))
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Up>", lambda e: self.increment())
        self.bind("<Down>", lambda e: self.decrement())
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get(self) -> float:
        return self._val

    def set(self, value: float, notify: bool = False) -> None:
        self._val = max(self._from, min(self._to, value))
        self._redraw()
        if notify and self._command is not None:
            self._command(self._val)

    def increment(self) -> None:
        self.set(self._val + self._step, notify=True)

    def decrement(self) -> None:
        self.set(self._val - self._step, notify=True)

    def _on_motion(self, e: tk.Event) -> None:
        w = max(self.winfo_width(), int(self["width"]))
        if e.x <= 36:
            self._set_zone("minus")
        elif e.x >= w - 36:
            self._set_zone("plus")
        else:
            self._set_zone(None)

    def _set_zone(self, zone: Optional[str]) -> None:
        if self._hover_zone != zone:
            self._hover_zone = zone
            self._redraw()

    def _on_click(self, e: tk.Event) -> None:
        self.focus_set()
        w = max(self.winfo_width(), int(self["width"]))
        if e.x <= 36:
            self.decrement()
        elif e.x >= w - 36:
            self.increment()

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        r = p.radius_md

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            r,
            fill_hex=p.input_bg,
            border_hex=p.input_border,
            border_width=1,
            bg_hex=parent_bg,
            bottom_border_hex=p.border_strong,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw")

        accent = p.role_color(self._role)
        # Dividers
        self.create_line(36, 7, 36, h - 7, fill=p.divider, width=1)
        self.create_line(w - 36, 7, w - 36, h - 7, fill=p.divider, width=1)

        # Minus / Plus buttons
        minus_col = accent if self._hover_zone == "minus" else p.fg_muted
        plus_col = accent if self._hover_zone == "plus" else p.fg_muted
        self.create_text(18, h // 2, text="−", fill=minus_col, font=self._font)
        self.create_text(w - 18, h // 2, text="+", fill=plus_col, font=self._font)

        # Value display
        val_str = str(int(self._val)) if float(self._val).is_integer() else f"{self._val:.2f}"
        self.create_text(w // 2, h // 2, text=val_str, fill=p.input_fg, font=self._font)

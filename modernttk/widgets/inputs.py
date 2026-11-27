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
    """Modern rounded dropdown / combobox with a custom themed rounded listbox popup (`ttk.Combobox` drop-in compatible)."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Sequence[str] = (),
        default: Optional[str] = None,
        textvariable: Optional[tk.StringVar] = None,
        state: str = "readonly",
        command: Optional[Callable[[str], None]] = None,
        width: Optional[int] = None,
        height: int = 34,
        bootstyle: str = "primary",
        **kwargs,
    ) -> None:
        kwargs.pop("style", None)
        kwargs.pop("exportselection", None)
        kwargs.pop("justify", None)

        self._values: List[str] = [str(v) for v in values]
        self._textvariable = textvariable
        if default is not None:
            init_val = str(default)
        elif textvariable is not None:
            try:
                init_val = str(textvariable.get())
            except Exception:
                init_val = ""
        else:
            init_val = ""

        self._selected = init_val
        if self._textvariable is not None and init_val and not self._textvariable.get():
            try:
                self._textvariable.set(init_val)
            except Exception:
                pass

        self._state = state or "normal"
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._is_hovered = False
        self._is_focused = False
        self._popup: Optional[tk.Toplevel] = None
        self._base_height = height
        self._val_state: Optional[str] = None
        self._val_msg: str = ""
        self._trace_id: Optional[str] = None
        self._updating_var = False
        self._popup_imgs: List[tk.PhotoImage] = []

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)
        self._caption_font = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        if width is None:
            px_width = 180
        elif width <= 60:
            px_width = max(92, int(width * 7.5 + 42))
        else:
            px_width = int(width)

        super().__init__(
            master,
            width=px_width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if self._state == "readonly" else ("arrow" if self._state == "disabled" else "xterm"),
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        # Optional embedded Entry when state is "normal" (editable combobox)
        self._entry: Optional[tk.Entry] = None
        self._entry_win: Optional[int] = None
        self._sync_entry_mode()

        if self._textvariable is not None:
            self._trace_id = self._textvariable.trace_add("write", self._on_var_changed)
            self.bind("<Destroy>", self._on_cleanup_var, add="+")

        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._on_canvas_click)
        self.bind("<Down>", lambda e: self._toggle_popup())
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def _sync_entry_mode(self) -> None:
        p = self.palette
        if self._state == "normal":
            if self._entry is None:
                self._entry = tk.Entry(
                    self,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    font=self._font,
                    bg=p.input_bg,
                    fg=p.input_fg,
                    insertbackground=p.fg,
                )
                self._entry.insert(0, self._selected)
                self._entry.bind("<KeyRelease>", self._on_entry_key)
                self._entry.bind("<FocusIn>", lambda e: self._set_focus(True))
                self._entry.bind("<FocusOut>", lambda e: self._set_focus(False))
                self._entry.bind("<Down>", lambda e: self._toggle_popup())
                self._entry_win = self.create_window(12, self._base_height // 2, window=self._entry, anchor="w")
        else:
            if self._entry is not None:
                if self._entry_win is not None:
                    self.delete(self._entry_win)
                    self._entry_win = None
                self._entry.destroy()
                self._entry = None
        super().configure(
            cursor="hand2" if self._state == "readonly" else ("arrow" if self._state == "disabled" else "hand2")
        )

    def _on_entry_key(self, _e: tk.Event) -> None:
        if self._entry is not None:
            val = self._entry.get()
            self._selected = val
            if self._textvariable is not None:
                self._updating_var = True
                try:
                    self._textvariable.set(val)
                finally:
                    self._updating_var = False

    def _set_focus(self, focused: bool) -> None:
        self._is_focused = focused
        self._redraw()

    def _on_var_changed(self, *_args) -> None:
        if self._updating_var or self._textvariable is None:
            return
        try:
            new_val = str(self._textvariable.get())
        except Exception:
            return
        self._selected = new_val
        if self._entry is not None and self._entry.get() != new_val:
            self._entry.delete(0, "end")
            self._entry.insert(0, new_val)
        if self.winfo_exists():
            self._redraw()

    def _on_cleanup_var(self, e: tk.Event) -> None:
        if e.widget is self and self._textvariable is not None and self._trace_id:
            try:
                self._textvariable.trace_remove("write", self._trace_id)
            except Exception:
                pass

    def _on_canvas_click(self, e: tk.Event) -> None:
        if self._state == "disabled":
            return
        if self._state == "normal" and self._entry is not None:
            w = max(self.winfo_width(), int(self["width"]))
            if e.x < max(24, w - 32):
                self._entry.focus_set()
                return
        self._toggle_popup()

    def get(self) -> str:
        if self._entry is not None:
            return self._entry.get()
        if self._textvariable is not None:
            try:
                return str(self._textvariable.get())
            except Exception:
                pass
        return self._selected

    def set(self, value: str, notify: bool = False) -> None:
        val_str = "" if value is None else str(value)
        self._selected = val_str
        if self._entry is not None:
            self._entry.delete(0, "end")
            self._entry.insert(0, val_str)
        if self._textvariable is not None:
            self._updating_var = True
            try:
                self._textvariable.set(val_str)
            finally:
                self._updating_var = False
        if self.winfo_exists():
            self._redraw()
        if notify:
            if self._command is not None:
                self._command(val_str)
            try:
                self.event_generate("<<ComboboxSelected>>")
            except tk.TclError:
                pass

    def current(self, newindex: Optional[int] = None) -> int:
        """Get or set the selected index (`ttk.Combobox.current()` compatible)."""
        if newindex is not None:
            idx = int(newindex)
            if 0 <= idx < len(self._values):
                self.set(self._values[idx], notify=False)
                return idx
            return -1
        cur = self.get()
        return self._values.index(cur) if cur in self._values else -1

    def delete(self, first, last=None) -> None:  # type: ignore[override]
        """Support both `tk.Canvas.delete(tag)` and `ttk.Combobox.delete(0, tk.END)`."""
        if first == 0 and (last == "end" or last == tk.END or last is None):
            self.set("", notify=False)
            return
        if last is not None:
            super().delete(first, last)
        else:
            super().delete(first)

    def insert(self, index, string: str = "") -> None:  # type: ignore[override]
        """Support `entry.insert(0, text)` on comboboxes."""
        if index in (0, "0", "end", tk.END):
            cur = self.get()
            if index in (0, "0"):
                self.set(str(string) + cur, notify=False)
            else:
                self.set(cur + str(string), notify=False)

    def set_values(self, values: Sequence[str]) -> None:
        self._values = [str(v) for v in values]
        self._redraw()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        if "values" in kwargs:
            self._values = [str(v) for v in (kwargs.pop("values") or ())]
        if "state" in kwargs:
            self._state = str(kwargs.pop("state") or "normal")
            self._sync_entry_mode()
        if "textvariable" in kwargs:
            if self._textvariable is not None and self._trace_id:
                try:
                    self._textvariable.trace_remove("write", self._trace_id)
                except Exception:
                    pass
            self._textvariable = kwargs.pop("textvariable")
            if self._textvariable is not None:
                self._trace_id = self._textvariable.trace_add("write", self._on_var_changed)
                self._selected = str(self._textvariable.get())
        if "bootstyle" in kwargs:
            self._role = str(kwargs.pop("bootstyle")).split("-")[0]
        if "width" in kwargs:
            w_val = int(kwargs.pop("width"))
            kwargs["width"] = max(92, int(w_val * 7.5 + 42)) if w_val <= 60 else w_val
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "values":
            return tuple(self._values)
        if key == "state":
            return self._state
        if key == "textvariable":
            return str(self._textvariable) if self._textvariable else ""
        if key == "style":
            return "TCombobox"
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

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

    def _close_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            try:
                self._popup.destroy()
            except tk.TclError:
                pass
        self._popup = None
        if self.winfo_exists():
            self._redraw()

    def _toggle_popup(self) -> None:
        if self._state == "disabled":
            return
        if self._popup is not None and self._popup.winfo_exists():
            self._close_popup()
            return

        if not self._values:
            return

        p = self.palette
        base_w = max(self.winfo_width(), int(self["width"]))
        max_text_w = max((self._font.measure(str(v)) for v in self._values), default=80)
        w = max(base_w, min(480, max_text_w + 54))

        item_h = 32
        pad = 6
        max_vis = 8
        vis_count = min(len(self._values), max_vis)
        pop_h = vis_count * item_h + pad * 2
        total_content_h = len(self._values) * item_h + pad * 2

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self._base_height + 4
        from ..utils import get_monitor_work_area

        mon_left, mon_top, mon_right, mon_bottom = get_monitor_work_area(self, x=x, y=y)
        if x + w > mon_right - 8:
            x = max(mon_left + 8, mon_right - w - 8)
        elif x < mon_left + 8:
            x = mon_left + 8
        if y + pop_h > mon_bottom - 8:
            y = max(mon_top + 8, self.winfo_rooty() - pop_h - 4)

        pop = tk.Toplevel(self)
        pop.wm_overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=p.bg)
        self._popup = pop
        self._redraw()

        canvas = tk.Canvas(pop, width=w, height=pop_h, bg=p.bg, bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        cur_val = self.get()
        cur_idx = self._values.index(cur_val) if cur_val in self._values else -1
        initial_scroll = 0
        if cur_idx >= max_vis:
            initial_scroll = min(
                total_content_h - pop_h,
                max(0, (cur_idx - max_vis // 2) * item_h),
            )

        state = {"hover_idx": -1, "scroll_y": initial_scroll}

        def _render_popup() -> None:
            if not canvas.winfo_exists():
                return
            canvas.delete("all")
            self._popup_imgs.clear()

            card_img = create_rounded_rect_image(
                w,
                pop_h,
                p.radius_md + 2,
                fill_hex=p.surface,
                border_hex=p.border_strong,
                border_width=1,
                bg_hex=p.bg,
            )
            self._popup_imgs.append(card_img)
            canvas.create_image(0, 0, image=card_img, anchor="nw")

            accent = p.role_color(self._role)
            sy = state["scroll_y"]
            has_scroll = total_content_h > pop_h
            row_w = w - (18 if has_scroll else 12)

            for i, val in enumerate(self._values):
                ry = pad + i * item_h - sy
                if ry + item_h < pad - 2 or ry > pop_h - pad + 2:
                    continue

                is_sel = val == cur_val
                is_hov = i == state["hover_idx"]

                if is_sel or is_hov:
                    r_fill = p.role_subtle_bg(self._role) if is_sel else p.surface_hover
                    r_img = create_rounded_rect_image(
                        row_w,
                        item_h - 2,
                        p.radius_sm,
                        fill_hex=r_fill,
                        bg_hex=p.surface,
                    )
                    self._popup_imgs.append(r_img)
                    canvas.create_image(6, ry + 1, image=r_img, anchor="nw")

                if is_sel:
                    bar_img = create_rounded_rect_image(3, 16, 1, fill_hex=accent, bg_hex=p.role_subtle_bg(self._role))
                    self._popup_imgs.append(bar_img)
                    canvas.create_image(9, ry + (item_h - 16) // 2, image=bar_img, anchor="nw")

                    chk_img = create_icon_image("check", size=14, color=accent)
                    self._popup_imgs.append(chk_img)
                    canvas.create_image(6 + row_w - 14, ry + item_h // 2, image=chk_img, anchor="center")

                fg_col = accent if is_sel else p.fg
                canvas.create_text(
                    18,
                    ry + item_h // 2,
                    text=str(val),
                    fill=fg_col,
                    font=self._font,
                    anchor="w",
                )

            if has_scroll:
                track_h = pop_h - 12
                thumb_h = max(24, int(track_h * (pop_h / total_content_h)))
                max_sy = max(1, total_content_h - pop_h)
                thumb_y = 6 + int((track_h - thumb_h) * (sy / max_sy))
                sb_img = create_rounded_rect_image(5, thumb_h, 2, fill_hex=p.border_strong, bg_hex=p.surface)
                self._popup_imgs.append(sb_img)
                canvas.create_image(w - 9, thumb_y, image=sb_img, anchor="nw")

        def _idx_at(y_pos: int) -> int:
            idx = (y_pos + state["scroll_y"] - pad) // item_h
            return idx if 0 <= idx < len(self._values) else -1

        def _on_motion(e: tk.Event) -> None:
            idx = _idx_at(e.y)
            if idx != state["hover_idx"]:
                state["hover_idx"] = idx
                canvas.configure(cursor="hand2" if idx >= 0 else "arrow")
                _render_popup()

        def _on_click(e: tk.Event) -> None:
            idx = _idx_at(e.y)
            if 0 <= idx < len(self._values):
                picked = self._values[idx]
                self._close_popup()
                self.set(picked, notify=True)
                if self._entry is not None and self._entry.winfo_exists():
                    self._entry.focus_set()
                    self._entry.icursor("end")

        def _on_wheel(e: tk.Event) -> None:
            if total_content_h <= pop_h:
                return
            delta = -1 if e.delta > 0 else 1
            max_sy = max(0, total_content_h - pop_h)
            state["scroll_y"] = max(0, min(max_sy, state["scroll_y"] + delta * item_h))
            _render_popup()

        canvas.bind("<Motion>", _on_motion)
        canvas.bind("<ButtonRelease-1>", _on_click)
        canvas.bind("<MouseWheel>", _on_wheel)
        pop.bind("<MouseWheel>", _on_wheel)
        _render_popup()

        pop.geometry(f"{w}x{pop_h}+{x}+{y}")
        pop.focus_force()
        pop.bind("<FocusOut>", lambda e: self._close_popup())
        pop.bind("<Escape>", lambda e: self._close_popup())

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        for item in self.find_all():
            if self._entry_win is not None and item == self._entry_win:
                continue
            super().delete(item)

        w = max(self.winfo_width(), int(self["width"]))
        box_h = self._base_height
        r = p.radius_md

        is_open = self._popup is not None and self._popup.winfo_exists()
        accent = p.role_color(self._val_state if self._val_state else self._role)
        border_col = (
            accent
            if (is_open or self._is_focused or self._is_hovered or self._val_state)
            else p.input_border
        )
        border_w = 2 if (is_open or self._is_focused or self._val_state in ("danger", "warning")) else 1
        fill_col = p.surface_hover if (self._is_hovered and self._state == "readonly") else p.input_bg

        self._bg_img = create_rounded_rect_image(
            w,
            box_h,
            r,
            fill_hex=fill_col,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
            bottom_border_hex=accent if (is_open or self._is_focused or self._val_state) else p.border_strong,
        )
        bg_id = self.create_image(0, 0, image=self._bg_img, anchor="nw")
        self.tag_lower(bg_id)

        if self._entry is not None and self._entry_win is not None:
            self._entry.configure(
                bg=fill_col,
                fg=p.fg_subtle if self._state == "disabled" else p.input_fg,
                insertbackground=p.fg,
                selectbackground=accent,
                selectforeground=p.role_text(self._role),
            )
            self.coords(self._entry_win, 12, box_h // 2)
            self.itemconfigure(self._entry_win, width=max(24, w - 40))
        else:
            # Truncate visible display text cleanly if wider than box
            disp = self.get()
            max_disp_w = max(20, w - 42)
            if self._font.measure(disp) > max_disp_w and len(disp) > 4:
                while len(disp) > 3 and self._font.measure(disp + "…") > max_disp_w:
                    disp = disp[:-1]
                disp += "…"
            self.create_text(
                12,
                box_h // 2,
                text=disp,
                fill=p.fg_subtle if self._state == "disabled" else p.input_fg,
                font=self._font,
                anchor="w",
            )

        chev_name = "chevron_up" if is_open else "chevron_down"
        chev_col = accent if (is_open or self._is_hovered or self._val_state) else p.fg_muted
        self._chev_img = create_icon_image(chev_name, size=14, color=chev_col)
        self.create_image(w - 14, box_h // 2, image=self._chev_img, anchor="center")

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

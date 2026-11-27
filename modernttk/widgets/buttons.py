"""Modern rounded buttons for ModernTtk with semantic styles, variants, and smooth hover states."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional

from ..icons import AVAILABLE_ICONS, create_icon_image
from ..themes import ThemePalette
from ..utils import blend_colors, create_rounded_rect_image
from .base import ThemedWidgetMixin


class ModernButton(tk.Canvas, ThemedWidgetMixin):
    """Anti-aliased rounded button supporting semantic styles and visual variants.

    Parameters
    ----------
    master : tk.Misc
        Parent widget.
    text : str
        Button label text.
    command : Callable[[], None], optional
        Callback invoked when the button is clicked.
    bootstyle : str
        Semantic color role ('primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark')
        or compound string like 'success-outline', 'danger-pill', 'primary-ghost'.
    variant : str
        Visual variant: 'filled' (default), 'outline', 'ghost', 'subtle', or 'link'.
    radius : int, optional
        Corner radius in pixels. Set `pill=True` or `radius=999` for a pill button.
    pill : bool
        If True, renders fully rounded capsule ends.
    icon : str, optional
        Vector icon name from `AVAILABLE_ICONS` or Unicode glyph/emoji prefix displayed before the label text.
    width : int, optional
        Explicit pixel width (or character units if <= 42 with text; auto-sized to text + padding if omitted).
    height : int
        Pixel height of the button (default 36).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        bootstyle: str = "primary",
        variant: str = "filled",
        radius: Optional[int] = None,
        pill: bool = False,
        icon: Optional[str] = None,
        width: Optional[int] = None,
        height: int = 36,
        padx: int = 18,
        state: str = "normal",
        **kwargs,
    ) -> None:
        # Accept ttk-style kwargs without failing on Canvas
        style_kw = kwargs.pop("style", None)
        kwargs.pop("padding", None)
        kwargs.pop("pady", None)
        if style_kw and bootstyle == "primary":
            bootstyle = str(style_kw).replace(".TButton", "").replace(".", "-")

        # Parse compound bootstyle strings like "danger-outline-pill"
        parts = bootstyle.lower().split("-")
        self._role = parts[0] if parts else "primary"
        if "outline" in parts:
            variant = "outline"
        elif "ghost" in parts:
            variant = "ghost"
        elif "subtle" in parts:
            variant = "subtle"
        elif "link" in parts:
            variant = "link"
        if "pill" in parts or "round" in parts:
            pill = True

        self._text = text
        self._icon = icon
        self._command = command
        self._variant = variant
        self._pill = pill
        self._custom_radius = radius
        self._padx = padx
        self._state = state
        self._hover_t = 0.0
        self._is_hovered = False
        self._is_pressed = False
        self._anim_job: Optional[str] = None
        self._req_height = height

        if master is not None:
            curr: Optional[tk.Misc] = master
            while getattr(curr, "master", None) is not None:
                curr = getattr(curr, "master", None)
            if isinstance(curr, tk.Tk) and getattr(tk, "_default_root", None) is not curr:
                tk._default_root = curr

        p = self.palette
        self._font = tkfont.Font(
            root=master,
            family=p.font_family,
            size=p.font_size,
            weight="bold" if variant == "filled" and self._role == "primary" else "normal",
        )

        self._raw_width: Optional[int] = int(width) if width is not None else None
        calc_w = self._compute_width(self._raw_width)
        self._explicit_width = calc_w if width is not None else None

        super().__init__(
            master,
            width=calc_w,
            height=height,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2" if state == "normal" else "arrow",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Key-Return>", lambda e: self.invoke())
        self.bind("<Key-space>", lambda e: self.invoke())
        self.bind("<FocusIn>", lambda e: self._redraw())
        self.bind("<FocusOut>", lambda e: self._redraw())

        self._redraw()

    def _is_vector_icon(self) -> bool:
        return bool(self._icon and self._icon.lower().strip() in AVAILABLE_ICONS)

    def _display_text(self) -> str:
        if self._is_vector_icon():
            return f"    {self._text}" if self._text else ""
        if self._icon and self._text:
            return f"{self._icon}  {self._text}"
        return self._icon or self._text

    def _compute_width(self, raw_width: Optional[int]) -> int:
        """Compute button width in pixels, ensuring text/icon content is never squished."""
        display_str = self._display_text()
        text_w = self._font.measure(display_str) if display_str else 0
        min_content_w = (text_w + self._padx * 2) if self._text else max(38, self._req_height + 2)
        if raw_width is not None:
            if raw_width <= 42 and self._text:
                char_px = max(7, self._font.measure("0"))
                return max(int(raw_width * char_px) + self._padx, min_content_w)
            if self._text:
                return max(int(raw_width), min_content_w)
            return max(32, int(raw_width))
        if not self._text and self._icon:
            return max(38, self._req_height + 2)
        return max(76, min_content_w)

    def invoke(self) -> None:
        if self._state != "disabled" and self._command is not None:
            self._command()

    def configure_button(
        self,
        text: Optional[str] = None,
        bootstyle: Optional[str] = None,
        variant: Optional[str] = None,
        state: Optional[str] = None,
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        width: Optional[int] = None,
    ) -> None:
        if text is not None:
            self._text = text
        if icon is not None:
            self._icon = icon
        if width is not None:
            self._raw_width = int(width) if width > 0 else None
        if bootstyle is not None:
            parts = bootstyle.lower().split("-")
            self._role = parts[0] if parts else "primary"
            if "outline" in parts:
                self._variant = "outline"
            elif "ghost" in parts:
                self._variant = "ghost"
            elif "subtle" in parts:
                self._variant = "subtle"
            elif "link" in parts:
                self._variant = "link"
            elif variant is None:
                self._variant = "filled"
        if variant is not None:
            self._variant = variant
        if state is not None:
            self._state = state
            super().configure(cursor="hand2" if state == "normal" else "arrow")
        if command is not None:
            self._command = command
        new_w = self._compute_width(self._raw_width)
        self._explicit_width = new_w if self._raw_width is not None else None
        super().configure(width=new_w)
        self._redraw()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        btn_keys = {}
        for k in ("text", "bootstyle", "variant", "state", "command", "icon", "width"):
            if k in kwargs:
                btn_keys[k] = kwargs.pop(k)
        if "style" in kwargs:
            st = str(kwargs.pop("style")).replace(".TButton", "").replace(".", "-")
            btn_keys.setdefault("bootstyle", st)
        kwargs.pop("padding", None)
        if kwargs:
            super().configure(**kwargs)
        if btn_keys:
            self.configure_button(**btn_keys)

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        if key in ("bootstyle", "style"):
            return f"{self._role}-{self._variant}" if self._variant != "filled" else self._role
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

    def _on_enter(self, _event: tk.Event) -> None:
        if self._state == "disabled":
            return
        self._is_hovered = True
        self._animate_hover(1.0)

    def _on_leave(self, _event: tk.Event) -> None:
        self._is_hovered = False
        self._is_pressed = False
        self._animate_hover(0.0)

    def _on_press(self, _event: tk.Event) -> None:
        if self._state == "disabled":
            return
        self.focus_set()
        self._is_pressed = True
        self._redraw()

    def _on_release(self, event: tk.Event) -> None:
        if self._state == "disabled":
            return
        was_pressed = self._is_pressed
        self._is_pressed = False
        self._redraw()
        if was_pressed and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self.invoke()

    def _animate_hover(self, target: float) -> None:
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None

        step = 0.25 if target > self._hover_t else -0.25
        if abs(target - self._hover_t) <= 0.26:
            self._hover_t = target
            self._redraw()
            return

        self._hover_t = max(0.0, min(1.0, self._hover_t + step))
        self._redraw()
        self._anim_job = self.after(14, lambda: self._animate_hover(target))

    def _on_configure(self, _event: tk.Event) -> None:
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
        r = h // 2 if self._pill else (self._custom_radius if self._custom_radius is not None else p.radius_md)

        base_color = p.role_color(self._role)
        hover_color = p.role_hover(self._role)
        active_color = p.role_active(self._role)

        border_hex: Optional[str] = None
        bottom_border_hex: Optional[str] = None
        border_w = 0

        if self._state == "disabled":
            fill_hex = p.surface_alt
            text_hex = p.fg_subtle
            border_hex = p.border
            border_w = 1
        elif self._variant == "filled":
            if self._role in ("secondary", "light") and p.mode == "light":
                # Windows 11 style elevated neutral button
                base_fill = p.surface if self._role == "light" else p.surface_alt
                hov_fill = p.surface_hover
                act_fill = p.surface_active
                fill_hex = act_fill if self._is_pressed else blend_colors(base_fill, hov_fill, self._hover_t)
                text_hex = p.fg
                border_hex = p.border
                bottom_border_hex = p.border_strong
                border_w = 1
            else:
                fill_hex = active_color if self._is_pressed else blend_colors(base_color, hover_color, self._hover_t)
                text_hex = p.role_text(self._role)
                border_hex = blend_colors(fill_hex, "#ffffff" if p.mode == "dark" else "#000000", 0.12)
                bottom_border_hex = blend_colors(fill_hex, "#000000", 0.24)
                border_w = 1
        elif self._variant == "outline":
            subtle_bg = p.role_subtle_bg(self._role)
            fill_hex = active_color if self._is_pressed else blend_colors(parent_bg, subtle_bg, self._hover_t)
            text_hex = p.role_text(self._role) if self._is_pressed else base_color
            border_hex = base_color
            border_w = 1
        elif self._variant == "subtle":
            subtle_bg = p.role_subtle_bg(self._role)
            hov_bg = blend_colors(subtle_bg, base_color, 0.18)
            fill_hex = blend_colors(subtle_bg, hov_bg, self._hover_t)
            text_hex = base_color
            border_w = 0
        elif self._variant in ("ghost", "link"):
            subtle_bg = p.role_subtle_bg(self._role)
            fill_hex = blend_colors(parent_bg, subtle_bg, self._hover_t) if self._variant == "ghost" else parent_bg
            text_hex = hover_color if self._is_hovered else base_color
            border_w = 0
        else:
            fill_hex = base_color
            text_hex = p.role_text(self._role)

        if self._variant != "link" or self._hover_t > 0:
            self._img = create_rounded_rect_image(
                w,
                h,
                r,
                fill_hex=fill_hex,
                border_hex=border_hex,
                border_width=border_w,
                bg_hex=parent_bg,
                bottom_border_hex=bottom_border_hex,
            )
            self.create_image(0, 0, image=self._img, anchor="nw")

        y_offset = 1 if self._is_pressed else 0
        self._font.configure(
            underline=1 if (self._variant == "link" and self._is_hovered) else 0
        )
        if self._is_vector_icon():
            icon_sz = 17 if not self._text else 15
            self._vec_icon_img = create_icon_image(self._icon, size=icon_sz, color=text_hex)
            if self._text:
                tw = self._font.measure(self._text)
                total_w = icon_sz + 7 + tw
                start_x = (w - total_w) // 2
                self.create_image(start_x, h // 2 + y_offset, image=self._vec_icon_img, anchor="w")
                self.create_text(
                    start_x + icon_sz + 7,
                    h // 2 + y_offset,
                    text=self._text,
                    fill=text_hex,
                    font=self._font,
                    anchor="w",
                )
            else:
                self.create_image(w // 2, h // 2 + y_offset, image=self._vec_icon_img, anchor="center")
        else:
            self.create_text(
                w // 2,
                h // 2 + y_offset,
                text=self._display_text(),
                fill=text_hex,
                font=self._font,
                anchor="center",
            )

"""Base mixin and container classes for theme-reactive ModernTtk widgets."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from ..style import ThemeManager
from ..themes import ThemePalette


class ThemedWidgetMixin:
    """Mixin that automatically subscribes a widget to ThemeManager updates and cleans up on destroy."""

    _custom_bg_role: Optional[str] = None

    def _init_themed(self, bg_role: Optional[str] = None) -> None:
        self._custom_bg_role = bg_role
        self._theme_dirty = False
        self._tm = ThemeManager.instance()
        self._tm.subscribe(self._dispatch_theme_changed)
        if isinstance(self, tk.Widget):
            curr: Optional[tk.Misc] = self
            while getattr(curr, "master", None) is not None:
                curr = getattr(curr, "master", None)
            if isinstance(curr, tk.Tk) and getattr(tk, "_default_root", None) is not curr:
                tk._default_root = curr
            self.bind("<Destroy>", self._on_destroy_themed, add="+")
            self.bind("<Map>", self._on_mapped_themed, add="+")

    def _dispatch_theme_changed(self, palette: ThemePalette) -> None:
        if isinstance(self, tk.Widget) and not self.winfo_ismapped():
            self._theme_dirty = True
            return
        self._theme_dirty = False
        self._on_theme_changed(palette)

    def _on_mapped_themed(self, _event: tk.Event) -> None:
        if getattr(self, "_theme_dirty", False):
            self._theme_dirty = False
            self._on_theme_changed(self.palette)

    @property
    def palette(self) -> ThemePalette:
        return ThemeManager.instance().palette

    def _resolve_parent_bg(self) -> str:
        """Dynamically resolve the current theme's background color for the parent container."""
        p = self.palette
        if self._custom_bg_role:
            return getattr(p, self._custom_bg_role, self._custom_bg_role)

        # Walk up the widget hierarchy to see if we are inside a themed surface/card
        curr = getattr(self, "master", None)
        while curr is not None:
            if hasattr(curr, "_surface_role"):
                role = getattr(curr, "_surface_role")
                return getattr(p, role, p.surface)
            if hasattr(curr, "surface_role"):
                role = getattr(curr, "surface_role")
                return getattr(p, role, p.surface)
            curr = getattr(curr, "master", None)

        return p.bg

    def _on_theme_changed(self, palette: ThemePalette) -> None:
        """Override in subclasses to redraw when the theme changes."""
        pass

    def _on_destroy_themed(self, event: tk.Event) -> None:
        if event.widget is self:
            self._tm.unsubscribe(self._dispatch_theme_changed)


class ModernFrame(tk.Frame, ThemedWidgetMixin):
    """Theme-reactive Frame whose background automatically updates when the theme changes."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        surface_role: Optional[str] = None,
        **kwargs,
    ) -> None:
        self._Explicit_role = surface_role
        super().__init__(master, bd=0, highlightthickness=0, **kwargs)
        self._init_themed(bg_role=surface_role)
        self._apply_bg()

    @property
    def surface_role(self) -> str:
        if self._Explicit_role:
            return self._Explicit_role
        # Inherit surface role from ancestor if inside a card/surface
        curr = self.master
        while curr is not None:
            if hasattr(curr, "_surface_role"):
                return getattr(curr, "_surface_role")
            if hasattr(curr, "surface_role"):
                return getattr(curr, "surface_role")
            curr = getattr(curr, "master", None)
        return "bg"

    def _apply_bg(self) -> None:
        p = self.palette
        role = self.surface_role
        bg_col = getattr(p, role, p.bg)
        super().configure(bg=bg_col)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._apply_bg()


class ModernLabel(tk.Label, ThemedWidgetMixin):
    """Theme-reactive Label whose background and foreground automatically update with the theme."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        bootstyle: Optional[str] = None,
        muted: bool = False,
        surface_role: Optional[str] = None,
        font_size_delta: int = 0,
        bold: bool = False,
        **kwargs,
    ) -> None:
        self._role = bootstyle.split("-")[0] if bootstyle else None
        self._muted = muted
        self._font_delta = font_size_delta
        self._bold = bold
        p = ThemeManager.instance().palette
        if "font" not in kwargs:
            weight = "bold" if bold else "normal"
            kwargs["font"] = (p.font_family, p.font_size + font_size_delta, weight)

        super().__init__(master, text=text, bd=0, highlightthickness=0, **kwargs)
        self._init_themed(bg_role=surface_role)
        self._apply_colors()

    def _apply_colors(self) -> None:
        p = self.palette
        bg_col = self._resolve_parent_bg()
        if self._role:
            fg_col = p.role_color(self._role)
        elif self._muted:
            fg_col = p.fg_muted
        else:
            fg_col = p.fg
        super().configure(bg=bg_col, fg=fg_col)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._apply_colors()

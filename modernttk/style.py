"""Dynamic ThemeManager and ttk.Style configurator for ModernTtk."""

from __future__ import annotations

import json
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .themes import BUILTIN_THEMES, SEMANTIC_ROLES, ThemePalette
from .utils import adjust_brightness, blend_colors


class ThemeManager:
    """Singleton-style manager that synchronizes standard ttk styles and custom ModernTtk widgets."""

    _instance: Optional["ThemeManager"] = None

    def __init__(self) -> None:
        self._themes: Dict[str, ThemePalette] = dict(BUILTIN_THEMES)
        self._current_theme: str = "fluent_dark"
        self._listeners: List[Callable[[ThemePalette], None]] = []
        self._style: Optional[ttk.Style] = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def palette(self) -> ThemePalette:
        return self._themes[self._current_theme]

    @property
    def current_theme_name(self) -> str:
        return self._current_theme

    def list_themes(self) -> List[str]:
        return list(self._themes.keys())

    def register_theme(self, palette: ThemePalette | dict) -> ThemePalette:
        """Register a custom ThemePalette or dictionary definition."""
        if isinstance(palette, dict):
            base_mode = palette.get("mode", "dark")
            base = BUILTIN_THEMES["fluent_dark" if base_mode == "dark" else "fluent_light"].to_dict()
            base.update(palette)
            palette = ThemePalette.from_dict(base)
        self._themes[palette.name] = palette
        return palette

    def load_theme_json(self, path: str | Path) -> ThemePalette:
        """Load a custom theme from a JSON file and register it."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.register_theme(data)

    def subscribe(self, callback: Callable[[ThemePalette], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[ThemePalette], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def apply_theme(self, theme_name: str = "fluent_dark", root: Optional[tk.Misc] = None) -> ThemePalette:
        """Apply a theme by name (or 'light'/'dark'/'system' shorthand) to ttk and all ModernTtk widgets."""
        if theme_name.lower() == "system":
            resolved = detect_system_theme()
        else:
            shorthands = {
                "light": "fluent_light",
                "dark": "fluent_dark",
            }
            resolved = shorthands.get(theme_name.lower(), theme_name)
        if resolved not in self._themes:
            raise ValueError(f"Unknown theme '{theme_name}'. Available: {self.list_themes()}")

        self._current_theme = resolved
        p = self.palette

        if root is None:
            root = tk._default_root
        if root is not None:
            try:
                root.configure(bg=p.bg)
            except tk.TclError:
                pass
            self._apply_windows_titlebar_mode(root, p.mode == "dark")
            self._configure_ttk_styles(root, p)

        # Notify all custom widgets
        for listener in list(self._listeners):
            try:
                listener(p)
            except Exception:
                pass
        return p

    def toggle_mode(self, root: Optional[tk.Misc] = None) -> ThemePalette:
        """Toggle between light and dark themes."""
        pairs = {
            "fluent_light": "fluent_dark",
            "fluent_dark": "fluent_light",
            "cosmo": "darkly",
            "darkly": "cosmo",
            "minty": "cyborg",
            "cyborg": "minty",
            "dracula": "fluent_light",
        }
        target = pairs.get(
            self._current_theme,
            "fluent_light" if self.palette.mode == "dark" else "fluent_dark",
        )
        return self.apply_theme(target, root=root)

    @staticmethod
    def _apply_windows_titlebar_mode(root: tk.Misc, dark: bool) -> None:
        """Set Windows 11 DWM immersive dark mode on the native window titlebar if supported."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            if not hwnd:
                hwnd = root.winfo_id()
            value = ctypes.c_int(1 if dark else 0)
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
        except Exception:
            pass

    def _configure_ttk_styles(self, root: tk.Misc, p: ThemePalette) -> None:
        """Configure standard ttk widgets so they seamlessly match ModernTtk's palette."""
        style = ttk.Style(root)
        self._style = style

        # Use 'clam' base theme if currently on a non-colorable OS native theme
        if style.theme_use() in ("vista", "winnative", "xpnative", "aqua", "default", "classic"):
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        default_font = (p.font_family, p.font_size)
        bold_font = (p.font_family, p.font_size, "bold")
        heading_font = (p.font_family, p.font_size, "bold")

        style.configure(
            ".",
            background=p.bg,
            foreground=p.fg,
            fieldbackground=p.input_bg,
            troughcolor=p.surface_alt,
            bordercolor=p.border,
            lightcolor=p.surface,
            darkcolor=p.border,
            focuscolor=p.primary,
            selectbackground=p.primary,
            selectforeground=p.role_text("primary"),
            font=default_font,
        )

        # Frame & Card TFrame styles
        style.configure("TFrame", background=p.bg)
        style.configure("Surface.TFrame", background=p.surface)
        style.configure("Card.TFrame", background=p.surface, relief="solid", borderwidth=1)

        # Labels
        style.configure("TLabel", background=p.bg, foreground=p.fg, font=default_font)
        style.configure("Surface.TLabel", background=p.surface, foreground=p.fg, font=default_font)
        style.configure("Muted.TLabel", background=p.bg, foreground=p.fg_muted, font=default_font)
        style.configure("Title.TLabel", background=p.bg, foreground=p.fg, font=(p.font_family, p.font_size + 6, "bold"))
        style.configure("Subtitle.TLabel", background=p.bg, foreground=p.fg, font=(p.font_family, p.font_size + 2, "bold"))

        for role in SEMANTIC_ROLES:
            rc = p.role_color(role)
            style.configure(f"{role}.TLabel", background=p.bg, foreground=rc, font=default_font)
            style.configure(f"Surface.{role}.TLabel", background=p.surface, foreground=rc, font=default_font)

        # Standard ttk.Button + semantic variants
        style.configure(
            "TButton",
            background=p.surface_alt,
            foreground=p.fg,
            bordercolor=p.border,
            lightcolor=p.surface_alt,
            darkcolor=p.border,
            padding=(12, 6),
            relief="flat",
            font=default_font,
        )
        style.map(
            "TButton",
            background=[("pressed", p.surface_active), ("active", p.surface_hover), ("disabled", p.surface)],
            foreground=[("disabled", p.fg_subtle)],
        )

        for role in SEMANTIC_ROLES:
            rc = p.role_color(role)
            rh = p.role_hover(role)
            ra = p.role_active(role)
            rt = p.role_text(role)
            style.configure(
                f"{role}.TButton",
                background=rc,
                foreground=rt,
                bordercolor=rc,
                lightcolor=rc,
                darkcolor=rc,
                padding=(12, 6),
                relief="flat",
                font=bold_font if role == "primary" else default_font,
            )
            style.map(
                f"{role}.TButton",
                background=[("pressed", ra), ("active", rh), ("disabled", p.surface_alt)],
                foreground=[("disabled", p.fg_subtle)],
            )
            style.configure(
                f"{role}.Outline.TButton",
                background=p.surface,
                foreground=rc,
                bordercolor=rc,
                lightcolor=p.surface,
                darkcolor=rc,
                padding=(12, 6),
                relief="solid",
                borderwidth=1,
                font=default_font,
            )
            style.map(
                f"{role}.Outline.TButton",
                background=[("pressed", ra), ("active", p.role_subtle_bg(role)), ("disabled", p.surface_alt)],
                foreground=[("pressed", rt), ("disabled", p.fg_subtle)],
            )

        # Standard ttk.Entry
        style.configure(
            "TEntry",
            fieldbackground=p.input_bg,
            foreground=p.input_fg,
            insertcolor=p.fg,
            bordercolor=p.input_border,
            lightcolor=p.input_bg,
            darkcolor=p.input_border,
            padding=(8, 6),
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", p.input_focus_border), ("hover", p.border_strong)],
            lightcolor=[("focus", p.input_focus_border)],
        )

        # Standard ttk.Combobox
        style.configure(
            "TCombobox",
            fieldbackground=p.input_bg,
            background=p.surface_alt,
            foreground=p.input_fg,
            arrowcolor=p.fg,
            bordercolor=p.input_border,
            lightcolor=p.input_bg,
            darkcolor=p.input_border,
            padding=(8, 6),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", p.input_bg)],
            selectbackground=[("readonly", p.input_bg)],
            selectforeground=[("readonly", p.input_fg)],
            bordercolor=[("focus", p.input_focus_border), ("hover", p.border_strong)],
        )

        # Treeview / Data Table (borderless modern table layout)
        style.layout(
            "Treeview",
            [("Treeview.treearea", {"sticky": "nswe"})],
        )
        style.configure(
            "Treeview",
            background=p.surface,
            fieldbackground=p.surface,
            foreground=p.fg,
            bordercolor=p.surface,
            lightcolor=p.surface,
            darkcolor=p.surface,
            borderwidth=0,
            relief="flat",
            rowheight=36,
            font=default_font,
        )
        style.configure(
            "Treeview.Heading",
            background=p.surface_alt,
            foreground=p.fg_muted,
            bordercolor=p.surface_alt,
            lightcolor=p.surface_alt,
            darkcolor=p.surface_alt,
            borderwidth=0,
            padding=(12, 9),
            font=heading_font,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", p.role_subtle_bg("primary"))],
            foreground=[("selected", p.primary if p.mode == "light" else p.fg)],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", p.surface_hover)],
            foreground=[("active", p.fg)],
        )

        # Notebook (Flat borderless modern tabs)
        style.configure(
            "TNotebook",
            background=p.surface,
            bordercolor=p.border,
            lightcolor=p.surface,
            darkcolor=p.surface,
            borderwidth=0,
            relief="flat",
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=p.surface_alt,
            foreground=p.fg_muted,
            bordercolor=p.border,
            lightcolor=p.surface_alt,
            darkcolor=p.surface_alt,
            focuscolor=p.surface,
            borderwidth=0,
            padding=(18, 9),
            font=heading_font,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", p.role_subtle_bg("primary")), ("active", p.surface_hover)],
            foreground=[("selected", p.primary), ("active", p.fg)],
            lightcolor=[("selected", p.role_subtle_bg("primary")), ("active", p.surface_hover)],
            darkcolor=[("selected", p.role_subtle_bg("primary")), ("active", p.surface_hover)],
        )

        # Scrollbar
        style.configure(
            "TScrollbar",
            background=p.surface_hover,
            troughcolor=p.bg,
            bordercolor=p.bg,
            arrowcolor=p.fg_muted,
            relief="flat",
        )
        style.map(
            "TScrollbar",
            background=[("active", p.fg_muted), ("pressed", p.primary)],
        )

        # Separator
        style.configure("TSeparator", background=p.divider)

        # PanedWindow
        style.configure("TPanedwindow", background=p.bg)
        style.configure("Sash", sashthickness=6, gripcount=0, background=p.divider, lightcolor=p.divider, darkcolor=p.divider)

        # LabelFrame
        style.configure(
            "TLabelframe",
            background=p.surface,
            foreground=p.fg,
            bordercolor=p.border,
            lightcolor=p.surface,
            darkcolor=p.border,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=p.surface,
            foreground=p.primary,
            font=heading_font,
        )

        # Progressbar
        style.configure(
            "TProgressbar",
            troughcolor=p.surface_alt,
            background=p.primary,
            bordercolor=p.surface_alt,
            lightcolor=p.primary,
            darkcolor=p.primary,
            thickness=8,
        )
        for role in SEMANTIC_ROLES:
            rc = p.role_color(role)
            style.configure(
                f"{role}.Horizontal.TProgressbar",
                troughcolor=p.surface_alt,
                background=rc,
                bordercolor=p.surface_alt,
                lightcolor=rc,
                darkcolor=rc,
                thickness=8,
            )


# Convenience module-level functions (sv_ttk / ttkbootstrap ergonomic style)
def set_theme(theme_name: str = "fluent_dark", root: Optional[tk.Misc] = None) -> ThemePalette:
    """Set the active ModernTtk theme (e.g. 'fluent_dark', 'fluent_light', 'cosmo', 'darkly', 'cyborg', 'minty', 'dracula')."""
    return ThemeManager.instance().apply_theme(theme_name, root=root)


def get_theme() -> str:
    """Return the name of the currently active theme."""
    return ThemeManager.instance().current_theme_name


def toggle_theme(root: Optional[tk.Misc] = None) -> ThemePalette:
    """Toggle between light and dark mode."""
    return ThemeManager.instance().toggle_mode(root=root)


def use_dark_theme(root: Optional[tk.Misc] = None) -> ThemePalette:
    """Switch to Fluent Dark theme."""
    return ThemeManager.instance().apply_theme("fluent_dark", root=root)


def use_light_theme(root: Optional[tk.Misc] = None) -> ThemePalette:
    """Switch to Fluent Light theme."""
    return ThemeManager.instance().apply_theme("fluent_light", root=root)


def detect_system_theme() -> str:
    """Detect the operating system's light/dark preference and return 'fluent_dark' or 'fluent_light'."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "fluent_light" if int(val) == 1 else "fluent_dark"
        except Exception:
            return "fluent_dark"
    elif sys.platform == "darwin":
        try:
            import subprocess
            out = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            return "fluent_dark" if "dark" in out.stdout.lower() else "fluent_light"
        except Exception:
            return "fluent_light"
    return "fluent_dark"


def auto_theme_tree(
    root_widget: tk.Misc,
    palette: Optional[ThemePalette] = None,
    subscribe: bool = True,
) -> None:
    """Recursively theme an existing legacy Tkinter widget tree without refactoring widget classes.

    Walks standard `tk.Frame`, `tk.Label`, `tk.Button`, `tk.Entry`, `tk.Text`, `tk.Listbox`,
    `tk.Canvas`, `tk.Checkbutton`, `tk.Radiobutton`, `tk.Spinbox`, and `tk.Toplevel` widgets,
    while preserving custom `ModernTtk` widgets that already subscribe to `ThemeManager`.
    """
    tm = ThemeManager.instance()
    p = palette if palette is not None else tm.palette
    default_font = (p.font_family, p.font_size)

    def _walk(w: tk.Misc, parent_bg: str) -> None:
        if not w.winfo_exists():
            return
        # Skip ModernTtk widgets that already handle their own theming via ThemedWidgetMixin
        if hasattr(w, "_init_themed"):
            curr_bg = getattr(p, getattr(w, "surface_role", "surface"), p.surface)
            for child in w.winfo_children():
                _walk(child, curr_bg)
            return

        # Skip tksheet.Sheet instances (they manage their own MT/CH/RI/TL canvases)
        if hasattr(w, "MT") and hasattr(w, "CH"):
            return

        cls_name = w.winfo_class()
        next_bg = parent_bg

        try:
            if cls_name in ("Tk", "Toplevel"):
                w.configure(bg=p.bg)
                ThemeManager._apply_windows_titlebar_mode(w, p.mode == "dark")
                next_bg = p.bg
            elif cls_name == "Frame":
                w.configure(bg=parent_bg, highlightbackground=p.border)
            elif cls_name == "Labelframe":
                w.configure(bg=p.surface, fg=p.primary, font=(p.font_family, p.font_size, "bold"))
                next_bg = p.surface
            elif cls_name == "Label":
                w.configure(bg=parent_bg, fg=p.fg)
            elif cls_name == "Button":
                w.configure(
                    bg=p.surface_alt,
                    fg=p.fg,
                    activebackground=p.surface_hover,
                    activeforeground=p.fg,
                    relief="flat",
                    bd=1,
                    highlightbackground=p.border,
                    padx=10,
                    pady=4,
                )
            elif cls_name in ("Entry", "Spinbox"):
                w.configure(
                    bg=p.input_bg,
                    fg=p.input_fg,
                    insertbackground=p.fg,
                    selectbackground=p.primary,
                    selectforeground=p.role_text("primary"),
                    relief="solid",
                    bd=1,
                    highlightbackground=p.input_border,
                    highlightcolor=p.input_focus_border,
                )
            elif cls_name == "Text":
                w.configure(
                    bg=p.input_bg,
                    fg=p.input_fg,
                    insertbackground=p.fg,
                    selectbackground=p.primary,
                    selectforeground=p.role_text("primary"),
                    relief="flat",
                    bd=1,
                    highlightthickness=1,
                    highlightbackground=p.input_border,
                    highlightcolor=p.input_focus_border,
                    padx=8,
                    pady=6,
                )
            elif cls_name == "Listbox":
                w.configure(
                    bg=p.surface,
                    fg=p.fg,
                    selectbackground=p.role_subtle_bg("primary"),
                    selectforeground=p.primary if p.mode == "light" else p.fg,
                    relief="flat",
                    bd=1,
                    highlightthickness=1,
                    highlightbackground=p.border,
                    highlightcolor=p.primary,
                    activestyle="none",
                    font=default_font,
                )
            elif cls_name in ("Checkbutton", "Radiobutton"):
                w.configure(
                    bg=parent_bg,
                    fg=p.fg,
                    activebackground=parent_bg,
                    activeforeground=p.fg,
                    selectcolor=p.input_bg,
                    highlightthickness=0,
                )
            elif cls_name == "Canvas":
                w.configure(bg=parent_bg, highlightthickness=0)
        except tk.TclError:
            pass

        for child in w.winfo_children():
            _walk(child, next_bg)

    _walk(root_widget, p.bg)

    if subscribe and not getattr(root_widget, "_mtk_auto_theme_bound", False):
        setattr(root_widget, "_mtk_auto_theme_bound", True)

        def _on_theme_change(new_p: ThemePalette) -> None:
            if root_widget.winfo_exists():
                auto_theme_tree(root_widget, palette=new_p, subscribe=False)

        tm.subscribe(_on_theme_change)


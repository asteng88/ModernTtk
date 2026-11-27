"""Theme palettes and semantic color definitions for ModernTtk.

Combines Windows 11 Fluent Design (sv_ttk) surface/elevation tokens with
Bootstrap (ttkbootstrap) semantic color roles.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict
import json

from .utils import adjust_brightness, blend_colors, contrast_text_color


SEMANTIC_ROLES = (
    "primary",
    "secondary",
    "success",
    "info",
    "warning",
    "danger",
    "light",
    "dark",
)


@dataclass
class ThemePalette:
    """Complete color palette and design token set for a ModernTtk theme."""

    name: str
    mode: str  # "light" or "dark"

    # Surface & Elevation tokens (Fluent / sv_ttk inspired)
    bg: str                 # Main window background
    surface: str            # Card / elevated surface background
    surface_alt: str        # Secondary/subtle surface (inputs, headers, striped rows)
    surface_hover: str      # Hover state on neutral surface
    surface_active: str     # Pressed state on neutral surface

    # Typography tokens
    fg: str                 # Primary text
    fg_muted: str           # Secondary / muted text
    fg_subtle: str          # Disabled / placeholder text

    # Border & Divider tokens
    border: str             # Standard control / card border
    border_strong: str      # Bottom elevation border / focused neutral border
    divider: str            # Hairline separator

    # Input control tokens
    input_bg: str
    input_fg: str
    input_border: str
    input_focus_border: str

    # Semantic color roles (ttkbootstrap inspired)
    primary: str
    secondary: str
    success: str
    info: str
    warning: str
    danger: str
    light: str
    dark: str

    # Geometry & Typography defaults
    radius_sm: int = 6
    radius_md: int = 8
    radius_lg: int = 12
    font_family: str = "Segoe UI"
    font_size: int = 10

    def role_color(self, role: str) -> str:
        """Return the base hex color for a semantic role (or hex literal)."""
        if role.startswith("#"):
            return role
        return getattr(self, role, self.primary)

    def role_hover(self, role: str) -> str:
        """Return the hover hex color for a semantic role."""
        base = self.role_color(role)
        if self.mode == "dark":
            return adjust_brightness(base, 0.14)
        return adjust_brightness(base, -0.10)

    def role_active(self, role: str) -> str:
        """Return the active/pressed hex color for a semantic role."""
        base = self.role_color(role)
        if self.mode == "dark":
            return adjust_brightness(base, -0.08)
        return adjust_brightness(base, -0.20)

    def role_subtle_bg(self, role: str) -> str:
        """Return a soft tinted background for badges, alerts, or ghost hovers."""
        base = self.role_color(role)
        return blend_colors(self.surface, base, 0.16 if self.mode == "dark" else 0.12)

    def role_text(self, role: str) -> str:
        """Return the contrasting foreground color for a filled role background."""
        if role == "light":
            return "#0f172a"
        if role == "dark":
            return "#f8fafc"
        return contrast_text_color(self.role_color(role))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ThemePalette":
        return cls(**data)


BUILTIN_THEMES: Dict[str, ThemePalette] = {
    "fluent_light": ThemePalette(
        name="fluent_light",
        mode="light",
        bg="#f3f3f3",
        surface="#fbfbfb",
        surface_alt="#f0f0f0",
        surface_hover="#eaeaea",
        surface_active="#e0e0e0",
        fg="#1a1a1a",
        fg_muted="#5c5c5c",
        fg_subtle="#9ca3af",
        border="#d6d6d6",
        border_strong="#b8b8b8",
        divider="#e5e5e5",
        input_bg="#ffffff",
        input_fg="#1a1a1a",
        input_border="#d1d5db",
        input_focus_border="#0067c0",
        primary="#0067c0",
        secondary="#5c636a",
        success="#15803d",
        info="#0284c7",
        warning="#d97706",
        danger="#dc2626",
        light="#f8fafc",
        dark="#1e293b",
    ),
    "fluent_dark": ThemePalette(
        name="fluent_dark",
        mode="dark",
        bg="#1c1c1c",
        surface="#272727",
        surface_alt="#323232",
        surface_hover="#383838",
        surface_active="#424242",
        fg="#f5f5f5",
        fg_muted="#a3a3a3",
        fg_subtle="#6b7280",
        border="#3d3d3d",
        border_strong="#525252",
        divider="#333333",
        input_bg="#242424",
        input_fg="#f5f5f5",
        input_border="#454545",
        input_focus_border="#4cc2ff",
        primary="#4cc2ff",
        secondary="#64748b",
        success="#22c55e",
        info="#38bdf8",
        warning="#f59e0b",
        danger="#ef4444",
        light="#e2e8f0",
        dark="#0f172a",
    ),
    "cosmo": ThemePalette(
        name="cosmo",
        mode="light",
        bg="#f8fafc",
        surface="#ffffff",
        surface_alt="#f1f5f9",
        surface_hover="#e2e8f0",
        surface_active="#cbd5e1",
        fg="#0f172a",
        fg_muted="#475569",
        fg_subtle="#94a3b8",
        border="#e2e8f0",
        border_strong="#cbd5e1",
        divider="#f1f5f9",
        input_bg="#ffffff",
        input_fg="#0f172a",
        input_border="#cbd5e1",
        input_focus_border="#2563eb",
        primary="#2563eb",
        secondary="#475569",
        success="#16a34a",
        info="#0891b2",
        warning="#ea580c",
        danger="#e11d48",
        light="#f8fafc",
        dark="#0f172a",
    ),
    "darkly": ThemePalette(
        name="darkly",
        mode="dark",
        bg="#0f172a",
        surface="#1e293b",
        surface_alt="#273549",
        surface_hover="#334155",
        surface_active="#475569",
        fg="#f8fafc",
        fg_muted="#94a3b8",
        fg_subtle="#64748b",
        border="#334155",
        border_strong="#475569",
        divider="#1e293b",
        input_bg="#162032",
        input_fg="#f8fafc",
        input_border="#334155",
        input_focus_border="#3b82f6",
        primary="#3b82f6",
        secondary="#64748b",
        success="#10b981",
        info="#06b6d4",
        warning="#f59e0b",
        danger="#f43f5e",
        light="#f1f5f9",
        dark="#090d16",
    ),
    "cyborg": ThemePalette(
        name="cyborg",
        mode="dark",
        bg="#09090b",
        surface="#141418",
        surface_alt="#1f1f26",
        surface_hover="#272730",
        surface_active="#32323e",
        fg="#fafafa",
        fg_muted="#a1a1aa",
        fg_subtle="#52525b",
        border="#27272a",
        border_strong="#3f3f46",
        divider="#1f1f23",
        input_bg="#121216",
        input_fg="#fafafa",
        input_border="#2e2e36",
        input_focus_border="#06b6d4",
        primary="#06b6d4",
        secondary="#71717a",
        success="#22c55e",
        info="#8b5cf6",
        warning="#eab308",
        danger="#f43f5e",
        light="#e4e4e7",
        dark="#09090b",
    ),
    "minty": ThemePalette(
        name="minty",
        mode="light",
        bg="#f2fbf9",
        surface="#ffffff",
        surface_alt="#e6f6f2",
        surface_hover="#d5efe9",
        surface_active="#bfe5dc",
        fg="#132a26",
        fg_muted="#496a63",
        fg_subtle="#88a8a1",
        border="#cde5df",
        border_strong="#adcFc7",
        divider="#e3f2ee",
        input_bg="#ffffff",
        input_fg="#132a26",
        input_border="#c2dfd8",
        input_focus_border="#14b8a6",
        primary="#0d9488",
        secondary="#f43f5e",
        success="#16a34a",
        info="#0284c7",
        warning="#f59e0b",
        danger="#ef4444",
        light="#f0fdfa",
        dark="#134e4a",
    ),
    "dracula": ThemePalette(
        name="dracula",
        mode="dark",
        bg="#1e1f29",
        surface="#282a36",
        surface_alt="#343746",
        surface_hover="#3e4153",
        surface_active="#44475a",
        fg="#f8f8f2",
        fg_muted="#9ea4c2",
        fg_subtle="#6272a4",
        border="#44475a",
        border_strong="#6272a4",
        divider="#343746",
        input_bg="#21222c",
        input_fg="#f8f8f2",
        input_border="#44475a",
        input_focus_border="#bd93f9",
        primary="#bd93f9",
        secondary="#6272a4",
        success="#50fa7b",
        info="#8be9fd",
        warning="#ffb86c",
        danger="#ff5555",
        light="#f8f8f2",
        dark="#191a21",
    ),
    "rccp_blue": ThemePalette(
        name="rccp_blue",
        mode="light",
        bg="#f0f6fa",
        surface="#ffffff",
        surface_alt="#eaf4fb",
        surface_hover="#d7e6ef",
        surface_active="#b8d6e8",
        fg="#18212b",
        fg_muted="#52606d",
        fg_subtle="#8292a0",
        border="#b8d6e8",
        border_strong="#8ab8d6",
        divider="#d7e6ef",
        input_bg="#ffffff",
        input_fg="#18212b",
        input_border="#b8d6e8",
        input_focus_border="#2b8fcc",
        primary="#2b8fcc",
        secondary="#5b6b7a",
        success="#198754",
        info="#6b8ead",
        warning="#d99000",
        danger="#c73a4a",
        light="#eaf4fb",
        dark="#18212b",
    ),
    "rccp_teal": ThemePalette(
        name="rccp_teal",
        mode="light",
        bg="#effaf8",
        surface="#ffffff",
        surface_alt="#e5f8f4",
        surface_hover="#d5ece7",
        surface_active="#b7e3dc",
        fg="#16332f",
        fg_muted="#58726e",
        fg_subtle="#849e9a",
        border="#b7e3dc",
        border_strong="#88cec3",
        divider="#d5ece7",
        input_bg="#ffffff",
        input_fg="#16332f",
        input_border="#b7e3dc",
        input_focus_border="#188c7e",
        primary="#188c7e",
        secondary="#52706c",
        success="#198754",
        info="#4f7ddd",
        warning="#c98700",
        danger="#c5485c",
        light="#e5f8f4",
        dark="#123d38",
    ),
    "rccp_fuchsia": ThemePalette(
        name="rccp_fuchsia",
        mode="light",
        bg="#fdf3f8",
        surface="#ffffff",
        surface_alt="#fceaf3",
        surface_hover="#f1dce7",
        surface_active="#edbed4",
        fg="#321322",
        fg_muted="#765669",
        fg_subtle="#a38597",
        border="#edbed4",
        border_strong="#df9bbb",
        divider="#f1dce7",
        input_bg="#ffffff",
        input_fg="#321322",
        input_border="#edbed4",
        input_focus_border="#d6347e",
        primary="#d6347e",
        secondary="#765269",
        success="#198754",
        info="#7e5ce0",
        warning="#c98600",
        danger="#c73a4a",
        light="#fceaf3",
        dark="#321322",
    ),
}

"""ModernTkk — A hybrid modern Tkinter & ttk UI styling and widget library.

Combines the clean Windows 11 Fluent Design aesthetics of `sv_ttk` with the
semantic color system and rich component suite of `ttkbootstrap`, powered by
supersampled anti-aliased rendering for crisp rounded corners and smooth animations.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from .icons import AVAILABLE_ICONS, create_icon_image, icon
from .style import (
    ThemeManager,
    auto_theme_tree,
    detect_system_theme,
    get_theme,
    set_theme,
    toggle_theme,
    use_dark_theme,
    use_light_theme,
)
from .themes import BUILTIN_THEMES, SEMANTIC_ROLES, ThemePalette
from .widgets import (
    ModernAccordion,
    ModernBadge,
    ModernButton,
    ModernCalendar,
    ModernCard,
    ModernCheckbox,
    ModernChips,
    ModernCombobox,
    ModernCommandPalette,
    ModernContextMenu,
    ModernDatePicker,
    ModernDialog,
    ModernEntry,
    ModernExpander,
    ModernFrame,
    ModernLabel,
    ModernMenu,
    ModernMeter,
    ModernMetricCard,
    ModernNotebook,
    ModernPasswordEntry,
    ModernProgressBar,
    ModernProgressDialog,
    ModernRadioButton,
    ModernScrollableFrame,
    ModernScrollbar,
    ModernSearchBar,
    ModernSegmentedButton,
    ModernSidebar,
    ModernSlider,
    ModernSpinbox,
    ModernSplash,
    ModernStatusBar,
    ModernSwitch,
    ModernTagInput,
    ModernText,
    ModernTextarea,
    ModernToast,
    ModernTooltip,
    ModernTreeview,
    bind_responsive_sections,
    style_matplotlib_figure,
    style_matplotlib_toolbar,
    style_tksheet,
)

# Short ergonomic aliases (ttkbootstrap / customTkinter style)
Frame = ModernFrame
Label = ModernLabel
Button = ModernButton
Switch = ModernSwitch
Checkbox = ModernCheckbox
RadioButton = ModernRadioButton
Entry = ModernEntry
SearchBar = ModernSearchBar
PasswordEntry = ModernPasswordEntry
Combobox = ModernCombobox
Spinbox = ModernSpinbox
Calendar = ModernCalendar
DatePicker = ModernDatePicker
Card = ModernCard
Notebook = ModernNotebook
TabView = ModernNotebook
SegmentedButton = ModernSegmentedButton
Badge = ModernBadge
Tooltip = ModernTooltip
ProgressBar = ModernProgressBar
Slider = ModernSlider
Toast = ModernToast
Dialog = ModernDialog
Scrollbar = ModernScrollbar
Treeview = ModernTreeview
DataTable = ModernTreeview
MetricCard = ModernMetricCard
ProgressDialog = ModernProgressDialog
ScrollableFrame = ModernScrollableFrame
Splash = ModernSplash
StatusBar = ModernStatusBar
Meter = ModernMeter
Text = ModernText
Textarea = ModernTextarea
Accordion = ModernAccordion
Expander = ModernExpander
TagInput = ModernTagInput
Chips = ModernChips
Sidebar = ModernSidebar
ContextMenu = ModernContextMenu
Menu = ModernMenu
CommandPalette = ModernCommandPalette


class ModernWindow(tk.Tk):
    """Convenience root window that initializes DPI awareness and applies a ModernTkk theme automatically."""

    def __init__(
        self,
        title: str = "ModernTkk Application",
        themename: str = "fluent_dark",
        geometry: str = "1160x820",
        **kwargs,
    ) -> None:
        self._enable_dpi_awareness()
        super().__init__(**kwargs)
        self.title(title)
        self.geometry(geometry)
        set_theme(themename, root=self)

    @staticmethod
    def _enable_dpi_awareness() -> None:
        import sys
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass


__version__ = "0.2.0"

__all__ = [
    "ModernWindow",
    "ThemeManager",
    "ThemePalette",
    "BUILTIN_THEMES",
    "SEMANTIC_ROLES",
    "AVAILABLE_ICONS",
    "icon",
    "create_icon_image",
    "set_theme",
    "get_theme",
    "toggle_theme",
    "use_dark_theme",
    "use_light_theme",
    "detect_system_theme",
    "auto_theme_tree",
    "ModernFrame",
    "ModernLabel",
    "ModernButton",
    "ModernSwitch",
    "ModernCheckbox",
    "ModernRadioButton",
    "ModernEntry",
    "ModernSearchBar",
    "ModernPasswordEntry",
    "ModernCombobox",
    "ModernSpinbox",
    "ModernCalendar",
    "ModernDatePicker",
    "ModernCard",
    "ModernNotebook",
    "ModernSegmentedButton",
    "ModernBadge",
    "ModernTooltip",
    "ModernProgressBar",
    "ModernSlider",
    "ModernToast",
    "ModernDialog",
    "ModernScrollbar",
    "ModernTreeview",
    "ModernMetricCard",
    "ModernProgressDialog",
    "ModernScrollableFrame",
    "ModernSplash",
    "ModernStatusBar",
    "ModernMeter",
    "ModernText",
    "ModernTextarea",
    "ModernAccordion",
    "ModernExpander",
    "ModernTagInput",
    "ModernChips",
    "ModernSidebar",
    "ModernContextMenu",
    "ModernMenu",
    "ModernCommandPalette",
    "bind_responsive_sections",
    "style_matplotlib_figure",
    "style_matplotlib_toolbar",
    "style_tksheet",
    "Frame",
    "Label",
    "Button",
    "Switch",
    "Checkbox",
    "RadioButton",
    "Entry",
    "SearchBar",
    "PasswordEntry",
    "Combobox",
    "Spinbox",
    "Calendar",
    "DatePicker",
    "Card",
    "Notebook",
    "TabView",
    "SegmentedButton",
    "Badge",
    "Tooltip",
    "ProgressBar",
    "Slider",
    "Toast",
    "Dialog",
    "Scrollbar",
    "Treeview",
    "DataTable",
    "MetricCard",
    "ProgressDialog",
    "ScrollableFrame",
    "Splash",
    "StatusBar",
    "Meter",
    "Text",
    "Textarea",
    "Accordion",
    "Expander",
    "TagInput",
    "Chips",
    "Sidebar",
    "ContextMenu",
    "Menu",
    "CommandPalette",
]

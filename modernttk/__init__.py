"""ModernTtk — A hybrid modern Tkinter & ttk UI styling and widget library.

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
    DATA_STREAM_FRAME_COUNT,
    DEFAULT_STAGE_CEILINGS,
    SPINNER_FRAME_COUNT,
    ModernAccordion,
    ModernActivityTimer,
    ModernBadge,
    ModernBusyOverlay,
    ModernButton,
    ModernCalendar,
    ModernCard,
    ModernCheckbox,
    ModernChips,
    ModernCombobox,
    ModernCommandPalette,
    ModernContextMenu,
    ModernDataStream,
    ModernDatePicker,
    ModernDialog,
    ModernEntry,
    ModernExpander,
    ModernFrame,
    ModernLabel,
    ModernLinearGauge,
    ModernLiquidGauge,
    ModernMenu,
    ModernMenuButton,
    ModernMeter,
    ModernMetricCard,
    ModernMultiRingGauge,
    ModernNotebook,
    ModernPasswordEntry,
    ModernProgressBar,
    ModernProgressDialog,
    ModernRadioButton,
    ModernScrollableFrame,
    ModernScrollbar,
    ModernSearchBar,
    ModernSegmentedButton,
    ModernSegmentedGauge,
    ModernSemiGauge,
    ModernSidebar,
    ModernSlider,
    ModernSpeedometer,
    ModernSpinbox,
    ModernSplash,
    ModernStatusBar,
    ModernSubprocessWorker,
    ModernSwitch,
    ModernTagInput,
    ModernTaskRunner,
    ModernText,
    ModernTextarea,
    ModernToast,
    ModernTooltip,
    ModernTreeview,
    _DIAL_FRAMES_CACHE,
    bind_responsive_sections,
    build_data_stream_frames,
    build_timer_dial_frames,
    default_stage_pct_ceiling,
    default_stream_status,
    enable_tksheet_switches,
    normalize_stream_direction,
    read_ipc_frame,
    render_data_stream_overlay_badge,
    render_timer_overlay_badge,
    run_subprocess_worker_loop,
    style_matplotlib_figure,
    style_matplotlib_toolbar,
    style_tksheet,
    write_ipc_frame,
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
SemiGauge = ModernSemiGauge
ArcGauge = ModernSemiGauge
Speedometer = ModernSpeedometer
DialGauge = ModernSpeedometer
SegmentedGauge = ModernSegmentedGauge
LedGauge = ModernSegmentedGauge
LinearGauge = ModernLinearGauge
BulletGauge = ModernLinearGauge
LiquidGauge = ModernLiquidGauge
TankGauge = ModernLiquidGauge
MultiRingGauge = ModernMultiRingGauge
ActivityRings = ModernMultiRingGauge
Text = ModernText
Textarea = ModernTextarea
Accordion = ModernAccordion
Expander = ModernExpander
TagInput = ModernTagInput
Chips = ModernChips
Sidebar = ModernSidebar
ContextMenu = ModernContextMenu
Menu = ModernMenu
MenuButton = ModernMenuButton
Menubutton = ModernMenuButton
CommandPalette = ModernCommandPalette
ActivityTimer = ModernActivityTimer
ChronoTimer = ModernActivityTimer
Timer = ModernActivityTimer
DataStream = ModernDataStream
DataTransferAnimation = ModernDataStream
BusyOverlay = ModernBusyOverlay
SubprocessWorker = ModernSubprocessWorker
TaskRunner = ModernTaskRunner
UninterruptedTaskRunner = ModernTaskRunner


class ModernWindow(tk.Tk):
    """Convenience root window that initializes DPI awareness and applies a ModernTtk theme automatically."""

    def __init__(
        self,
        title: str = "ModernTtk Application",
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
    "ModernSemiGauge",
    "ModernSpeedometer",
    "ModernSegmentedGauge",
    "ModernLinearGauge",
    "ModernLiquidGauge",
    "ModernMultiRingGauge",
    "ModernText",
    "ModernTextarea",
    "ModernAccordion",
    "ModernExpander",
    "ModernTagInput",
    "ModernChips",
    "ModernSidebar",
    "ModernContextMenu",
    "ModernMenu",
    "ModernMenuButton",
    "ModernCommandPalette",
    "bind_responsive_sections",
    "enable_tksheet_switches",
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
    "SemiGauge",
    "ArcGauge",
    "Speedometer",
    "DialGauge",
    "SegmentedGauge",
    "LedGauge",
    "LinearGauge",
    "BulletGauge",
    "LiquidGauge",
    "TankGauge",
    "MultiRingGauge",
    "ActivityRings",
    "Text",
    "Textarea",
    "Accordion",
    "Expander",
    "TagInput",
    "Chips",
    "Sidebar",
    "ContextMenu",
    "Menu",
    "MenuButton",
    "Menubutton",
    "CommandPalette",
    "DATA_STREAM_FRAME_COUNT",
    "ModernDataStream",
    "DataStream",
    "DataTransferAnimation",
    "build_data_stream_frames",
    "default_stream_status",
    "normalize_stream_direction",
    "render_data_stream_overlay_badge",
    "SPINNER_FRAME_COUNT",
    "DEFAULT_STAGE_CEILINGS",
    "_DIAL_FRAMES_CACHE",
    "build_timer_dial_frames",
    "render_timer_overlay_badge",
    "default_stage_pct_ceiling",
    "ModernActivityTimer",
    "ModernBusyOverlay",
    "ModernSubprocessWorker",
    "ModernTaskRunner",
    "ActivityTimer",
    "ChronoTimer",
    "Timer",
    "BusyOverlay",
    "SubprocessWorker",
    "TaskRunner",
    "UninterruptedTaskRunner",
    "write_ipc_frame",
    "read_ipc_frame",
    "run_subprocess_worker_loop",
]

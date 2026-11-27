# ModernTtk — Complete Developer Guide & API Reference

**ModernTtk** is a next-generation UI styling and custom widget library for Python's `tkinter` and `tkinter.ttk`. It combines the clean **Windows 11 Fluent Design** surface aesthetics of `sv_ttk` with the **semantic color roles and rich component suite** of `ttkbootstrap`—powered by a **4× supersampled Pillow (`PIL`) anti-aliased rendering engine** for crisp rounded corners, smooth 60 FPS animations, and zero-artifact live theme switching.

---

## Table of Contents

1. [Why ModernTtk?](#1-why-modernttk)
2. [Installation & Requirements](#2-installation--requirements)
3. [Quick Start](#3-quick-start)
4. [Theming & Palette System](#4-theming--palette-system)
   - [Built-In Themes](#built-in-themes)
   - [Semantic Color Roles (`bootstyle`)](#semantic-color-roles-bootstyle)
   - [Switching & Toggling Themes at Runtime](#switching--toggling-themes-at-runtime)
   - [Creating Custom Themes (Dict or JSON)](#creating-custom-themes-dict-or-json)
5. [Core Widget Reference](#5-core-widget-reference)
   - [Window & Base Containers (`ModernWindow`, `Frame`, `Label`, `Card`)](#51-window--base-containers)
   - [Rounded Buttons (`Button` / `ModernButton`)](#52-rounded-buttons)
   - [Animated Toggles (`Switch`, `Checkbox`, `RadioButton`)](#53-animated-toggles)
   - [Modern Inputs (`Entry`, `SearchBar`, `PasswordEntry`, `Combobox`, `Spinbox`)](#54-modern-inputs)
   - [Interactive Calendar & DatePicker (`Calendar`, `DatePicker`)](#55-interactive-calendar--datepicker)
   - [Tabs & Navigation (`Notebook` / `TabView`, `SegmentedButton`)](#56-tabs--navigation)
   - [Data Tables & Scrollbars (`Treeview` / `DataTable`, `Scrollbar`)](#57-data-tables--scrollbars)
   - [Feedback & Overlays (`ProgressBar`, `Slider`, `Badge`, `Tooltip`, `Toast`, `Dialog`)](#58-feedback--overlays)
6. [Enterprise & Analytics Suite](#6-enterprise--analytics-suite)
   - [KPI Metric Cards (`MetricCard`)](#61-kpi-metric-cards)
   - [Scrollable Viewports (`ScrollableFrame`)](#62-scrollable-viewports)
   - [Application Status Bar (`StatusBar`)](#63-application-status-bar)
   - [Modal Progress Dialog (`ProgressDialog`)](#64-modal-progress-dialog)
   - [Glassmorphic Startup Splash Screen (`Splash`)](#65-glassmorphic-startup-splash-screen)
   - [Third-Party Integrations (`Matplotlib`, `tksheet`, Responsive Layouts)](#66-third-party-integrations)
   - [Animated Chronograph Timer, `BusyOverlay` & Uninterrupted Execution (`ActivityTimer`, `BusyOverlay`, `SubprocessWorker`, `TaskRunner`)](#67-animated-chronograph-timer-busyoverlay--uninterrupted-execution)
7. [Migrating from `sv_ttk` and `ttkbootstrap`](#7-migrating-from-sv_ttk-and-ttkbootstrap)
8. [Packaging & Releasing to GitHub / PyPI](#8-packaging--releasing-to-github--pypi)

---

## 1. Why ModernTtk?

Traditional Tkinter themes often force a trade-off:
- **`sv_ttk`** gives you gorgeous Windows 11 light/dark surfaces, but is limited to standard `ttk` widget types and static sprite-sheet themes.
- **`ttkbootstrap`** gives you semantic color roles (`primary`, `success`, `danger`) and extra utilities, but native `ttk` drawing still produces jagged or boxy corners on custom-sized buttons, inputs, and tables.

**ModernTtk** bridges both worlds with a **Hybrid Architecture**:
1. **Dynamic `ttk` Theme Engine**: Automatically styles all standard `ttk` widgets (`ttk.Button`, `ttk.Entry`, `ttk.Combobox`, `ttk.Treeview`, `ttk.Notebook`, `ttk.PanedWindow`, `ttk.LabelFrame`) so existing Tkinter code looks modern immediately.
2. **Supersampled Custom Widget Suite**: Provides drop-in custom widgets rendered at 4× resolution with `Pillow` (`ImageDraw.rounded_rectangle` + `LANCZOS` downsampling) and LRU-cached `PhotoImage` objects—delivering razor-sharp rounded corners, animated pill switches, interactive calendars, and modern data tables.

---

## 2. Installation & Requirements

- **Python**: `>= 3.10`
- **Dependencies**: `Pillow >= 9.5.0` (standard `tkinter` is included with Python)

### Local / Editable Installation
```bash
git clone https://github.com/<your-username>/modernttk.git
cd modernttk
pip install -e .
```

### Run the Built-In Showcase Gallery
```bash
python demo.py
```

---

## 3. Quick Start

You can either use `mtk.ModernWindow` as your root window, or apply ModernTtk to an existing `tk.Tk()` instance with `mtk.set_theme()`.

```python
import modernttk as mtk

# 1. Create a DPI-aware themed root window
app = mtk.ModernWindow(
    title="ModernTtk Quick Start",
    themename="fluent_dark",
    geometry="720x480",
)

# 2. Create an elevated rounded Card container
card = mtk.Card(
    app,
    title="Workspace Preferences",
    subtitle="Configure appearance, notifications, and deployment schedule.",
)
card.pack(fill="both", expand=True, padx=24, pady=24)

# 3. Add modern animated Switches, Checkboxes, and DatePicker inside `card.body`
mtk.Switch(
    card.body,
    text="Dark Mode Theme",
    bootstyle="primary",
    command=lambda: mtk.toggle_theme(app),
).pack(anchor="w", pady=6)

mtk.Checkbox(
    card.body,
    text="Enable real-time telemetry",
    bootstyle="success",
).pack(anchor="w", pady=6)

mtk.DatePicker(
    card.body,
    bootstyle="primary",
).pack(anchor="w", pady=10)

# 4. Add a rounded Pill Button that triggers a non-blocking Toast notification
mtk.Button(
    card.body,
    text="Save Changes",
    icon="🚀",
    bootstyle="primary-pill",
    command=lambda: mtk.Toast.show(
        app,
        title="Settings Saved",
        message="Your workspace configuration has been updated.",
        bootstyle="success",
    ),
).pack(anchor="w", pady=(14, 0))

app.mainloop()
```

---

## 4. Theming & Palette System

### Built-In Themes

ModernTtk ships with **10 built-in themes** spanning Windows 11 Fluent Design, Bootstrap/Tailwind palettes, and enterprise analytics themes:

| Theme Name | Mode | Aesthetic Inspiration | Primary Accent |
| :--- | :--- | :--- | :--- |
| `"fluent_dark"` | Dark | Windows 11 Fluent Dark (`sv_ttk` dark) | `#4cc2ff` (Sky Blue) |
| `"fluent_light"` | Light | Windows 11 Fluent Light (`sv_ttk` light) | `#0067c0` (Fluent Blue) |
| `"cosmo"` | Light | Clean Bootstrap / Modern Web Light | `#2563eb` (Royal Blue) |
| `"darkly"` | Dark | Deep Slate / Tailwind Dark | `#3b82f6` (Bright Blue) |
| `"cyborg"` | Dark | High-Contrast Zinc & Cyan | `#06b6d4` (Cyan) |
| `"minty"` | Light | Fresh Mint Teal & Coral | `#0d9488` (Teal) |
| `"dracula"` | Dark | Classic Dracula Purple & Neon Green | `#bd93f9` (Purple) |
| `"rccp_blue"` | Light | Enterprise Analytics Blue | `#2b8fcc` (Steel Blue) |
| `"rccp_teal"` | Light | Enterprise Analytics Teal | `#188c7e` (Deep Teal) |
| `"rccp_fuchsia"` | Light | Enterprise Analytics Pop Fuchsia | `#d6347e` (Fuchsia) |

### Semantic Color Roles (`bootstyle`)

Every widget accepts a `bootstyle` parameter supporting 8 semantic roles:
- `"primary"` (Default accent)
- `"secondary"` (Neutral / muted)
- `"success"` (Green / healthy / confirmed)
- `"info"` (Cyan / informational)
- `"warning"` (Amber / caution)
- `"danger"` (Red / destructive / alert)
- `"light"` (Light surface)
- `"dark"` (Dark surface)

Compound `bootstyle` strings work just like `ttkbootstrap`:
- `"success-outline"` — Outlined button or badge
- `"primary-pill"` — Capsule / pill button
- `"danger-outline-pill"` — Outlined capsule button
- `"info-subtle"` — Soft tinted background with accent text
- `"secondary-ghost"` — Transparent button that highlights on hover
- `"primary-link"` — Hyperlink-style button

### Switching & Toggling Themes at Runtime

All `ModernTtk` widgets subscribe automatically to `ThemeManager` and redraw seamlessly when the theme changes—including updating Windows 11 native DWM dark/light titlebars:

```python
import modernttk as mtk

# Apply a specific theme by name (or "system" to auto-detect OS dark/light mode!)
mtk.set_theme("system", root=app)
mtk.set_theme("dracula", root=app)

# Toggle between light and dark mode (e.g., fluent_dark <-> fluent_light)
mtk.toggle_theme(root=app)

# Convenience helpers (sv_ttk compatible)
mtk.use_dark_theme(root=app)
mtk.use_light_theme(root=app)

# Zero-refactor theming for an existing legacy tk/ttk widget tree:
mtk.auto_theme_tree(app)

# Inspect current theme name or palette object
current_name = mtk.get_theme()
palette = mtk.ThemeManager.instance().palette
```

### Creating Custom Themes (Dict or JSON)

You can register your own custom theme using a Python `dict`, a `ThemePalette` dataclass, or a `.json` file. Any omitted keys automatically inherit from `fluent_dark` or `fluent_light` based on `"mode"`:

```python
import modernttk as mtk

mtk.ThemeManager.instance().register_theme({
    "name": "nord_dark",
    "mode": "dark",
    "bg": "#2e3440",
    "surface": "#3b4252",
    "surface_alt": "#434c5e",
    "surface_hover": "#4c566a",
    "fg": "#eceff4",
    "fg_muted": "#d8dee9",
    "border": "#4c566a",
    "primary": "#88c0d0",
    "success": "#a3be8c",
    "warning": "#ebcb8b",
    "danger": "#bf616a",
})

mtk.set_theme("nord_dark", root=app)
```

Or load from a JSON file:
```python
mtk.ThemeManager.instance().load_theme_json("themes/nord_dark.json")
mtk.set_theme("nord_dark", root=app)
```

---

## 5. Core Widget Reference

All custom widgets are exported with both explicit `Modern*` names (e.g. `ModernButton`) and concise aliases (e.g. `mtk.Button`).

### 5.1 Window & Base Containers

#### `mtk.ModernWindow`
Root `tk.Tk` subclass that enables Windows High-DPI awareness (`SetProcessDpiAwareness`) and applies a theme on startup.
```python
app = mtk.ModernWindow(
    title="My App",
    themename="fluent_dark",
    geometry="1200x800",
)
```

#### `mtk.Frame` (`ModernFrame`) & `mtk.Label` (`ModernLabel`)
Theme-reactive replacements for `tk.Frame` and `tk.Label`. They automatically inherit their parent container's surface role (`"bg"`, `"surface"`, or `"surface_alt"`) so you never get mismatched background rectangles when switching themes.
```python
row = mtk.Frame(parent)
row.pack(fill="x", pady=4)

mtk.Label(row, text="Section Header", bold=True, font_size_delta=2).pack(side="left")
mtk.Label(row, text="Secondary description", muted=True).pack(side="left", padx=8)
mtk.Label(row, text="Active", bootstyle="success").pack(side="right")
```

#### `mtk.Card` (`ModernCard`)
Elevated anti-aliased rounded container with an optional `title` and `subtitle`. Place child widgets inside **`card.body`**.
```python
card = mtk.Card(
    parent,
    title="Server Configuration",
    subtitle="Manage cluster endpoints and timeouts.",
    padding=18,
    radius=12,              # Optional custom corner radius
    surface_role="surface", # "surface" or "surface_alt"
)
card.pack(fill="both", expand=True)

# Add children to `card.body`
mtk.Button(card.body, text="Deploy", bootstyle="primary").pack(anchor="w")
```

---

### 5.2 Rounded Buttons

#### `mtk.Button` (`ModernButton`)
Anti-aliased rounded button with smooth hover interpolation, press animation, keyboard focus (`<Return>` / `<space>`), and icon prefix support.

```python
btn = mtk.Button(
    parent,
    text="Launch Build",
    icon="🚀",
    bootstyle="primary",       # or "success-outline", "danger-pill", "info-subtle", "secondary-ghost", "primary-link"
    variant="filled",          # "filled", "outline", "subtle", "ghost", "link"
    pill=False,                # True for capsule/pill ends
    radius=8,                  # Custom corner radius in px
    height=36,
    padx=18,
    state="normal",            # "normal" or "disabled"
    command=lambda: print("Clicked!"),
)
btn.pack(side="left", padx=6)

# Update dynamically at runtime:
btn.configure_button(text="Building...", bootstyle="warning", state="disabled")
```

---

### 5.3 Animated Toggles

#### `mtk.Switch` (`ModernSwitch`)
Windows 11 Fluent-inspired sliding pill toggle switch.
```python
sync_var = tk.BooleanVar(value=True)
sw = mtk.Switch(
    parent,
    text="Enable Automatic Sync",
    variable=sync_var,
    bootstyle="primary",
    command=lambda: print("Switch state:", sw.get()),
)
sw.pack(anchor="w", pady=4)

# Programmatic access:
sw.set(False)
is_on = sw.get()
```

#### `mtk.Checkbox` (`ModernCheckbox`)
Rounded checkbox with animated checkmark draw-in and indeterminate (`—`) state support.
```python
cb = mtk.Checkbox(
    parent,
    text="Auto-format on Save",
    bootstyle="success",
    indeterminate=False,
    command=lambda: print("Checked:", cb.get()),
)
cb.set(True)
cb.pack(anchor="w", pady=4)

# Toggle indeterminate dash state:
cb.set_indeterminate(True)
```

#### `mtk.RadioButton` (`ModernRadioButton`)
Circular radio button with animated inner dot.
```python
plan_var = tk.StringVar(value="pro")
mtk.RadioButton(parent, text="Starter", variable=plan_var, value="starter").pack(anchor="w")
mtk.RadioButton(parent, text="Pro Plan", variable=plan_var, value="pro", bootstyle="success").pack(anchor="w")
```

---

### 5.4 Modern Inputs

#### `mtk.Entry` (`ModernEntry`)
Rounded text input with placeholder text, prefix/suffix icons, and an accent border on focus.
```python
entry = mtk.Entry(
    parent,
    placeholder="Enter workspace name...",
    prefix_icon="👤",
    width=280,
    height=38,
    bootstyle="primary",
)
entry.pack(anchor="w", pady=6)

print(entry.get())
entry.set("Production Workspace")

# Live semantic validation states ("error"/"danger", "warning", "success", "info", or None):
entry.set_validation("error", "✖ Invalid workspace handle or unreachable host")
entry.set_validation("success", "✔ Endpoint verified")
entry.set_validation(None)  # Clear validation state
```

#### `mtk.TagInput` / `mtk.Chips` (`ModernTagInput`)
Rounded multi-tag chip box where pressing `<Return>` or `,` adds a removable pill chip (`tag ✕`).
```python
chips = mtk.TagInput(
    parent,
    tags=["production", "us-east-1", "gpu-node"],
    bootstyle="primary",
    width=360,
    on_change=lambda tags: print("Active tags:", tags),
)
chips.pack(anchor="w", pady=6)
chips.add_tag("auto-scaled")
```

#### `mtk.SearchBar` (`ModernSearchBar`)
Rounded search input with `🔍` icon, clickable `✕` clear button, and live search callback.
```python
search = mtk.SearchBar(
    parent,
    placeholder="Filter resources...",
    width=300,
    on_search=lambda query: print("Filtering by:", query),
)
search.pack(anchor="w", pady=6)
```

#### `mtk.PasswordEntry` (`ModernPasswordEntry`)
Rounded password input with clickable `👁` / `🙈` visibility toggle.
```python
pwd = mtk.PasswordEntry(parent, placeholder="API Secret Key", width=280)
pwd.pack(anchor="w", pady=6)
```

#### `mtk.Combobox` (`ModernCombobox`)
Rounded dropdown selector with a themed floating popup list.
```python
combo = mtk.Combobox(
    parent,
    values=["Daily", "Weekly", "Monthly"],
    default="Weekly",
    width=180,
    command=lambda val: print("Selected view:", val),
)
combo.pack(anchor="w", pady=6)
```

#### `mtk.Spinbox` (`ModernSpinbox`)
Rounded numeric stepper with integrated `−` and `+` buttons and Up/Down arrow key bindings.
```python
spin = mtk.Spinbox(
    parent,
    from_=1,
    to=100,
    step=1,
    value=12,
    width=140,
    command=lambda val: print("Value:", val),
)
spin.pack(anchor="w", pady=6)
```

---

### 5.5 Interactive Calendar & DatePicker

#### `mtk.Calendar` (`ModernCalendar`)
Interactive month/year calendar with header drill-down (Click `Month Year ▾` to switch to Month Grid → Year Grid), `Today` shortcut, single or date-range selection, and custom date highlighting for holidays/events.

```python
import datetime as dt

# Single-date mode:
cal = mtk.Calendar(
    parent,
    selected_date=dt.date.today(),
    select_mode="single",      # "single" or "range"
    bootstyle="primary",
    on_select=lambda d: print("Picked date:", d),
)
cal.pack(side="left", padx=8)

# Highlight specific dates (e.g., holidays, fiscal start/end):
cal.highlight_date(dt.date(2026, 12, 25), bootstyle="danger")
cal.highlight_date(dt.date(2026, 10, 30), bootstyle="warning")
# cal.unhighlight_date(dt.date(2026, 10, 30))
# cal.clear_highlights()
```

#### `mtk.DatePicker` (`ModernDatePicker`)
Rounded date input field with `📅` icon that opens a popup `ModernCalendar` on click.
```python
picker = mtk.DatePicker(
    parent,
    date_format="%Y-%m-%d",
    bootstyle="primary",
    on_select=lambda d: print("Date selected:", d),
)
picker.pack(anchor="w", pady=6)
```

---

### 5.6 Tabs & Navigation

#### `mtk.Notebook` / `mtk.TabView` (`ModernNotebook`)
Modern tabbed notebook supporting three visual variants (`"underline"`, `"pills"`, `"cards"`), tab icons, notification badges, and optional close (`✕`) buttons.

```python
nb = mtk.Notebook(
    parent,
    variant="underline",       # "underline", "pills", or "cards"
    bootstyle="primary",
    closeable=False,           # Default closeable setting for tabs
    on_tab_change=lambda title: print("Switched to tab:", title),
)
nb.pack(fill="both", expand=True)

# Method 1: Create and return a themed ModernFrame for the tab
tab_overview = nb.add("Overview", icon="📊", badge="New")
mtk.Label(tab_overview, text="Welcome to Overview", bold=True).pack(anchor="w")

# Method 2: Add an existing Frame (ttk.Notebook compatible)
settings_frame = mtk.Frame(nb)
nb.add(settings_frame, text="Settings", icon="⚙", closeable=True)

# Programmatic tab selection:
nb.select("Overview")
```

#### `mtk.SegmentedButton` (`ModernSegmentedButton`)
Compact animated pill/segmented switcher with sliding active indicator.
```python
seg = mtk.SegmentedButton(
    parent,
    values=["Daily", "Weekly", "Monthly"],
    default="Weekly",
    pill=True,
    bootstyle="primary",
    command=lambda val: print("View:", val),
)
seg.pack(anchor="w", pady=6)
```

---

### 5.7 Data Tables & Scrollbars

#### `mtk.Treeview` / `mtk.DataTable` (`ModernTreeview`)
Modern rounded data table with a custom anti-aliased header bar, interactive column sorting (`▲` / `▼` for both numbers and strings), alternating striped rows, hover row highlighting, semantic row tags, and an integrated `ModernScrollbar`.

```python
columns = [
    ("id", "Resource ID", 120),
    ("name", "Resource Name", 220),
    ("utilization", "Utilization", 130),
    ("status", "Status", 140),
]

table = mtk.DataTable(
    parent,
    columns=columns,
    height=8,
    striped=True,
    sortable=True,
    bootstyle="primary",
    on_select=lambda rows: print("Selected rows:", rows),
)
table.pack(fill="both", expand=True)

# Insert rows with optional semantic color tags ("success", "warning", "danger", "info", "primary")
table.insert_row(("RES-01", "CNC Milling Cell A", "92.4%", "● Optimal"), tag="success")
table.insert_row(("RES-02", "Laser Cutter B", "108.2%", "⚠ Overloaded"), tag="danger")
table.insert_row(("RES-03", "Assembly Line 4", "74.0%", "● Normal"))
```

---

### 5.8 Feedback & Overlays

#### `mtk.ProgressBar` (`ModernProgressBar`) & `mtk.Slider` (`ModernSlider`)
```python
# Determinate progress bar with percentage text
pb = mtk.ProgressBar(parent, value=65, show_percent=True, bootstyle="primary", width=300)
pb.pack(pady=6)

# Indeterminate animated progress bar
pb_ind = mtk.ProgressBar(parent, mode="indeterminate", bootstyle="info", width=300)
pb_ind.pack(pady=6)

# Interactive slider linked to progress bar
slider = mtk.Slider(parent, from_=0, to=100, value=65, command=pb.set, width=300)
slider.pack(pady=6)
```

#### `mtk.Badge` (`ModernBadge`) & `mtk.Tooltip` (`ModernTooltip`)
```python
badge = mtk.Badge(parent, text="● Live", bootstyle="success-subtle")
badge.pack(side="left", padx=4)

mtk.Tooltip(badge, text="All cluster services are healthy")
```

#### `mtk.Toast` (`ModernToast`) & `mtk.Dialog` (`ModernDialog`)
```python
# Non-blocking floating toast notification anchored to bottom-right
mtk.Toast.show(
    app,
    title="Export Complete",
    message="Saved report to Exported Data/report.pdf",
    bootstyle="success",
    duration_ms=3200,
)

# Modal confirmation dialog
dlg = mtk.Dialog(
    app,
    title="Delete Selected Resources?",
    message="This action will remove 3 resources from the database.",
    confirm_text="Delete",
    cancel_text="Cancel",
    bootstyle="danger",
)
app.wait_window(dlg)
if dlg.result:
    print("Confirmed!")
```

---

### 5.9 Gauges, Code/Log Consoles & Expanders

#### `mtk.Meter` (`ModernMeter`)
4× supersampled radial arc gauge (`ttkbootstrap.Meter` hybrid replacement) with smooth animated sweeps, interactive pointer dragging, and automatic semantic color thresholds:
```python
meter = mtk.Meter(
    parent,
    value=72,
    maximum=100,
    size=160,
    thickness=12,
    arcrange=260,               # Set to 360 for a full circular ring
    subtext="CPU Load",
    bootstyle="success",
    thresholds=[(70, "warning"), (88, "danger")],  # Auto-changes color as value rises!
    interactive=True,           # Allow clicking/dragging the dial
)
meter.pack(side="left", padx=8)

# Animate to a new value:
meter.set(91, animate=True)
```

#### `mtk.Text` / `mtk.Textarea` (`ModernText`)
Rounded multi-line text / code / log editor with focus border ring, integrated `ModernScrollbar`, optional line-number gutter, and semantic colored log levels:
```python
log_box = mtk.Textarea(
    parent,
    line_numbers=True,
    monospace=True,
    height=160,
)
log_box.pack(fill="both", expand=True)

log_box.append_log("Service initialized on port 8080", "INFO")
log_box.append_log("Database connection healthy", "SUCCESS")
log_box.append_log("High memory utilization on node-03", "WARNING")
log_box.append_log("Replica timeout on shard #2", "ERROR")
```

#### `mtk.Accordion` / `mtk.Expander` (`ModernAccordion`)
Windows 11 Settings-style collapsible section card with rotating vector chevron (`▾` / `▸`). Place child widgets inside **`expander.body`**:
```python
exp = mtk.Accordion(
    parent,
    title="Automated Backup Schedule",
    subtitle="Configure snapshot retention and S3 replication.",
    icon="download",
    expanded=True,
)
exp.pack(fill="x", pady=6)

mtk.Switch(exp.body, text="Enable hourly snapshots", bootstyle="success").pack(anchor="w")
```

---

### 5.10 Sidebar Rail, Context Menus, Command Palette & Vector Icons

#### `mtk.Sidebar` (`ModernSidebar`)
Collapsible Windows 11 Fluent left navigation rail supporting expanded mode (`icon + label + badge`) and collapsed mode (`icon-only` rail):
```python
sidebar = mtk.Sidebar(
    app,
    title="Workspace",
    expanded_width=210,
    collapsed_width=60,
    on_select=lambda key: print("Navigated to:", key),
)
sidebar.pack(side="left", fill="y")

sidebar.add_section("Core")
sidebar.add_item("dashboard", "Dashboard", icon="sliders", badge="Live")
sidebar.add_item("calendar", "Schedule", icon="calendar")
sidebar.add_section("System")
sidebar.add_item("logs", "System Logs", icon="terminal", badge="4")

# Toggle between expanded and icon-only collapsed rail:
# sidebar.toggle_collapse()
```

#### `mtk.ContextMenu` / `mtk.Menu` (`ModernContextMenu`)
Floating, rounded dark/light themed popup menu replacing native `tk.Menu`:
```python
menu = mtk.ContextMenu(app)
menu.add_command("Open Command Palette", command=palette.show, icon="search", accelerator="Ctrl+K", bootstyle="primary")
menu.add_command("Refresh Data", command=refresh_fn, icon="refresh", accelerator="F5")
menu.add_separator()
menu.add_command("Delete Resource", command=delete_fn, icon="trash", bootstyle="danger")

# Bind right-click (<Button-3>) to any widget or window:
menu.bind_context(app)

# Or open below a dropdown button:
# menu.show_under(dropdown_btn)
```

#### `mtk.CommandPalette` (`ModernCommandPalette`)
VS Code / Raycast-style `Ctrl+K` floating command spotlight modal:
```python
cmd = mtk.CommandPalette(app, bootstyle="primary")
cmd.bind_shortcut("<Control-k>")

cmd.register("Switch Light / Dark Mode", callback=lambda: mtk.toggle_theme(app), category="Theme", icon="sun", shortcut="Alt+T")
cmd.register("Export Capacity Report", callback=export_fn, category="Action", icon="download", shortcut="Ctrl+E")
```

#### Procedural 4× Vector Icon Engine (`mtk.icon`)
Render 28 built-in vector icons at any size or color without external asset files (`"search"`, `"check"`, `"close"`, `"plus"`, `"minus"`, `"chevron_down"`, `"chevron_up"`, `"chevron_left"`, `"chevron_right"`, `"settings"`, `"sun"`, `"moon"`, `"user"`, `"lock"`, `"eye"`, `"eye_off"`, `"calendar"`, `"download"`, `"upload"`, `"trash"`, `"refresh"`, `"info"`, `"warning"`, `"filter"`, `"folder"`, `"terminal"`, `"sliders"`, `"sparkles"`):
```python
# Pass directly to Button, Entry, Sidebar, Accordion, or ContextMenu:
mtk.Button(parent, text="Export", icon="download", bootstyle="primary")

# Or generate a Tkinter PhotoImage directly:
photo = mtk.icon("settings", size=18, color="#4cc2ff")
```

---

## 6. Enterprise & Analytics Suite

### 6.1 KPI Metric Cards (`mtk.MetricCard`)
Rounded KPI dashboard card displaying an uppercase title, large metric value, semantic left accent bar, icon, and a delta pill badge:
```python
kpi = mtk.MetricCard(
    parent,
    title="Total Demand (hrs)",
    value="4,820.5",
    delta="+6.4% wk",
    icon="📈",
    bootstyle="primary",
    width=250,
    height=92,
)
kpi.pack(side="left", padx=8)

# Update live metrics:
kpi.set_metric(value="5,120.0", delta="+12.1% wk", bootstyle="success")
```

### 6.2 Scrollable Viewports (`mtk.ScrollableFrame`)
Mousewheel-scrollable container with an auto-hiding `ModernScrollbar`. Add child widgets inside **`scroll.body`**:
```python
scroll = mtk.ScrollableFrame(parent, surface_role="surface", padding=12)
scroll.pack(fill="both", expand=True)

for i in range(30):
    mtk.Switch(scroll.body, text=f"Enable Worker Node #{i + 1}").pack(anchor="w", pady=4)
```

### 6.3 Application Status Bar (`mtk.StatusBar`)
Bottom status bar with status message on the left and automatic `Selected`, `Sum`, and `Average` calculators on the right:
```python
status_bar = mtk.StatusBar(app, status_text="Status: Ready", show_stats=True)
status_bar.pack(side="bottom", fill="x")

status_bar.set_status("Status: Calculating capacity...")
status_bar.update_stats([120.5, 84.0, 95.5, 110.0])  # Updates Selected: 4 | Sum: 410.00 | Average: 102.50
```

### 6.4 Modal Progress Dialog (`mtk.ProgressDialog`)
Centered modal progress window with disabled window close button while work is running:
```python
dlg = mtk.ProgressDialog(
    app,
    title="Importing Data Source",
    message="Reading Excel workbook...",
    bootstyle="primary",
)
dlg.update(45, "Validating resource mappings...")
dlg.update(90, "Writing rows to SQLite...")
dlg.destroy()
```

### 6.5 Glassmorphic Startup Splash Screen (`mtk.Splash`)
Borderless rounded splash screen with ambient radial glow, vector gauge dial, and smooth progress bar:
```python
app.withdraw()
splash = mtk.Splash(
    app,
    title="RCCP Analytics Suite",
    subtitle="Rough Cut Capacity Planning & Simulation Engine",
    version="v1.2.0 Official Release",
    footer="Designed by Andrew Thomas",
    bootstyle="info",
)
splash.update_progress(50, "Loading database & holiday calendars...")
splash.update_progress(100, "Ready")
splash.finish()
app.deiconify()
```

### 6.6 Third-Party Integrations (`Matplotlib`, `tksheet`, Responsive Layouts)

ModernTtk includes built-in theme adapters so scientific/data libraries match your active theme automatically:

```python
import modernttk as mtk

# 1. Style a Matplotlib Figure, Axes, and NavigationToolbar2Tk
mtk.style_matplotlib_figure(figure, ax)
mtk.style_matplotlib_toolbar(toolbar)
canvas.draw_idle()

# 2. Style a tksheet.Sheet widget
mtk.style_tksheet(sheet)

# 3. Re-style automatically whenever the user switches themes:
mtk.ThemeManager.instance().subscribe(lambda palette: (
    mtk.style_matplotlib_figure(figure, ax, palette),
    mtk.style_matplotlib_toolbar(toolbar, palette),
    canvas.draw_idle(),
    mtk.style_tksheet(sheet, palette),
))

# 4. Responsive toolbar section wrapping (stacks vertically below breakpoint width)
mtk.bind_responsive_sections(toolbar_frame, [filter_section, actions_section], breakpoint=850)
```

### 6.7 Animated Chronograph Timer, `BusyOverlay` & Uninterrupted Execution

When an application updates a preview canvas or runs heavy background work, users need continuous visual feedback that never freezes mid-task. ModernTtk ships a high-DPI 36-frame chronograph timer and an uninterrupted execution architecture (`modernttk/widgets/timer.py`):

#### 1. Standalone Animated Chronograph Widget (`mtk.ActivityTimer` / `mtk.ChronoTimer`)
Renders a `168×188` subpixel-anti-aliased frosted glassmorphic chronograph medallion (with 12 wake-illuminated dial ticks, a tapered conical comet sweep with leading bloom halo, a rotating stopwatch hand, and a 2× supersampled `"1.2s • 65%"` readout pill) at 30 FPS (`33 ms`):
```python
timer = mtk.ActivityTimer(parent, bootstyle="primary", autostart=True)
timer.pack(pady=8)

# Advance progress monotonically and glide smoothly toward the next stage ceiling:
timer.set_progress(35.0, ceiling=64.0)
timer.stop()
```

#### 2. Non-Blocking Canvas Busy Overlay (`mtk.BusyOverlay` / `ModernBusyOverlay`)
Attaches the centered `168×188` animated chronograph timer (`tag="busy_overlay"`) over one or more target `tk.Canvas` viewports (e.g., edited output canvases, while leaving original/reference canvases untouched) and synchronizes an optional `ModernProgressBar`:
```python
busy_overlay = mtk.BusyOverlay(
    app,
    canvases=(canvas_edited, canvas_inspector),  # Never touches original/reference canvases
    progress_bar=progress_bar,
    bootstyle="primary",
)

# Start 30 FPS rotation + automatic stage-ceiling progress gliding:
busy_overlay.start(initial_pct=5.0, initial_ceiling=16.0)
busy_overlay.set_progress(38.0)   # Glides smoothly toward 64% between milestones
busy_overlay.stop()               # Clears "busy_overlay" items from all canvases
```

#### 3. Why Timers Freeze at ~35% & How to Run Uninterrupted (`mtk.SubprocessWorker` + `mtk.TaskRunner`)
- **The Problem**: Python's `threading.Thread` shares a single Global Interpreter Lock (GIL) with the Tkinter GUI thread. If a background thread calls a native C/Rust extension (`vtracer`, `resvg_py`, heavy image/numerical kernels) that holds the GIL for 0.5–1.5 seconds, Tkinter's `after(33, ...)` loop is starved and the animated clock stops mid-spin (e.g., at 35%).
- **The Solution (Two-Part Uninterrupted Architecture)**:
  1. **GIL-Free Subprocess Offloading (`mtk.SubprocessWorker` + `mtk.run_subprocess_worker_loop`)**: Execute GIL-holding native extensions inside a persistent child process over length-prefixed binary stdio IPC (`ModernSubprocessWorker.should_offload()`). Pre-warm the worker on startup (`worker.prewarm()`) so the main Tkinter process never experiences GIL contention.
  2. **Stage-Ceiling Gliding + `mtk.TaskRunner`**: Stream fine-grained `(pct, message)` milestones over a `queue.SimpleQueue` polled every `25 ms`, while `ModernBusyOverlay` glides `pct` smoothly toward the current stage ceiling (`step = max(0.22, (ceiling - pct) * 0.055)`) on every `33 ms` tick:

```python
import sys
import modernttk as mtk

# 1. Early in your entrypoint (before GUI imports), handle the worker flag:
if len(sys.argv) >= 2 and sys.argv[1] == "--native-worker":
    raise SystemExit(mtk.run_subprocess_worker_loop({
        "heavy_op": lambda data: run_native_extension(data),
    }))

# 2. Create & pre-warm the persistent GIL-free subprocess client:
WORKER = mtk.SubprocessWorker(script_path=__file__, worker_flag="--native-worker")
WORKER.prewarm()

# 3. Coordinate background tasks with uninterrupted 30 FPS overlay animation:
runner = mtk.TaskRunner(app, overlay=busy_overlay, progress_bar=progress_bar)
runner.start(
    lambda progress_cb: (
        progress_cb(30.0, "Running native stage in GIL-free worker..."),
        WORKER.request(("heavy_op", payload)),
    )[-1],
    on_done=lambda result: render_output(result),
)
```

---

## 7. Migrating from `sv_ttk` and `ttkbootstrap`

### From `sv_ttk`
| `sv_ttk` | `modernttk` |
| :--- | :--- |
| `import sv_ttk` | `import modernttk as mtk` |
| `sv_ttk.set_theme("dark")` | `mtk.set_theme("fluent_dark")` (or `mtk.set_theme("dark")`) |
| `sv_ttk.set_theme("light")` | `mtk.set_theme("fluent_light")` (or `mtk.set_theme("light")`) |
| `sv_ttk.toggle_theme()` | `mtk.toggle_theme()` |
| `sv_ttk.use_dark_theme()` | `mtk.use_dark_theme()` |
| `sv_ttk.use_light_theme()` | `mtk.use_light_theme()` |

### From `ttkbootstrap`
| `ttkbootstrap` | `modernttk` |
| :--- | :--- |
| `tb.Window(themename="darkly")` | `mtk.ModernWindow(themename="darkly")` |
| `tb.Button(parent, text="OK", bootstyle="success-outline")` | `mtk.Button(parent, text="OK", bootstyle="success-outline")` |
| `tb.Checkbutton(parent, bootstyle="round-toggle")` | `mtk.Switch(parent, bootstyle="primary")` |
| `tb.DateEntry(parent)` | `mtk.DatePicker(parent)` |
| `tb.Notebook(parent, bootstyle="primary")` | `mtk.Notebook(parent, bootstyle="primary")` |

---

## 8. Packaging & Releasing to GitHub / PyPI

If you decide to publish **ModernTtk** to GitHub and PyPI for the broader Python community:

### 1. Repository Structure
```text
ModernTtk/
├── modernttk/
│   ├── __init__.py          # Public API & ergonomic aliases
│   ├── icons.py             # 28 procedural 4x supersampled vector icons
│   ├── style.py             # ThemeManager, OS theme detection & auto_theme_tree
│   ├── themes.py            # ThemePalette & 10 built-in palettes
│   ├── utils.py             # 4x supersampled Pillow shape renderers & cache
│   └── widgets/
│       ├── __init__.py
│       ├── base.py          # ThemedWidgetMixin, ModernFrame, ModernLabel
│       ├── buttons.py       # ModernButton (with vector icon support)
│       ├── toggles.py       # ModernSwitch, ModernCheckbox, ModernRadioButton
│       ├── inputs.py        # ModernEntry, SearchBar, PasswordEntry, Combobox, Spinbox + validation
│       ├── calendar.py      # ModernCalendar (with highlight_date), ModernDatePicker
│       ├── containers.py    # ModernCard, ModernNotebook, ModernSegmentedButton, Badge, Tooltip
│       ├── feedback.py      # ModernProgressBar, ModernSlider, ModernToast, ModernDialog
│       ├── table.py         # ModernTreeview (DataTable), ModernScrollbar
│       ├── advanced.py      # ModernMeter, ModernText (Code/Log), ModernAccordion, ModernTagInput
│       ├── navigation.py    # ModernSidebar, ModernContextMenu, ModernCommandPalette (Ctrl+K)
│       ├── timer.py         # ActivityTimer, BusyOverlay, SubprocessWorker & TaskRunner (Uninterrupted 30 FPS)
│       └── enterprise.py    # MetricCard, StatusBar, ScrollableFrame, ProgressDialog, Splash, Adapters
├── demo.py                  # Interactive 5-page showcase gallery with Sidebar & Ctrl+K
├── instructions.md          # Complete developer documentation & API reference
├── README.md                # GitHub landing page
└── pyproject.toml           # PEP 621 package metadata
```

### 2. Initialize Git & Push to GitHub
```bash
cd p:\ModernTtk
git init
git add .
git commit -m "Initial release of ModernTtk v0.1.0"
git branch -M main
git remote add origin https://github.com/<your-username>/modernttk.git
git push -u origin main
```

### 3. Build & Publish to PyPI
```bash
pip install build twine
python -m build
twine upload dist/*
```

### 4. PyInstaller / Nuitka Compilation Notes
Because `ModernTtk` generates all rounded shapes, checkmarks, and splash cards procedurally in memory via `Pillow` (`PIL.ImageDraw`) rather than relying on external `.tcl` scripts or sprite-sheet image folders, **it requires zero extra `--add-data` theme asset flags** when freezing applications with PyInstaller or Nuitka.

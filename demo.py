"""Interactive Showcase Gallery for ModernTkk.

Run with:
    python demo.py
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import ttk

import moderntkk as mtk


class ShowcaseApp(mtk.ModernWindow):
    def __init__(self) -> None:
        super().__init__(
            title="ModernTkk — Hybrid Fluent & Bootstrap UI Suite for Tkinter",
            themename="fluent_dark",
            geometry="1280x880",
        )
        self._build_header()
        self._build_main_area()
        self._setup_command_palette()
        self._setup_global_context_menu()

    def _build_header(self) -> None:
        self.header = mtk.ModernFrame(self, surface_role="surface", padx=20, pady=12)
        self.header.pack(fill="x")

        left = mtk.ModernFrame(self.header)
        left.pack(side="left")

        self.title_lbl = mtk.ModernLabel(
            left,
            text="✦ ModernTkk Studio",
            font_size_delta=4,
            bold=True,
        )
        self.title_lbl.pack(side="left", padx=(0, 10))

        mtk.ModernBadge(left, text="v0.2.0", bootstyle="primary-subtle").pack(side="left", padx=4)

        # Navigation segmented button
        self.nav_seg = mtk.ModernSegmentedButton(
            self.header,
            values=[
                "Components",
                "Calendar & Inputs",
                "Tabs & Data",
                "Gauges, Logs & Pro",
                "Enterprise & RCCP",
            ],
            default="Components",
            command=self._switch_page,
            pill=True,
        )
        self.nav_seg.pack(side="left", padx=18)

        right = mtk.ModernFrame(self.header)
        right.pack(side="right")

        self.cmd_btn = mtk.ModernButton(
            right,
            text="Ctrl+K Actions",
            icon="search",
            bootstyle="primary-subtle",
            height=34,
            padx=12,
            command=lambda: self.cmd_palette.show(),
        )
        self.cmd_btn.pack(side="left", padx=(0, 10))

        self.theme_lbl = mtk.ModernLabel(
            right,
            text="Theme:",
            muted=True,
        )
        self.theme_lbl.pack(side="left", padx=(0, 6))

        self.theme_combo = mtk.ModernCombobox(
            right,
            values=mtk.ThemeManager.instance().list_themes(),
            default=mtk.get_theme(),
            command=self._on_theme_pick,
            width=142,
            height=34,
        )
        self.theme_combo.pack(side="left", padx=(0, 8))

        self.mode_btn = mtk.ModernButton(
            right,
            text="Toggle",
            icon="sun",
            bootstyle="secondary-outline",
            height=34,
            padx=12,
            command=self._on_toggle_mode,
        )
        self.mode_btn.pack(side="left")

    def _on_theme_pick(self, theme_name: str) -> None:
        mtk.set_theme(theme_name, root=self)

    def _on_toggle_mode(self) -> None:
        new_p = mtk.toggle_theme(root=self)
        self.theme_combo.set(new_p.name, notify=False)

    def _build_main_area(self) -> None:
        self.status_bar = mtk.ModernStatusBar(
            self,
            status_text="Status: Ready — Press Ctrl+K for Command Palette or Right-Click anywhere for Context Menu",
            show_stats=True,
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.update_stats([11.4, 28.9, 19.1, 42.0, 89.4, 15.2])

        self.body_wrap = mtk.ModernFrame(self)
        self.body_wrap.pack(fill="both", expand=True)

        # Collapsible Left Navigation Sidebar Rail
        self.sidebar = mtk.ModernSidebar(
            self.body_wrap,
            title="Workspace",
            expanded_width=206,
            collapsed_width=58,
            on_select=self._on_sidebar_select,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.add_section("Core Suite")
        self.sidebar.add_item("Components", "Components", icon="sliders", badge="20+")
        self.sidebar.add_item("Calendar & Inputs", "Calendar & Inputs", icon="calendar")
        self.sidebar.add_item("Tabs & Data", "Tabs & Data", icon="folder", badge="6")
        self.sidebar.add_section("Advanced & Pro")
        self.sidebar.add_item("Gauges, Logs & Pro", "Gauges, Logs & Pro", icon="terminal", badge="New")
        self.sidebar.add_item("Enterprise & RCCP", "Enterprise & RCCP", icon="settings")

        self.pages_container = mtk.ModernFrame(self.body_wrap, padx=18, pady=18)
        self.pages_container.pack(side="left", fill="both", expand=True)

        self.pages: dict[str, mtk.ModernFrame] = {
            "Components": mtk.ModernFrame(self.pages_container),
            "Calendar & Inputs": mtk.ModernFrame(self.pages_container),
            "Tabs & Data": mtk.ModernFrame(self.pages_container),
            "Gauges, Logs & Pro": mtk.ModernFrame(self.pages_container),
            "Enterprise & RCCP": mtk.ModernFrame(self.pages_container),
        }

        self._populate_components_page(self.pages["Components"])
        self._populate_calendar_inputs_page(self.pages["Calendar & Inputs"])
        self._populate_ttk_page(self.pages["Tabs & Data"])
        self._populate_pro_page(self.pages["Gauges, Logs & Pro"])
        self._populate_enterprise_page(self.pages["Enterprise & RCCP"])

        self._switch_page("Components")

    def _on_sidebar_select(self, page_name: str) -> None:
        self.nav_seg.set(page_name, notify=False)
        self._switch_page(page_name)

    def _switch_page(self, page_name: str) -> None:
        for frame in self.pages.values():
            frame.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)
        if self.sidebar.get() != page_name:
            self.sidebar.select(page_name, notify=False)
        if self.nav_seg.get() != page_name:
            self.nav_seg.set(page_name, notify=False)

    def _setup_command_palette(self) -> None:
        self.cmd_palette = mtk.ModernCommandPalette(self, bootstyle="primary")
        self.cmd_palette.bind_shortcut("<Control-k>")

        for page_name in self.pages:
            self.cmd_palette.register(
                f"Go to {page_name}",
                callback=lambda p=page_name: self._switch_page(p),
                category="Navigate",
                icon="chevron_right",
            )
        self.cmd_palette.register(
            "Toggle Light / Dark Mode",
            callback=self._on_toggle_mode,
            category="Theme",
            icon="sun",
            shortcut="Alt+T",
        )
        self.cmd_palette.register(
            "Toggle Sidebar Collapse / Expand",
            callback=self.sidebar.toggle_collapse,
            category="Layout",
            icon="sliders",
            shortcut="Ctrl+B",
        )
        for th_name in mtk.ThemeManager.instance().list_themes():
            self.cmd_palette.register(
                f"Apply Theme: {th_name}",
                callback=lambda t=th_name: (mtk.set_theme(t, root=self), self.theme_combo.set(t, notify=False)),
                category="Theme",
                icon="sparkles",
            )

    def _setup_global_context_menu(self) -> None:
        self.ctx_menu = mtk.ModernContextMenu(self, width=240)
        self.ctx_menu.add_command(
            "Open Command Palette",
            command=lambda: self.cmd_palette.show(),
            icon="search",
            accelerator="Ctrl+K",
            bootstyle="primary",
        )
        self.ctx_menu.add_command(
            "Toggle Sidebar Rail",
            command=self.sidebar.toggle_collapse,
            icon="sliders",
        )
        self.ctx_menu.add_command(
            "Switch Light / Dark Mode",
            command=self._on_toggle_mode,
            icon="sun",
        )
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(
            "Trigger Toast Notification",
            command=lambda: mtk.ModernToast.show(
                self,
                title="Context Action Executed",
                message="Invoked from ModernContextMenu!",
                bootstyle="info",
            ),
            icon="info",
        )
        self.ctx_menu.add_command(
            "Clear Selection Cache",
            command=lambda: self.status_bar.set_status("Status: Selection cache cleared"),
            icon="trash",
            bootstyle="danger",
        )
        self.ctx_menu.bind_context(self)

    def _populate_components_page(self, parent: mtk.ModernFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # 1. Rounded Buttons Card
        btn_card = mtk.ModernCard(
            parent,
            title="Rounded Buttons & Semantic Variants",
            subtitle="Supersampled anti-aliased geometry with filled, outline, subtle, ghost, and pill options.",
        )
        btn_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        row1 = mtk.ModernFrame(btn_card.body)
        row1.pack(fill="x", pady=(4, 8))
        for role in ("primary", "secondary", "success", "info", "warning", "danger"):
            b = mtk.ModernButton(row1, text=role.capitalize(), bootstyle=role, padx=14)
            b.pack(side="left", padx=(0, 8))
            mtk.ModernTooltip(b, f"Filled '{role}' semantic button")

        row2 = mtk.ModernFrame(btn_card.body)
        row2.pack(fill="x", pady=8)
        for role in ("primary", "success", "warning", "danger"):
            mtk.ModernButton(
                row2,
                text=f"{role.capitalize()} Outline",
                bootstyle=f"{role}-outline",
                padx=14,
            ).pack(side="left", padx=(0, 8))

        row3 = mtk.ModernFrame(btn_card.body)
        row3.pack(fill="x", pady=8)
        mtk.ModernButton(row3, text="Pill Action", icon="🚀", bootstyle="primary-pill").pack(side="left", padx=(0, 8))
        mtk.ModernButton(row3, text="Subtle Tag", icon="✨", bootstyle="info-subtle-pill").pack(side="left", padx=(0, 8))
        mtk.ModernButton(row3, text="Ghost Button", bootstyle="secondary-ghost").pack(side="left", padx=(0, 8))
        mtk.ModernButton(row3, text="Disabled", state="disabled").pack(side="left")

        # 2. Modern Switches, Checkboxes & Radios Card
        tog_card = mtk.ModernCard(
            parent,
            title="Modern Switches, Checkboxes & Radios",
            subtitle="Smooth animated toggle transitions with semantic color roles.",
        )
        tog_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))

        cols = mtk.ModernFrame(tog_card.body)
        cols.pack(fill="both", expand=True)

        c1 = mtk.ModernFrame(cols)
        c1.pack(side="left", fill="both", expand=True)

        sw1 = mtk.ModernSwitch(c1, text="Enable Cloud Sync", bootstyle="primary")
        sw1.set(True)
        sw1.pack(anchor="w", pady=4)

        sw2 = mtk.ModernSwitch(c1, text="Real-time Telemetry", bootstyle="success")
        sw2.set(True)
        sw2.pack(anchor="w", pady=4)

        sw3 = mtk.ModernSwitch(c1, text="Strict Firewall Mode", bootstyle="danger")
        sw3.pack(anchor="w", pady=4)

        c2 = mtk.ModernFrame(cols)
        c2.pack(side="left", fill="both", expand=True)

        cb1 = mtk.ModernCheckbox(c2, text="Auto-format on Save", bootstyle="primary")
        cb1.set(True)
        cb1.pack(anchor="w", pady=4)

        cb2 = mtk.ModernCheckbox(c2, text="Select All Modules", bootstyle="info", indeterminate=True)
        cb2.pack(anchor="w", pady=4)

        radio_var = tk.StringVar(value="pro")
        mtk.ModernRadioButton(c2, text="Starter Plan", variable=radio_var, value="starter").pack(anchor="w", pady=2)
        mtk.ModernRadioButton(c2, text="Pro Plan (Recommended)", variable=radio_var, value="pro", bootstyle="success").pack(anchor="w", pady=2)

        # 3. Sliders & Progress Bars Card
        prog_card = mtk.ModernCard(
            parent,
            title="Sliders & Progress Indicators",
            subtitle="Interactive sliders linked to determinate and indeterminate progress bars.",
        )
        prog_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))

        pb1 = mtk.ModernProgressBar(prog_card.body, value=68, bootstyle="primary", show_percent=True, width=460, height=20)
        pb1.pack(fill="x", pady=(4, 10))

        pb2 = mtk.ModernProgressBar(prog_card.body, value=45, bootstyle="success", width=460, height=10)
        pb2.pack(fill="x", pady=(0, 12))

        pb_ind = mtk.ModernProgressBar(prog_card.body, mode="indeterminate", bootstyle="info", width=460, height=8)
        pb_ind.pack(fill="x", pady=(0, 14))

        def _on_slide(v: float) -> None:
            pb1.set(v)
            pb2.set(min(100.0, v * 1.15))

        slider = mtk.ModernSlider(prog_card.body, from_=0, to=100, value=68, command=_on_slide, width=460)
        slider.pack(fill="x")

        # 4. Badges, Toasts & Modal Dialogs Card
        fb_card = mtk.ModernCard(
            parent,
            title="Badges, Toast Notifications & Modal Dialogs",
            subtitle="Status pills and non-blocking floating notifications.",
        )
        fb_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

        b_row = mtk.ModernFrame(fb_card.body)
        b_row.pack(fill="x", pady=(4, 14))
        for role, label in [
            ("primary-subtle", "● Live"),
            ("success-subtle", "✔ Verified"),
            ("warning-subtle", "⚡ Building"),
            ("danger-filled", "3 Critical"),
            ("info-outline", "v2.4 Beta"),
        ]:
            mtk.ModernBadge(b_row, text=label, bootstyle=role).pack(side="left", padx=(0, 8))

        t_row = mtk.ModernFrame(fb_card.body)
        t_row.pack(fill="x", pady=8)

        mtk.ModernButton(
            t_row,
            text="Show Success Toast",
            icon="✔",
            bootstyle="success",
            command=lambda: mtk.ModernToast.show(
                self,
                title="Deployment Succeeded",
                message="All 14 microservices are healthy and online.",
                bootstyle="success",
            ),
        ).pack(side="left", padx=(0, 8))

        mtk.ModernButton(
            t_row,
            text="Show Warning Toast",
            icon="⚠",
            bootstyle="warning-outline",
            command=lambda: mtk.ModernToast.show(
                self,
                title="High Memory Usage",
                message="Worker node #3 exceeded 85% memory threshold.",
                bootstyle="warning",
            ),
        ).pack(side="left", padx=(0, 8))

        mtk.ModernButton(
            t_row,
            text="Open Modal Dialog",
            bootstyle="primary-subtle",
            command=lambda: mtk.ModernDialog(
                self,
                title="Publish Release v2.4?",
                message="This will deploy the current build to production servers and notify subscribers.",
                confirm_text="Publish Now",
                bootstyle="primary",
            ),
        ).pack(side="left")

    def _populate_calendar_inputs_page(self, parent: mtk.ModernFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # Left: Modern Calendar Showcase
        cal_card = mtk.ModernCard(
            parent,
            title="Modern Interactive Calendar",
            subtitle="Click the month/year header to drill into Month and Year grids, or select date ranges.",
        )
        cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        cal_row = mtk.ModernFrame(cal_card.body)
        cal_row.pack(fill="both", expand=True, pady=6)

        self.sel_date_badge = mtk.ModernBadge(
            cal_card.body,
            text=f"Selected: {dt.date.today().isoformat()}",
            bootstyle="primary-subtle",
        )
        self.sel_date_badge.pack(anchor="w", pady=(8, 0))

        cal = mtk.ModernCalendar(
            cal_row,
            on_select=lambda d: self.sel_date_badge.set_text(f"Selected: {d}"),
            bootstyle="primary",
        )
        # Highlight sample holiday & fiscal start/end dates (inspired by HighlightedCalendar in Capacity)
        today = dt.date.today()
        cal.highlight_date(today.replace(day=min(28, today.day + 3)), "warning")
        cal.highlight_date(today.replace(day=max(1, today.day - 4)), "danger")
        cal.pack(side="left", padx=(0, 18))

        range_cal = mtk.ModernCalendar(
            cal_row,
            select_mode="range",
            bootstyle="success",
            on_select=lambda r: self.sel_date_badge.set_text(
                f"Range: {r[0]} → {r[1] or '...'}" if isinstance(r, tuple) else str(r)
            ),
        )
        range_cal.pack(side="left")

        # Right: Modern Rounded Inputs
        inp_card = mtk.ModernCard(
            parent,
            title="Modern Rounded Inputs, Validation & Chip Tags",
            subtitle="Rounded Entries, Validation states, TagInput chips, Combobox, Spinbox, and DatePicker.",
        )
        inp_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        mtk.ModernSearchBar(
            inp_card.body,
            placeholder="Search documentation, components, tokens...",
            width=360,
        ).pack(anchor="w", pady=(2, 8))

        val_entry = mtk.ModernEntry(
            inp_card.body,
            placeholder="Cluster Endpoint Hostname",
            prefix_icon="user",
            width=360,
        )
        val_entry.set("prod-cluster-01.internal")
        val_entry.set_validation("success", "✔ Endpoint verified and reachable (11.4 ms)")
        val_entry.pack(anchor="w", pady=(0, 6))

        val_btns = mtk.ModernFrame(inp_card.body)
        val_btns.pack(anchor="w", pady=(0, 8))
        mtk.ModernButton(
            val_btns,
            text="Valid",
            bootstyle="success-subtle",
            height=26,
            padx=10,
            command=lambda: val_entry.set_validation("success", "✔ Endpoint verified and reachable"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            val_btns,
            text="Warning",
            bootstyle="warning-subtle",
            height=26,
            padx=10,
            command=lambda: val_entry.set_validation("warning", "⚠ High latency detected on us-west-2"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            val_btns,
            text="Error",
            bootstyle="danger-subtle",
            height=26,
            padx=10,
            command=lambda: val_entry.set_validation("error", "✖ Invalid hostname or port unreachable"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            val_btns,
            text="Clear State",
            bootstyle="secondary-ghost",
            height=26,
            padx=10,
            command=lambda: val_entry.set_validation(None),
        ).pack(side="left")

        mtk.ModernPasswordEntry(
            inp_card.body,
            placeholder="API Secret Token",
            width=360,
        ).pack(anchor="w", pady=(0, 8))

        mtk.ModernLabel(inp_card.body, text="Resource Tags (type & press Enter or click ✕):", muted=True).pack(anchor="w", pady=(0, 4))
        mtk.ModernTagInput(
            inp_card.body,
            tags=["production", "us-east-1", "gpu-node"],
            bootstyle="primary",
            width=360,
        ).pack(anchor="w", pady=(0, 8))

        ctrl_row = mtk.ModernFrame(inp_card.body)
        ctrl_row.pack(fill="x", pady=(2, 8))

        mtk.ModernCombobox(
            ctrl_row,
            values=["Python 3.15", "Python 3.14", "Python 3.13", "Rust + PyO3"],
            default="Python 3.15",
            width=180,
        ).pack(side="left", padx=(0, 12))

        mtk.ModernSpinbox(
            ctrl_row,
            from_=1,
            to=64,
            value=8,
            width=140,
        ).pack(side="left")

        mtk.ModernDatePicker(
            inp_card.body,
            width=220,
            bootstyle="primary",
        ).pack(anchor="w", pady=(2, 0))

    def _populate_ttk_page(self, parent: mtk.ModernFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # 1. Top-Left: ModernNotebook ("underline" variant with icons, badges, closeable tabs)
        nb_card = mtk.ModernCard(
            parent,
            title="ModernNotebook — Animated Underline Tabs",
            subtitle="Supports tab icons, notification badges, animated sliding underline, and optional close buttons.",
        )
        nb_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        notebook = mtk.ModernNotebook(nb_card.body, variant="underline", bootstyle="primary", surface_role="surface_alt")
        notebook.pack(fill="both", expand=True)

        tab_overview = notebook.add("Overview", icon="📊", badge="New")
        mtk.ModernLabel(
            tab_overview,
            text="Workspace Overview",
            bold=True,
            font_size_delta=1,
        ).pack(anchor="w", pady=(0, 6))
        mtk.ModernLabel(
            tab_overview,
            text="This tab pane is a theme-reactive ModernFrame created via notebook.add('Overview', icon='📊').",
            muted=True,
        ).pack(anchor="w", pady=(0, 12))
        mtk.ModernProgressBar(tab_overview, value=78, bootstyle="success", show_percent=True, width=360, height=20).pack(anchor="w")

        tab_deployments = notebook.add("Deployments", icon="🚀", badge="3")
        mtk.ModernSwitch(tab_deployments, text="Auto-deploy on main branch push", bootstyle="success").pack(anchor="w", pady=4)
        mtk.ModernSwitch(tab_deployments, text="Run integration test suite before deploy", bootstyle="primary").pack(anchor="w", pady=4)

        tab_security = notebook.add("Security", icon="🛡", closeable=True)
        mtk.ModernCheckbox(tab_security, text="Require 2FA for all workspace admins", bootstyle="warning").pack(anchor="w", pady=4)
        mtk.ModernButton(tab_security, text="Rotate API Keys", bootstyle="danger-outline").pack(anchor="w", pady=6)

        # 2. Top-Right: ModernNotebook ("pills" & "cards" variants + dynamic tab adding)
        pills_card = mtk.ModernCard(
            parent,
            title="ModernNotebook — Pill & Card Tab Variants",
            subtitle="Switch between 'pills' or 'cards' tab styles, or dynamically add/close tabs at runtime.",
        )
        pills_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))

        pill_nb = mtk.ModernNotebook(
            pills_card.body,
            variant="pills",
            bootstyle="success",
            closeable=True,
            surface_role="surface_alt",
        )
        pill_nb.pack(fill="both", expand=True)

        p_tab1 = pill_nb.add("Metrics", icon="📈")
        mtk.ModernLabel(p_tab1, text="Real-time cluster CPU & memory utilization", muted=True).pack(anchor="w", pady=(0, 8))
        mtk.ModernSlider(p_tab1, from_=0, to=100, value=62, bootstyle="success", width=340).pack(anchor="w")

        p_tab2 = pill_nb.add("Logs", icon="📜", badge="12")
        mtk.ModernLabel(p_tab2, text="[09:30:12] INFO  All worker nodes synchronized.", muted=True).pack(anchor="w", pady=2)
        mtk.ModernLabel(p_tab2, text="[09:31:04] INFO  Health check passed (11.4 ms).", muted=True).pack(anchor="w", pady=2)

        def _add_dynamic_tab() -> None:
            idx = len(pill_nb._tabs) + 1
            new_t = pill_nb.add(f"Task #{idx}", icon="⚡", closeable=True)
            mtk.ModernLabel(new_t, text=f"Dynamic Closeable Tab #{idx} (click ✕ on the tab to close)", bold=True).pack(anchor="w")
            pill_nb.select(f"Task #{idx}")

        mtk.ModernButton(
            pills_card.body,
            text="+ Add Dynamic Tab",
            bootstyle="primary-outline",
            height=32,
            command=_add_dynamic_tab,
        ).pack(anchor="w", pady=(10, 0))

        # 3. Bottom: ModernNotebook + ModernTreeview (DataTable) Showcase
        card = mtk.ModernCard(
            parent,
            title="ModernNotebook & ModernTreeview (DataTable)",
            subtitle="Rounded modern data table with clickable column sorting (▲/▼), striped rows, hover highlight, semantic tags, and pill scrollbar.",
        )
        card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))

        data_nb = mtk.ModernNotebook(card.body, variant="cards", bootstyle="primary", surface_role="surface")
        data_nb.pack(fill="both", expand=True)

        tree_tab = data_nb.add("Cluster Instances", icon="🖥", badge="6")
        btns_tab = data_nb.add("Standard ttk Fallbacks", icon="🧩")

        cols = [
            ("id", "Instance ID", 140),
            ("service", "Service Name", 260),
            ("region", "Region", 180),
            ("latency", "P95 Latency", 150),
            ("status", "Status", 160),
        ]
        table = mtk.ModernTreeview(
            tree_tab,
            columns=cols,
            height=5,
            striped=True,
            sortable=True,
            bootstyle="primary",
        )
        sample_rows = [
            (("i-09a8f1", "Auth Gateway API", "us-east-1", "11.4 ms", "● Healthy"), "success"),
            (("i-04c2b9", "Vector Embedding Worker", "us-west-2", "28.9 ms", "● Healthy"), None),
            (("i-07e3d4", "Realtime Stream Broker", "eu-central-1", "19.1 ms", "● Healthy"), None),
            (("i-02f9a0", "Billing Webhook Queue", "ap-northeast-1", "42.0 ms", "⚡ Scaling"), "warning"),
            (("i-08b7e1", "Model Inference Cluster", "us-east-1", "89.4 ms", "✖ Degraded"), "danger"),
            (("i-05d1c3", "Analytics Lakehouse Sync", "eu-west-1", "15.2 ms", "● Healthy"), "info"),
        ]
        for row_vals, row_tag in sample_rows:
            table.insert_row(row_vals, tag=row_tag)
        table.pack(fill="both", expand=True)

        mtk.ModernLabel(
            btns_tab,
            text="Standard ttk.Button widgets styled automatically by ModernTkk's ThemeManager:",
            muted=True,
        ).pack(anchor="w", pady=(0, 10))
        btn_bar = mtk.ModernFrame(btns_tab)
        btn_bar.pack(fill="x")
        for role in ("primary", "secondary", "success", "info", "warning", "danger"):
            ttk.Button(
                btn_bar,
                text=f"ttk.{role}",
                style=f"{role}.TButton",
            ).pack(side="left", padx=(0, 8), anchor="n")

    def _populate_pro_page(self, parent: mtk.ModernFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # 1. Top-Left: Supersampled Radial Meters (mtk.Meter)
        meter_card = mtk.ModernCard(
            parent,
            title="Supersampled Radial Gauges (ModernMeter)",
            subtitle="Animated value sweeps, interactive pointer dragging, and automatic semantic color thresholds.",
        )
        meter_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        m_row = mtk.ModernFrame(meter_card.body)
        m_row.pack(fill="x", pady=(4, 8))

        meter_cpu = mtk.ModernMeter(
            m_row,
            value=72,
            size=148,
            thickness=12,
            subtext="CPU Load (Auto)",
            bootstyle="success",
            thresholds=[(70, "warning"), (88, "danger")],
        )
        meter_cpu.pack(side="left", padx=(0, 14))

        meter_interactive = mtk.ModernMeter(
            m_row,
            value=84,
            size=148,
            thickness=12,
            subtext="Drag Me!",
            bootstyle="primary",
            interactive=True,
        )
        meter_interactive.pack(side="left", padx=(0, 14))

        meter_ring = mtk.ModernMeter(
            m_row,
            value=94,
            size=148,
            thickness=12,
            arcrange=360,
            arcoffset=270,
            subtext="OEE Score",
            bootstyle="info",
        )
        meter_ring.pack(side="left")

        mtk.ModernSlider(
            meter_card.body,
            from_=0,
            to=100,
            value=72,
            command=lambda v: meter_cpu.set(v, animate=False),
            width=440,
        ).pack(fill="x", pady=(4, 0))

        # 2. Top-Right: ModernText / Code & Log Console
        log_card = mtk.ModernCard(
            parent,
            title="ModernText — Code & Semantic Log Console",
            subtitle="Rounded multi-line editor with line numbers, scrollbar, and semantic log level coloring.",
        )
        log_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))

        log_view = mtk.ModernText(
            log_card.body,
            line_numbers=True,
            monospace=True,
            height=136,
        )
        log_view.pack(fill="both", expand=True, pady=(0, 8))
        log_view.append_log("ModernTkk v0.2.0 initialized (4x supersampled PIL engine).", "INFO")
        log_view.append_log("Connected to primary analytics database (11.4 ms).", "SUCCESS")
        log_view.append_log("Worker pool #3 approaching 85% utilization threshold.", "WARNING")
        log_view.append_log("Retry scheduled for webhook endpoint eu-west-1.", "ERROR")

        log_btns = mtk.ModernFrame(log_card.body)
        log_btns.pack(fill="x")
        mtk.ModernButton(
            log_btns,
            text="+ Info",
            bootstyle="info-subtle",
            height=28,
            padx=12,
            command=lambda: log_view.append_log("Heartbeat check completed across 14 nodes.", "INFO"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            log_btns,
            text="+ Success",
            bootstyle="success-subtle",
            height=28,
            padx=12,
            command=lambda: log_view.append_log("Deployment pipeline artifact verified.", "SUCCESS"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            log_btns,
            text="+ Warning",
            bootstyle="warning-subtle",
            height=28,
            padx=12,
            command=lambda: log_view.append_log("Memory pressure detected on node-07.", "WARNING"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            log_btns,
            text="+ Error",
            bootstyle="danger-subtle",
            height=28,
            padx=12,
            command=lambda: log_view.append_log("Connection timeout on replica shard #2.", "ERROR"),
        ).pack(side="left", padx=(0, 6))
        mtk.ModernButton(
            log_btns,
            text="Clear",
            icon="trash",
            bootstyle="secondary-ghost",
            height=28,
            padx=10,
            command=log_view.clear,
        ).pack(side="right")

        # 3. Bottom-Left: Collapsible ModernAccordion / Expander Cards
        acc_card = mtk.ModernCard(
            parent,
            title="ModernAccordion (Collapsible Settings Expanders)",
            subtitle="Windows 11 Settings-style expandable sections with rotating vector chevrons.",
        )
        acc_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))

        exp1 = mtk.ModernAccordion(
            acc_card.body,
            title="Automated Backup Schedule",
            subtitle="Configure snapshot retention and S3 bucket replication.",
            icon="download",
            expanded=True,
            surface_role="surface_alt",
            padding=12,
        )
        exp1.pack(fill="x", pady=(0, 8))
        sw_bak = mtk.ModernSwitch(exp1.body, text="Enable hourly incremental snapshots", bootstyle="success")
        sw_bak.set(True)
        sw_bak.pack(anchor="w")

        exp2 = mtk.ModernAccordion(
            acc_card.body,
            title="Advanced Security & Zero-Trust Rules",
            subtitle="Click header to expand or collapse this section.",
            icon="lock",
            expanded=False,
            surface_role="surface_alt",
            padding=12,
        )
        exp2.pack(fill="x")
        mtk.ModernCheckbox(exp2.body, text="Enforce mutual TLS (mTLS) on internal RPCs", bootstyle="primary").pack(anchor="w")

        # 4. Bottom-Right: Procedural Vector Icon Engine & Context Menu
        vec_card = mtk.ModernCard(
            parent,
            title="Procedural Vector Icon Engine & Context Menus",
            subtitle="28 built-in 4x supersampled vector icons + themed popup menus & Ctrl+K Command Palette.",
        )
        vec_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

        act_row = mtk.ModernFrame(vec_card.body)
        act_row.pack(fill="x", pady=(2, 12))

        drop_btn = mtk.ModernButton(
            act_row,
            text="Dropdown Menu ▾",
            icon="sliders",
            bootstyle="primary",
            command=lambda: self.ctx_menu.show_under(drop_btn),
        )
        drop_btn.pack(side="left", padx=(0, 8))

        mtk.ModernButton(
            act_row,
            text="Open Command Palette (Ctrl+K)",
            icon="search",
            bootstyle="info-outline",
            command=lambda: self.cmd_palette.show(),
        ).pack(side="left")

        mtk.ModernLabel(
            vec_card.body,
            text="Vector Icons (rendered in memory via PIL.ImageDraw — zero external image files):",
            muted=True,
        ).pack(anchor="w", pady=(0, 8))

        ic_bar = mtk.ModernFrame(vec_card.body)
        ic_bar.pack(fill="x")
        for ic_name in ("search", "settings", "download", "upload", "calendar", "refresh", "filter", "terminal", "trash", "sparkles"):
            b = mtk.ModernButton(
                ic_bar,
                text="",
                icon=ic_name,
                bootstyle="secondary-outline",
                width=36,
                height=36,
                padx=6,
            )
            b.pack(side="left", padx=(0, 6))
            mtk.ModernTooltip(b, f"mtk.icon('{ic_name}')")

    def _populate_enterprise_page(self, parent: mtk.ModernFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # 1. Top Row: KPI Metric Cards (inspired by Capacity's StaffingOptimizerTab)
        kpi_card = mtk.ModernCard(
            parent,
            title="KPI Metric Cards (Capacity & Load Analytics)",
            subtitle="Inspired by RCCP StaffingOptimizerTab — live semantic KPI tiles with accent bars and delta pills.",
        )
        kpi_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        kpi_row = mtk.ModernFrame(kpi_card.body)
        kpi_row.pack(fill="x", pady=4)

        m1 = mtk.ModernMetricCard(
            kpi_row,
            title="Total Demand (hrs)",
            value="4,820.5",
            delta="+6.4% wk",
            icon="📈",
            bootstyle="primary",
            surface_role="surface_alt",
            width=260,
        )
        m1.pack(side="left", padx=(0, 12))

        m2 = mtk.ModernMetricCard(
            kpi_row,
            title="Available Capacity",
            value="5,140.0",
            delta="93.8% Load",
            icon="⚙",
            bootstyle="success",
            surface_role="surface_alt",
            width=260,
        )
        m2.pack(side="left", padx=(0, 12))

        m3 = mtk.ModernMetricCard(
            kpi_row,
            title="Net Balance (hrs)",
            value="+319.5",
            delta="Surplus",
            icon="✔",
            bootstyle="info",
            surface_role="surface_alt",
            width=260,
        )
        m3.pack(side="left", padx=(0, 12))

        m4 = mtk.ModernMetricCard(
            kpi_row,
            title="Bottleneck Alerts",
            value="2 Groups",
            delta="Action Req",
            icon="⚠",
            bootstyle="warning",
            surface_role="surface_alt",
            width=260,
        )
        m4.pack(side="left")

        # 2. Bottom Row: Split PanedWindow with Scrollable Settings & Progress/Splash Launchers
        bottom_split = ttk.PanedWindow(parent, orient="horizontal")
        bottom_split.grid(row=1, column=0, sticky="nsew")

        left_card = mtk.ModernCard(
            bottom_split,
            title="ModernScrollableFrame Viewport",
            subtitle="Smooth mousewheel-scrollable form container with auto-hiding pill scrollbar.",
        )
        right_card = mtk.ModernCard(
            bottom_split,
            title="Splash Screen, Progress Dialog & Chart Adapters",
            subtitle="Launch the glassmorphic ModernSplash or modal ModernProgressDialog from Capacity.",
        )
        bottom_split.add(left_card, weight=1)
        bottom_split.add(right_card, weight=1)

        scroll_view = mtk.ModernScrollableFrame(left_card.body, surface_role="surface_alt")
        scroll_view.pack(fill="both", expand=True)
        for idx in range(1, 12):
            row_f = mtk.ModernFrame(scroll_view.body, surface_role="surface_alt", pady=4)
            row_f.pack(fill="x")
            mtk.ModernLabel(
                row_f,
                text=f"Resource Pool #{idx:02d} — CNC Machining Cell {idx}",
                surface_role="surface_alt",
                bold=True,
            ).pack(side="left")
            sw = mtk.ModernSwitch(row_f, text="Active", bootstyle="success" if idx % 3 else "warning")
            sw.set(True)
            sw.pack(side="right")

        btn_col = mtk.ModernFrame(right_card.body)
        btn_col.pack(fill="x", pady=6)

        def _demo_progress_dialog() -> None:
            dlg = mtk.ModernProgressDialog(
                self,
                title="Running Auto-Optimizer",
                message="Leveling weekly capacity & demand...",
                bootstyle="primary",
            )
            steps = [
                (25, "Loading active resource groups..."),
                (55, "Solving weekly shift & overtime constraints..."),
                (85, "Building smoothing plan..."),
                (100, "Optimization complete!"),
            ]

            def _step(i: int = 0) -> None:
                if i < len(steps):
                    pct, msg = steps[i]
                    dlg.update(pct, msg)
                    self.after(350, lambda: _step(i + 1))
                else:
                    dlg.destroy()
                    mtk.ModernToast.show(
                        self,
                        title="Optimization Finished",
                        message="Weekly capacity plan updated.",
                        bootstyle="success",
                    )

            self.after(250, _step)

        def _demo_splash() -> None:
            sp = mtk.ModernSplash(
                self,
                title="RCCP Analytics Suite",
                subtitle="Rough Cut Capacity Planning & Simulation Engine",
                version="v1.2.0 ModernTkk Edition",
                footer="Glassmorphic Pillow Splash Screen Preview",
                bootstyle="info",
            )
            stages = [
                (30, "Loading SQLite database & settings..."),
                (65, "Loading resource pools & holiday calendars..."),
                (95, "Initializing What-If simulation engine..."),
                (100, "Ready!"),
            ]

            def _run(i: int = 0) -> None:
                if i < len(stages):
                    pct, msg = stages[i]
                    sp.update_progress(pct, msg)
                    self.after(380, lambda: _run(i + 1))
                else:
                    sp.finish()

            self.after(250, _run)

        mtk.ModernButton(
            btn_col,
            text="Launch Modal ProgressDialog",
            icon="⏳",
            bootstyle="primary",
            command=_demo_progress_dialog,
        ).pack(anchor="w", pady=6)

        mtk.ModernButton(
            btn_col,
            text="Preview Glassmorphic SplashScreen",
            icon="🚀",
            bootstyle="info-outline",
            command=_demo_splash,
        ).pack(anchor="w", pady=6)

        mtk.ModernLabel(
            right_card.body,
            text=(
                "Also included in moderntkk:\n"
                "• mtk.style_matplotlib_figure(fig, ax) — Live theme sync for Matplotlib\n"
                "• mtk.style_matplotlib_toolbar(toolbar) — Flat themed chart toolbar\n"
                "• mtk.style_tksheet(sheet) — Full theme sync for tksheet grids\n"
                "• Built-in 'rccp_blue', 'rccp_teal', and 'rccp_fuchsia' themes!"
            ),
            muted=True,
            justify="left",
        ).pack(anchor="w", pady=(14, 0))


if __name__ == "__main__":
    app = ShowcaseApp()
    app.mainloop()

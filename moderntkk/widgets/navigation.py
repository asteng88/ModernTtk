"""Modern navigation and overlay menus for ModernTkk:

- ModernSidebar (Collapsible Windows 11 Fluent left navigation rail with active indicator pill)
- ModernContextMenu / ModernMenu (Rounded dark/light themed popup & right-click context menu)
- ModernCommandPalette (Ctrl+K Spotlight quick-action search modal)
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from PIL import ImageTk

from ..icons import AVAILABLE_ICONS, create_icon_image
from ..themes import ThemePalette
from ..utils import create_rounded_rect_image
from .base import ModernFrame, ThemedWidgetMixin


@dataclass
class _SidebarEntry:
    kind: str  # "item" or "section"
    key: str
    label: str
    icon: Optional[str] = None
    badge: Optional[str] = None


class ModernSidebar(tk.Canvas, ThemedWidgetMixin):
    """Collapsible Windows 11 Fluent navigation sidebar rail.

    Supports expanded mode (icon + label + badge) and collapsed mode (icon-only rail),
    vertical active indicator pill, section headers, and live theme reactivity.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Navigation",
        expanded_width: int = 216,
        collapsed_width: int = 62,
        collapsed: bool = False,
        bootstyle: str = "primary",
        surface_role: str = "surface",
        on_select: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        self._title = title
        self._expanded_w = expanded_width
        self._collapsed_w = collapsed_width
        self._collapsed = collapsed
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._surface_role = surface_role
        self._on_select = on_select

        self._entries: List[_SidebarEntry] = []
        self._selected_key: Optional[str] = None
        self._hovered_key: Optional[str] = None
        self._toggle_hovered = False
        self._hitboxes: List[Tuple[int, int, int, int, str]] = []
        self._toggle_box: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self._img_refs: List[ImageTk.PhotoImage] = []

        init_w = collapsed_width if collapsed else expanded_width
        super().__init__(
            master,
            width=init_w,
            bd=0,
            highlightthickness=0,
            relief="flat",
            **kwargs,
        )
        self._init_themed(bg_role=surface_role)

        p = self.palette
        self._font_header = tkfont.Font(family=p.font_family, size=p.font_size + 1, weight="bold")
        self._font_sec = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")
        self._font_item = tkfont.Font(family=p.font_family, size=p.font_size)
        self._font_item_bold = tkfont.Font(family=p.font_family, size=p.font_size, weight="bold")
        self._font_badge = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._redraw())

    def add_section(self, label: str) -> None:
        """Add an uppercase section divider header to the sidebar."""
        self._entries.append(_SidebarEntry(kind="section", key=f"__sec_{len(self._entries)}", label=label))
        self._redraw()

    def add_item(
        self,
        key: str,
        label: str,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
    ) -> None:
        """Add a selectable navigation item to the sidebar."""
        self._entries.append(_SidebarEntry(kind="item", key=key, label=label, icon=icon, badge=badge))
        if self._selected_key is None:
            self._selected_key = key
        self._redraw()

    def select(self, key: str, notify: bool = True) -> None:
        """Select a navigation item by key."""
        self._selected_key = key
        self._redraw()
        if notify and self._on_select is not None:
            self._on_select(key)

    def get(self) -> Optional[str]:
        return self._selected_key

    def toggle_collapse(self) -> None:
        """Toggle between expanded and icon-only collapsed rail mode."""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        target_w = self._collapsed_w if collapsed else self._expanded_w
        super().configure(width=target_w)
        self._redraw()

    def _on_motion(self, e: tk.Event) -> None:
        tx1, ty1, tx2, ty2 = self._toggle_box
        in_toggle = tx1 <= e.x <= tx2 and ty1 <= e.y <= ty2

        found_key: Optional[str] = None
        if not in_toggle:
            for x1, y1, x2, y2, k in self._hitboxes:
                if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                    found_key = k
                    break

        if in_toggle != self._toggle_hovered or found_key != self._hovered_key:
            self._toggle_hovered = in_toggle
            self._hovered_key = found_key
            self.configure(cursor="hand2" if (in_toggle or found_key) else "arrow")
            self._redraw()

    def _on_leave(self, _e: tk.Event) -> None:
        if self._hovered_key is not None or self._toggle_hovered:
            self._hovered_key = None
            self._toggle_hovered = False
            self.configure(cursor="arrow")
            self._redraw()

    def _on_click(self, e: tk.Event) -> None:
        tx1, ty1, tx2, ty2 = self._toggle_box
        if tx1 <= e.x <= tx2 and ty1 <= e.y <= ty2:
            self.toggle_collapse()
            return
        for x1, y1, x2, y2, k in self._hitboxes:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self.select(k, notify=True)
                return

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        surf = getattr(p, self._surface_role, p.surface)
        super().configure(bg=surf)
        self.delete("all")
        self._hitboxes.clear()
        self._img_refs.clear()

        w = self._collapsed_w if self._collapsed else self._expanded_w
        h = max(200, self.winfo_height())
        accent = p.role_color(self._role)

        # Right border hairline
        self.create_line(w - 1, 0, w - 1, h, fill=p.divider, width=1)

        # Top header bar + collapse toggle button
        y = 14
        toggle_sz = 34
        tx = (w - toggle_sz) // 2 if self._collapsed else w - toggle_sz - 10
        self._toggle_box = (tx, y, tx + toggle_sz, y + toggle_sz)

        if self._toggle_hovered:
            t_img = create_rounded_rect_image(toggle_sz, toggle_sz, p.radius_sm, fill_hex=p.surface_hover, bg_hex=surf)
            self._img_refs.append(t_img)
            self.create_image(tx, y, image=t_img, anchor="nw")

        chev_icon = "chevron_right" if self._collapsed else "chevron_left"
        c_img = create_icon_image(chev_icon, size=16, color=accent if self._toggle_hovered else p.fg_muted)
        self._img_refs.append(c_img)
        self.create_image(tx + toggle_sz // 2, y + toggle_sz // 2, image=c_img, anchor="center")

        if not self._collapsed and self._title:
            self.create_text(16, y + toggle_sz // 2, text=self._title, fill=p.fg, font=self._font_header, anchor="w")

        y += toggle_sz + 10
        self.create_line(10, y, w - 10, y, fill=p.divider, width=1)
        y += 10

        item_h = 38
        pad_x = 8

        for entry in self._entries:
            if entry.kind == "section":
                if self._collapsed:
                    self.create_line(14, y + 6, w - 14, y + 6, fill=p.divider, width=1)
                    y += 14
                else:
                    self.create_text(
                        16,
                        y + 12,
                        text=entry.label.upper(),
                        fill=p.fg_subtle,
                        font=self._Short_sec(entry.label),
                        anchor="w",
                    )
                    y += 26
                continue

            is_sel = entry.key == self._selected_key
            is_hov = entry.key == self._hovered_key
            row_w = w - pad_x * 2

            if is_sel or is_hov:
                row_fill = p.role_subtle_bg(self._role) if is_sel else p.surface_hover
                r_img = create_rounded_rect_image(
                    row_w,
                    item_h,
                    p.radius_md,
                    fill_hex=row_fill,
                    bg_hex=surf,
                )
                self._img_refs.append(r_img)
                self.create_image(pad_x, y, image=r_img, anchor="nw")

            if is_sel:
                # Fluent active vertical pill bar
                bar_h = 18
                b_img = create_rounded_rect_image(
                    4,
                    bar_h,
                    2,
                    fill_hex=accent,
                    bg_hex=p.role_subtle_bg(self._role),
                )
                self._img_refs.append(b_img)
                self.create_image(pad_x + 3, y + (item_h - bar_h) // 2, image=b_img, anchor="nw")

            fg_col = accent if is_sel else (p.fg if is_hov else p.fg_muted)
            cy = y + item_h // 2

            if entry.icon:
                ic_x = w // 2 if self._collapsed else pad_x + 22
                if entry.icon.lower().strip() in AVAILABLE_ICONS:
                    ic_img = create_icon_image(entry.icon, size=16, color=fg_col)
                    self._img_refs.append(ic_img)
                    self.create_image(ic_x, cy, image=ic_img, anchor="center")
                else:
                    self.create_text(ic_x, cy, text=entry.icon, fill=fg_col, font=self._font_item, anchor="center")

            if not self._collapsed:
                text_x = pad_x + (40 if entry.icon else 16)
                self.create_text(
                    text_x,
                    cy,
                    text=entry.label,
                    fill=p.fg if is_sel else fg_col,
                    font=self._font_item_bold if is_sel else self._font_item,
                    anchor="w",
                )
                if entry.badge:
                    bw = max(20, self._font_badge.measure(entry.badge) + 12)
                    bh = 18
                    bx = w - pad_x - bw - 8
                    by = cy - bh // 2
                    badge_img = create_rounded_rect_image(
                        bw,
                        bh,
                        bh // 2,
                        fill_hex=accent if is_sel else p.surface_alt,
                        bg_hex=p.role_subtle_bg(self._role) if is_sel else surf,
                    )
                    self._img_refs.append(badge_img)
                    self.create_image(bx, by, image=badge_img, anchor="nw")
                    self.create_text(
                        bx + bw // 2,
                        cy,
                        text=entry.badge,
                        fill=p.role_text(self._role) if is_sel else p.fg_muted,
                        font=self._font_badge,
                    )

            self._hitboxes.append((pad_x, y, pad_x + row_w, y + item_h, entry.key))
            y += item_h + 4

    def _Short_sec(self, _label: str) -> tkfont.Font:
        return self._font_sec


@dataclass
class _MenuItem:
    kind: str  # "command" or "separator"
    label: str = ""
    command: Optional[Callable[[], None]] = None
    icon: Optional[str] = None
    accelerator: str = ""
    bootstyle: Optional[str] = None


class ModernContextMenu:
    """Floating anti-aliased rounded popup and right-click context menu (`ModernMenu` / `ModernContextMenu`).

    Replaces native `tk.Menu` with full dark/light theme support, vector/emoji icons,
    keyboard shortcut accelerators, and semantic danger/primary item colors.
    """

    def __init__(self, master: Optional[tk.Misc] = None, width: int = 230) -> None:
        self._master = master
        self._width = width
        self._items: List[_MenuItem] = []
        self._popup_win: Optional[tk.Toplevel] = None
        self._img_refs: List[ImageTk.PhotoImage] = []

    def add_command(
        self,
        label: str,
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        accelerator: str = "",
        bootstyle: Optional[str] = None,
    ) -> "ModernContextMenu":
        """Add a clickable command item to the menu."""
        self._items.append(
            _MenuItem(
                kind="command",
                label=label,
                command=command,
                icon=icon,
                accelerator=accelerator,
                bootstyle=bootstyle,
            )
        )
        return self

    def add_separator(self) -> "ModernContextMenu":
        """Add a horizontal hairline divider."""
        self._items.append(_MenuItem(kind="separator"))
        return self

    def bind_context(self, widget: tk.Misc) -> None:
        """Bind this menu as a right-click context menu on `widget`."""
        widget.bind("<Button-3>", lambda e: self.popup(e.x_root, e.y_root), add="+")
        widget.bind("<Button-2>", lambda e: self.popup(e.x_root, e.y_root), add="+")

    def show_under(self, widget: tk.Misc) -> None:
        """Open this menu directly underneath `widget` (ideal for dropdown action buttons)."""
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        self.popup(x, y)

    def close(self) -> None:
        if self._popup_win is not None and self._popup_win.winfo_exists():
            self._popup_win.destroy()
        self._popup_win = None

    def popup(self, x_root: int, y_root: int) -> None:
        """Show the floating menu at screen coordinates `(x_root, y_root)`."""
        self.close()
        if not self._items:
            return

        from ..style import ThemeManager
        p = ThemeManager.instance().palette

        item_h = 34
        sep_h = 9
        pad = 6
        total_h = pad * 2 + sum(sep_h if it.kind == "separator" else item_h for it in self._items)
        w = self._width

        pop = tk.Toplevel(self._master)
        pop.wm_overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=p.bg)
        self._popup_win = pop

        canvas = tk.Canvas(pop, width=w, height=total_h, bg=p.bg, bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        font_item = tkfont.Font(family=p.font_family, size=p.font_size)
        font_acc = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        state = {"hovered_idx": -1}
        row_bounds: List[Tuple[int, int, int, _MenuItem]] = []

        def _render() -> None:
            canvas.delete("all")
            self._img_refs.clear()
            row_bounds.clear()

            bg_img = create_rounded_rect_image(
                w,
                total_h,
                p.radius_lg,
                fill_hex=p.surface,
                border_hex=p.border_strong,
                border_width=1,
                bg_hex=p.bg,
            )
            self._img_refs.append(bg_img)
            canvas.create_image(0, 0, image=bg_img, anchor="nw")

            cy = pad
            for idx, it in enumerate(self._items):
                if it.kind == "separator":
                    canvas.create_line(12, cy + sep_h // 2, w - 12, cy + sep_h // 2, fill=p.divider, width=1)
                    cy += sep_h
                    continue

                is_hov = state["hovered_idx"] == idx
                role = it.bootstyle.split("-")[0] if it.bootstyle else None
                fg_col = p.role_color(role) if role else p.fg

                if is_hov:
                    hov_fill = p.role_subtle_bg(role) if role else p.surface_hover
                    h_img = create_rounded_rect_image(
                        w - 12,
                        item_h - 2,
                        p.radius_sm,
                        fill_hex=hov_fill,
                        bg_hex=p.surface,
                    )
                    self._img_refs.append(h_img)
                    canvas.create_image(6, cy + 1, image=h_img, anchor="nw")

                mid_y = cy + item_h // 2
                if it.icon:
                    if it.icon.lower().strip() in AVAILABLE_ICONS:
                        ic_img = create_icon_image(it.icon, size=15, color=fg_col)
                        self._img_refs.append(ic_img)
                        canvas.create_image(22, mid_y, image=ic_img, anchor="center")
                    else:
                        canvas.create_text(22, mid_y, text=it.icon, fill=fg_col, font=font_item, anchor="center")

                canvas.create_text(40, mid_y, text=it.label, fill=fg_col, font=font_item, anchor="w")

                if it.accelerator:
                    canvas.create_text(w - 14, mid_y, text=it.accelerator, fill=p.fg_subtle, font=font_acc, anchor="e")

                row_bounds.append((cy, cy + item_h, idx, it))
                cy += item_h

        def _on_motion(e: tk.Event) -> None:
            found = -1
            for y1, y2, idx, _ in row_bounds:
                if y1 <= e.y <= y2:
                    found = idx
                    break
            if found != state["hovered_idx"]:
                state["hovered_idx"] = found
                canvas.configure(cursor="hand2" if found >= 0 else "arrow")
                _render()

        def _on_click(e: tk.Event) -> None:
            for y1, y2, _idx, it in row_bounds:
                if y1 <= e.y <= y2:
                    self.close()
                    if it.command is not None:
                        it.command()
                    return

        canvas.bind("<Motion>", _on_motion)
        canvas.bind("<ButtonRelease-1>", _on_click)
        _render()

        pop.geometry(f"{w}x{total_h}+{x_root}+{y_root}")
        pop.focus_force()
        pop.bind("<FocusOut>", lambda e: self.close())
        pop.bind("<Escape>", lambda e: self.close())


@dataclass
class _CommandEntry:
    title: str
    callback: Callable[[], None]
    category: str = "Command"
    icon: str = "sparkles"
    shortcut: str = ""


class ModernCommandPalette:
    """VS Code / Raycast-style `Ctrl+K` floating spotlight command palette.

    Allows users to search and invoke registered application actions, switch themes,
    or jump to tabs with full keyboard navigation (`<Up>`, `<Down>`, `<Return>`, `<Escape>`).
    """

    def __init__(
        self,
        root: tk.Misc,
        placeholder: str = "Type a command or search actions...",
        bootstyle: str = "primary",
        width: int = 560,
    ) -> None:
        self._root = root
        self._placeholder = placeholder
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._width = width
        self._commands: List[_CommandEntry] = []
        self._win: Optional[tk.Toplevel] = None
        self._img_refs: List[ImageTk.PhotoImage] = []

    def register(
        self,
        title: str,
        callback: Callable[[], None],
        category: str = "Action",
        icon: str = "sparkles",
        shortcut: str = "",
    ) -> "ModernCommandPalette":
        """Register a searchable command in the palette."""
        self._commands.append(
            _CommandEntry(
                title=title,
                callback=callback,
                category=category,
                icon=icon,
                shortcut=shortcut,
            )
        )
        return self

    def bind_shortcut(self, sequence: str = "<Control-k>") -> None:
        """Bind a global keyboard shortcut (default `Ctrl+K`) on the root window."""
        self._root.bind_all(sequence, lambda e: self.show())

    def close(self) -> None:
        if self._win is not None and self._win.winfo_exists():
            self._win.destroy()
        self._win = None

    def show(self) -> None:
        """Open the floating command palette overlay centered near the top of the window."""
        if self._win is not None and self._win.winfo_exists():
            self.close()
            return

        from ..style import ThemeManager
        p = ThemeManager.instance().palette
        accent = p.role_color(self._role)

        w = self._width
        max_visible = 7
        row_h = 42
        header_h = 54
        footer_h = 28

        pop = tk.Toplevel(self._root)
        pop.wm_overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=p.border_strong, padx=1, pady=1)
        self._win = pop

        container = tk.Frame(pop, bg=p.surface)
        container.pack(fill="both", expand=True)

        # Top Search Input Bar
        top_bar = tk.Canvas(container, width=w, height=header_h, bg=p.surface, bd=0, highlightthickness=0)
        top_bar.pack(fill="x")

        ic_search = create_icon_image("search", size=18, color=accent)
        self._img_refs = [ic_search]
        top_bar.create_image(22, header_h // 2, image=ic_search, anchor="center")
        top_bar.create_line(0, header_h - 1, w, header_h - 1, fill=p.divider, width=1)

        query_var = tk.StringVar()
        font_input = tkfont.Font(family=p.font_family, size=p.font_size + 1)
        font_title = tkfont.Font(family=p.font_family, size=p.font_size)
        font_cat = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")
        font_foot = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        entry = tk.Entry(
            top_bar,
            textvariable=query_var,
            bg=p.surface,
            fg=p.fg,
            insertbackground=p.fg,
            selectbackground=accent,
            selectforeground=p.role_text(self._role),
            bd=0,
            highlightthickness=0,
            font=font_input,
        )
        top_bar.create_window(44, header_h // 2, window=entry, anchor="w", width=w - 110)

        # ESC pill hint
        esc_img = create_rounded_rect_image(40, 22, 6, fill_hex=p.surface_alt, border_hex=p.border, border_width=1, bg_hex=p.surface)
        self._img_refs.append(esc_img)
        top_bar.create_image(w - 52, (header_h - 22) // 2, image=esc_img, anchor="nw")
        top_bar.create_text(w - 32, header_h // 2, text="ESC", fill=p.fg_muted, font=font_cat)

        # Results Canvas
        list_canvas = tk.Canvas(container, width=w, height=row_h * max_visible, bg=p.surface, bd=0, highlightthickness=0)
        list_canvas.pack(fill="both", expand=True)

        # Footer Bar
        footer = tk.Frame(container, bg=p.surface_alt, height=footer_h, padx=14)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="↑↓ Navigate    ↵ Execute    ESC Close",
            bg=p.surface_alt,
            fg=p.fg_muted,
            font=font_foot,
        ).pack(side="left", pady=4)

        state = {
            "filtered": list(self._commands),
            "sel_idx": 0,
        }

        def _filter_commands(*_args) -> None:
            q = query_var.get().strip().lower()
            if not q:
                state["filtered"] = list(self._commands)
            else:
                state["filtered"] = [
                    c for c in self._commands
                    if q in c.title.lower() or q in c.category.lower()
                ]
            state["sel_idx"] = 0
            _render_list()

        def _render_list() -> None:
            list_canvas.delete("all")
            items = state["filtered"][:max_visible]
            vis_count = max(1, len(items))
            list_h = vis_count * row_h + 12
            list_canvas.configure(height=list_h)

            if not items:
                list_canvas.create_text(
                    w // 2,
                    list_h // 2,
                    text="No matching commands found.",
                    fill=p.fg_muted,
                    font=font_title,
                )
            else:
                cy = 6
                for idx, cmd in enumerate(items):
                    is_sel = idx == state["sel_idx"]
                    if is_sel:
                        r_img = create_rounded_rect_image(
                            w - 16,
                            row_h - 4,
                            p.radius_md,
                            fill_hex=p.role_subtle_bg(self._role),
                            border_hex=accent,
                            border_width=1,
                            bg_hex=p.surface,
                        )
                        self._img_refs.append(r_img)
                        list_canvas.create_image(8, cy + 2, image=r_img, anchor="nw")

                    mid_y = cy + row_h // 2
                    ic_col = accent if is_sel else p.fg_muted
                    if cmd.icon.lower().strip() in AVAILABLE_ICONS:
                        c_ic = create_icon_image(cmd.icon, size=16, color=ic_col)
                        self._img_refs.append(c_ic)
                        list_canvas.create_image(28, mid_y, image=c_ic, anchor="center")
                    else:
                        list_canvas.create_text(28, mid_y, text=cmd.icon, fill=ic_col, font=font_title)

                    # Category pill
                    cat_w = font_cat.measure(cmd.category) + 14
                    cat_img = create_rounded_rect_image(
                        cat_w,
                        20,
                        10,
                        fill_hex=p.surface_alt,
                        bg_hex=p.role_subtle_bg(self._role) if is_sel else p.surface,
                    )
                    self._img_refs.append(cat_img)
                    list_canvas.create_image(48, mid_y - 10, image=cat_img, anchor="nw")
                    list_canvas.create_text(48 + cat_w // 2, mid_y, text=cmd.category, fill=p.fg_muted, font=font_cat)

                    # Command title
                    list_canvas.create_text(
                        48 + cat_w + 10,
                        mid_y,
                        text=cmd.title,
                        fill=p.fg,
                        font=font_title,
                        anchor="w",
                    )

                    if cmd.shortcut:
                        list_canvas.create_text(
                            w - 20,
                            mid_y,
                            text=cmd.shortcut,
                            fill=accent if is_sel else p.fg_subtle,
                            font=font_cat,
                            anchor="e",
                        )

                    cy += row_h

            total_h = header_h + list_h + footer_h
            rx = self._root.winfo_rootx() + (self._root.winfo_width() - w) // 2
            ry = self._root.winfo_rooty() + max(48, int(self._root.winfo_height() * 0.14))
            pop.geometry(f"{w}x{total_h}+{rx}+{ry}")

        def _move_sel(delta: int) -> str:
            items = state["filtered"][:max_visible]
            if items:
                state["sel_idx"] = (state["sel_idx"] + delta) % len(items)
                _render_list()
            return "break"

        def _execute_selected(_e: Optional[tk.Event] = None) -> str:
            items = state["filtered"][:max_visible]
            if items and 0 <= state["sel_idx"] < len(items):
                chosen = items[state["sel_idx"]]
                self.close()
                chosen.callback()
            return "break"

        def _on_list_click(e: tk.Event) -> None:
            idx = (e.y - 6) // row_h
            items = state["filtered"][:max_visible]
            if 0 <= idx < len(items):
                state["sel_idx"] = idx
                _execute_selected()

        def _on_list_motion(e: tk.Event) -> None:
            idx = (e.y - 6) // row_h
            items = state["filtered"][:max_visible]
            if 0 <= idx < len(items) and idx != state["sel_idx"]:
                state["sel_idx"] = idx
                _render_list()

        query_var.trace_add("write", _filter_commands)
        entry.bind("<Down>", lambda e: _move_sel(1))
        entry.bind("<Up>", lambda e: _move_sel(-1))
        entry.bind("<Return>", _execute_selected)
        entry.bind("<Escape>", lambda e: self.close())
        list_canvas.bind("<ButtonRelease-1>", _on_list_click)
        list_canvas.bind("<Motion>", _on_list_motion)
        pop.bind("<Escape>", lambda e: self.close())
        entry.bind("<FocusOut>", lambda e: pop.after(120, lambda: self.close() if pop.winfo_exists() and pop.focus_get() is None else None))

        _render_list()
        entry.focus_force()


# Ergonomic alias
ModernMenu = ModernContextMenu

"""Modern navigation and overlay menus for ModernTtk:

- ModernSidebar (Collapsible Windows 11 Fluent left navigation rail with active indicator pill)
- ModernContextMenu / ModernMenu (Rounded dark/light themed popup & right-click context menu)
- ModernCommandPalette (Ctrl+K Spotlight quick-action search modal)
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import ImageTk

from ..icons import AVAILABLE_ICONS, create_icon_image
from ..themes import ThemePalette
from ..utils import create_circle_image, create_rounded_rect_image, get_monitor_work_area
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
    kind: str  # "command", "separator", "radiobutton", "checkbutton", "cascade", "header"
    label: str = ""
    command: Optional[Callable[[], None]] = None
    icon: Optional[str] = None
    accelerator: str = ""
    bootstyle: Optional[str] = None
    variable: Optional[tk.Variable] = None
    value: Any = None
    onvalue: Any = True
    offvalue: Any = False
    menu: Optional["ModernContextMenu"] = None
    state: str = "normal"


class ModernContextMenu:
    """Floating anti-aliased rounded popup and right-click context menu (`ModernMenu` / `ModernContextMenu`).

    Replaces native `tk.Menu` with full dark/light theme support, vector/emoji icons,
    radio/checkbutton items, cascades, keyboard shortcut accelerators, and semantic item colors.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 220,
        tearoff: bool | int = False,
        **kwargs,
    ) -> None:
        self._master = master
        self._width = width
        self._items: List[_MenuItem] = []
        self._popup_win: Optional[tk.Toplevel] = None
        self._img_refs: List[ImageTk.PhotoImage] = []
        self._on_close_cb: Optional[Callable[[], None]] = None

    @property
    def is_open(self) -> bool:
        return self._popup_win is not None and self._popup_win.winfo_exists()

    def add_command(
        self,
        label: str,
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        accelerator: str = "",
        bootstyle: Optional[str] = None,
        state: str = "normal",
        **kwargs,
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
                state=str(state or "normal"),
            )
        )
        return self

    def add_radiobutton(
        self,
        label: str,
        variable: Optional[tk.Variable] = None,
        value: Any = None,
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        state: str = "normal",
        **kwargs,
    ) -> "ModernContextMenu":
        """Add a radio selection item to the menu (`tk.Menu.add_radiobutton` compatible)."""
        self._items.append(
            _MenuItem(
                kind="radiobutton",
                label=label,
                variable=variable,
                value=label if value is None else value,
                command=command,
                icon=icon,
                state=str(state or "normal"),
            )
        )
        return self

    def add_checkbutton(
        self,
        label: str,
        variable: Optional[tk.Variable] = None,
        onvalue: Any = True,
        offvalue: Any = False,
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        state: str = "normal",
        **kwargs,
    ) -> "ModernContextMenu":
        """Add a checkable toggle item to the menu (`tk.Menu.add_checkbutton` compatible)."""
        self._items.append(
            _MenuItem(
                kind="checkbutton",
                label=label,
                variable=variable,
                onvalue=onvalue,
                offvalue=offvalue,
                command=command,
                icon=icon,
                state=str(state or "normal"),
            )
        )
        return self

    def add_cascade(
        self,
        label: str,
        menu: Optional["ModernContextMenu"] = None,
        icon: Optional[str] = None,
        state: str = "normal",
        **kwargs,
    ) -> "ModernContextMenu":
        """Add a submenu group (`tk.Menu.add_cascade` compatible)."""
        self._items.append(
            _MenuItem(
                kind="cascade",
                label=label,
                menu=menu,
                icon=icon,
                state=str(state or "normal"),
            )
        )
        return self

    def add_separator(self) -> "ModernContextMenu":
        """Add a horizontal hairline divider."""
        self._items.append(_MenuItem(kind="separator"))
        return self

    def _resolve_index(self, idx: int | str) -> int:
        if isinstance(idx, int):
            return idx
        s = str(idx).lower().strip()
        if s in ("end", "last"):
            return max(0, len(self._items) - 1)
        try:
            return int(s)
        except ValueError:
            for i, item in enumerate(self._items):
                if item.label == idx:
                    return i
            return 0

    def index(self, idx: int | str) -> Optional[int]:
        """Return numeric index of menu entry (`tk.Menu.index` compatible)."""
        if not self._items:
            return None
        return self._resolve_index(idx)

    def delete(self, index1: int | str = 0, index2: Optional[int | str] = None) -> "ModernContextMenu":
        """Delete menu items between `index1` and `index2` (`tk.Menu.delete` compatible)."""
        if not self._items:
            return self
        if index2 is None:
            if str(index1).lower().strip() in ("all", "end") and len(self._items) == 1:
                self._items.clear()
                return self
            i1 = self._resolve_index(index1)
            if 0 <= i1 < len(self._items):
                del self._items[i1]
        else:
            if index1 in (0, "0") and str(index2).lower().strip() in ("end", "last"):
                self._items.clear()
            else:
                i1 = max(0, self._resolve_index(index1))
                i2 = min(len(self._items) - 1, self._resolve_index(index2))
                if i1 <= i2:
                    del self._items[i1 : i2 + 1]
        return self

    def clear(self) -> "ModernContextMenu":
        """Remove all items from the menu."""
        self._items.clear()
        return self

    def entryconfigure(self, index: int | str, **kwargs) -> "ModernContextMenu":
        """Update properties of an existing menu item (`tk.Menu.entryconfigure` compatible)."""
        if not self._items:
            return self
        i = self._resolve_index(index)
        if 0 <= i < len(self._items):
            item = self._items[i]
            for k, v in kwargs.items():
                if hasattr(item, k):
                    setattr(item, k, v)
        return self

    entryconfig = entryconfigure

    def bind_context(self, widget: tk.Misc) -> None:
        """Bind this menu as a right-click context menu on `widget`."""
        widget.bind("<Button-3>", lambda e: self.popup(e.x_root, e.y_root), add="+")
        widget.bind("<Button-2>", lambda e: self.popup(e.x_root, e.y_root), add="+")

    def show_under(self, widget: tk.Misc, on_close: Optional[Callable[[], None]] = None) -> None:
        """Open this menu directly underneath `widget` (ideal for dropdown action buttons)."""
        if self.is_open:
            self.close()
            return
        self._on_close_cb = on_close
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        self.popup(x, y)

    def tk_popup(self, x_root: int, y_root: int, entry: str = "") -> None:
        """Drop-in compatibility for `tk.Menu.tk_popup(x, y)`."""
        self.popup(x_root, y_root)

    def grab_release(self) -> None:
        """Drop-in compatibility for `tk.Menu.grab_release()`."""
        pass

    def close(self) -> None:
        if self._popup_win is not None and self._popup_win.winfo_exists():
            try:
                self._popup_win.destroy()
            except tk.TclError:
                pass
        self._popup_win = None
        if self._on_close_cb is not None:
            cb = self._on_close_cb
            self._on_close_cb = None
            try:
                cb()
            except Exception:
                pass

    def _flatten_items(self) -> List[_MenuItem]:
        flat: List[_MenuItem] = []
        for it in self._items:
            if it.kind == "cascade" and it.menu is not None:
                if flat and flat[-1].kind != "separator":
                    flat.append(_MenuItem(kind="separator"))
                flat.append(_MenuItem(kind="header", label=it.label))
                flat.extend(it.menu._flatten_items())
            else:
                flat.append(it)
        return flat

    def popup(self, x_root: int, y_root: int) -> None:
        """Show the floating menu at screen coordinates `(x_root, y_root)`."""
        if self._popup_win is not None and self._popup_win.winfo_exists():
            try:
                self._popup_win.destroy()
            except tk.TclError:
                pass
            self._popup_win = None

        render_items = self._flatten_items()
        if not render_items:
            return

        from ..style import ThemeManager
        p = ThemeManager.instance().palette

        font_item = tkfont.Font(family=p.font_family, size=p.font_size)
        font_hdr = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2), weight="bold")
        font_acc = tkfont.Font(family=p.font_family, size=max(8, p.font_size - 2))

        item_h = 34
        hdr_h = 24
        sep_h = 9
        pad = 2
        outer_inset = 4
        content_h = pad * 2 + sum(
            sep_h if it.kind == "separator" else (hdr_h if it.kind == "header" else item_h)
            for it in render_items
        )
        total_h = content_h + outer_inset * 2
        max_lbl_w = max((font_item.measure(it.label) for it in render_items if it.label), default=120)
        w = max(self._width, max_lbl_w + 68)

        pop = tk.Toplevel(self._master)
        pop.wm_overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=p.bg)
        self._popup_win = pop

        mon_left, mon_top, mon_right, mon_bottom = get_monitor_work_area(
            self._master, x=x_root, y=y_root
        )
        mon_h = max(240, mon_bottom - mon_top)
        max_visible_h = max(240, min(mon_h - 40, int(mon_h * 0.72)))
        needs_scroll = total_h > max_visible_h
        visible_h = min(total_h, max_visible_h)
        sb_w = 12 if needs_scroll else 0
        popup_w = w + sb_w
        inner_w = max(80, w - outer_inset * 2)
        inner_h = max(60, visible_h - outer_inset * 2)

        outer_canvas = tk.Canvas(
            pop, width=popup_w, height=visible_h, bg=p.bg, bd=0, highlightthickness=0
        )
        outer_canvas.pack(fill="both", expand=True)

        outer_bg_img = create_rounded_rect_image(
            popup_w,
            visible_h,
            p.radius_lg,
            fill_hex=p.surface,
            border_hex=p.border_strong,
            border_width=1,
            bg_hex=p.bg,
        )
        self._outer_bg_ref = outer_bg_img
        outer_canvas.create_image(0, 0, image=outer_bg_img, anchor="nw")

        body = tk.Frame(outer_canvas, bg=p.surface, bd=0, highlightthickness=0)
        outer_canvas.create_window(
            outer_inset,
            outer_inset,
            window=body,
            anchor="nw",
            width=popup_w - outer_inset * 2,
            height=inner_h,
        )

        canvas = tk.Canvas(
            body,
            width=inner_w,
            height=inner_h,
            bg=p.surface,
            bd=0,
            highlightthickness=0,
            yscrollincrement=18,
        )
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = None
        if needs_scroll:
            from .table import ModernScrollbar

            scrollbar = ModernScrollbar(body, orient="vertical", command=canvas.yview, thickness=10)
            scrollbar.pack(side="right", fill="y", padx=(2, 0))
            canvas.configure(yscrollcommand=scrollbar.set)

        state = {"hovered_idx": -1}
        row_bounds: List[Tuple[int, int, int, _MenuItem]] = []

        def _is_checked(it: _MenuItem) -> bool:
            if it.variable is None:
                return False
            try:
                val = it.variable.get()
            except Exception:
                return False
            if it.kind == "radiobutton":
                return str(val) == str(it.value)
            if it.kind == "checkbutton":
                if isinstance(it.variable, tk.IntVar) and it.onvalue is True:
                    return int(val) == 1
                return bool(val) == bool(it.onvalue)
            return False

        def _render() -> None:
            if not canvas.winfo_exists():
                return
            canvas.delete("all")
            self._img_refs.clear()
            row_bounds.clear()

            accent = p.primary
            cy = pad
            has_left_slot_any = any(
                x.kind in ("radiobutton", "checkbutton") or x.icon for x in render_items
            )
            for idx, it in enumerate(render_items):
                if it.kind == "separator":
                    canvas.create_line(
                        8, cy + sep_h // 2, inner_w - 8, cy + sep_h // 2, fill=p.divider, width=1
                    )
                    cy += sep_h
                    continue

                if it.kind == "header":
                    canvas.create_text(
                        12,
                        cy + hdr_h // 2,
                        text=it.label.upper(),
                        fill=p.fg_subtle,
                        font=font_hdr,
                        anchor="w",
                    )
                    cy += hdr_h
                    continue

                is_disabled = getattr(it, "state", "normal") == "disabled"
                is_hov = (state["hovered_idx"] == idx) and not is_disabled
                checked = _is_checked(it)
                role = it.bootstyle.split("-")[0] if it.bootstyle else None
                fg_col = p.fg_subtle if is_disabled else (p.role_color(role) if role else (accent if checked else p.fg))

                if is_hov or checked:
                    hov_fill = (
                        p.role_subtle_bg(role)
                        if (is_hov and role)
                        else (p.surface_hover if is_hov else p.role_subtle_bg("primary"))
                    )
                    h_img = create_rounded_rect_image(
                        inner_w - 4,
                        item_h - 2,
                        p.radius_sm,
                        fill_hex=hov_fill,
                        bg_hex=p.surface,
                    )
                    self._img_refs.append(h_img)
                    canvas.create_image(2, cy + 1, image=h_img, anchor="nw")

                mid_y = cy + item_h // 2
                if it.kind == "radiobutton":
                    if checked:
                        dot = create_circle_image(8, fill_hex=accent, bg_hex=p.surface_hover if is_hov else p.role_subtle_bg("primary"))
                        self._img_refs.append(dot)
                        canvas.create_image(18, mid_y, image=dot, anchor="center")
                    else:
                        ring = create_circle_image(12, fill_hex=p.surface_hover if is_hov else p.surface, border_hex=p.border_strong, border_width=1, bg_hex=p.surface_hover if is_hov else p.surface)
                        self._img_refs.append(ring)
                        canvas.create_image(18, mid_y, image=ring, anchor="center")
                elif it.kind == "checkbutton":
                    if checked:
                        chk = create_icon_image("check", size=14, color=accent)
                        self._img_refs.append(chk)
                        canvas.create_image(18, mid_y, image=chk, anchor="center")
                elif it.icon:
                    if it.icon.lower().strip() in AVAILABLE_ICONS:
                        ic_img = create_icon_image(it.icon, size=15, color=fg_col)
                        self._img_refs.append(ic_img)
                        canvas.create_image(18, mid_y, image=ic_img, anchor="center")
                    else:
                        canvas.create_text(18, mid_y, text=it.icon, fill=fg_col, font=font_item, anchor="center")

                has_left_slot = it.kind in ("radiobutton", "checkbutton") or has_left_slot_any
                text_x = 34 if has_left_slot else 12
                canvas.create_text(text_x, mid_y, text=it.label, fill=fg_col, font=font_item, anchor="w")

                if it.accelerator:
                    canvas.create_text(inner_w - 10, mid_y, text=it.accelerator, fill=p.fg_subtle, font=font_acc, anchor="e")

                row_bounds.append((cy, cy + item_h, idx, it))
                cy += item_h

            canvas.configure(scrollregion=(0, 0, inner_w, cy + pad))

        def _on_motion(e: tk.Event) -> None:
            ev_y = int(canvas.canvasy(e.y))
            found = -1
            for y1, y2, idx, it in row_bounds:
                if y1 <= ev_y <= y2:
                    if getattr(it, "state", "normal") != "disabled":
                        found = idx
                    break
            if found != state["hovered_idx"]:
                state["hovered_idx"] = found
                canvas.configure(cursor="hand2" if found >= 0 else "arrow")
                _render()

        def _on_click(e: tk.Event) -> None:
            ev_y = int(canvas.canvasy(e.y))
            for y1, y2, _idx, it in row_bounds:
                if y1 <= ev_y <= y2:
                    if getattr(it, "state", "normal") == "disabled":
                        return
                    if it.kind == "radiobutton" and it.variable is not None:
                        try:
                            it.variable.set(it.value)
                        except Exception:
                            pass
                    elif it.kind == "checkbutton" and it.variable is not None:
                        try:
                            cur = _is_checked(it)
                            if isinstance(it.variable, tk.IntVar) and it.onvalue is True and it.offvalue is False:
                                it.variable.set(0 if cur else 1)
                            else:
                                it.variable.set(it.offvalue if cur else it.onvalue)
                        except Exception:
                            pass
                    self.close()
                    if it.command is not None:
                        it.command()
                    return

        def _on_mousewheel(e: tk.Event) -> str:
            if not needs_scroll:
                return "break"
            if getattr(e, "delta", 0):
                steps = int(-1 * (e.delta / 120)) * 3
                if steps == 0:
                    steps = -3 if e.delta > 0 else 3
                canvas.yview_scroll(steps, "units")
            elif getattr(e, "num", None) == 4:
                canvas.yview_scroll(-3, "units")
            elif getattr(e, "num", None) == 5:
                canvas.yview_scroll(3, "units")
            return "break"

        def _on_focus_out(_e: tk.Event) -> None:
            try:
                focused = pop.focus_get()
                if focused is not None and str(focused).startswith(str(pop)):
                    return
            except Exception:
                pass
            self.close()

        canvas.bind("<Motion>", _on_motion)
        canvas.bind("<ButtonRelease-1>", _on_click)
        if needs_scroll:
            for w_bind in (pop, outer_canvas, body, canvas, scrollbar):
                if w_bind is not None:
                    w_bind.bind("<MouseWheel>", _on_mousewheel)
                    w_bind.bind("<Button-4>", _on_mousewheel)
                    w_bind.bind("<Button-5>", _on_mousewheel)
            pop.bind("<Up>", lambda _e: canvas.yview_scroll(-2, "units"))
            pop.bind("<Down>", lambda _e: canvas.yview_scroll(2, "units"))
            pop.bind("<Prior>", lambda _e: canvas.yview_scroll(-10, "units"))
            pop.bind("<Next>", lambda _e: canvas.yview_scroll(10, "units"))
        _render()

        if x_root + popup_w > mon_right - 8:
            x_root = max(mon_left + 8, mon_right - popup_w - 8)
        elif x_root < mon_left + 8:
            x_root = mon_left + 8

        if y_root + visible_h > mon_bottom - 8:
            if y_root - visible_h - 36 >= mon_top + 8:
                y_root = y_root - visible_h - 36
            else:
                y_root = max(mon_top + 8, mon_bottom - visible_h - 8)
        elif y_root < mon_top + 8:
            y_root = mon_top + 8

        pop.geometry(f"{popup_w}x{visible_h}+{x_root}+{y_root}")
        pop.focus_force()
        pop.bind("<FocusOut>", _on_focus_out)
        pop.bind("<Escape>", lambda e: self.close())


class ModernMenuButton(tk.Canvas, ThemedWidgetMixin):
    """Modern rounded dropdown menu button (`mtk.Menubutton` / `mtk.MenuButton`) with vector chevron and attached `ModernMenu`."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Menu",
        menu: Optional[ModernContextMenu] = None,
        bootstyle: str = "secondary-outline",
        width: Optional[int] = None,
        height: int = 34,
        state: str = "normal",
        **kwargs,
    ) -> None:
        kwargs.pop("style", None)
        self._text = text
        self._menu = menu
        self._role = bootstyle.split("-")[0] if bootstyle else "secondary"
        self._variant = "outline" if "outline" in bootstyle else "solid"
        self._state = state
        self._base_height = height
        self._is_hovered = False

        p = self.palette
        self._font = tkfont.Font(root=master, family=p.font_family, size=p.font_size, weight="bold")

        if width is None:
            px_width = max(96, self._font.measure(text) + 46)
        elif width <= 42:
            px_width = max(self._font.measure(text) + 44, int(width * 8 + 30))
        else:
            px_width = int(width)
        self._base_px_width = px_width

        super().__init__(
            master,
            width=px_width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if state == "normal" else "arrow",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def _set_hover(self, hov: bool) -> None:
        self._is_hovered = hov
        self._redraw()

    def _on_click(self, _e: tk.Event) -> None:
        if self._state == "disabled" or self._menu is None:
            return
        if hasattr(self._menu, "show_under"):
            self._menu.show_under(self, on_close=lambda: self._redraw() if self.winfo_exists() else None)
            self._redraw()
        elif hasattr(self._menu, "tk_popup"):
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height() + 4
            self._menu.tk_popup(x, y)

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            if isinstance(cnf, str):
                return self.cget(cnf)
            kwargs.update(cnf)
        text_changed = "text" in kwargs
        if text_changed:
            self._text = str(kwargs.pop("text"))
        if "menu" in kwargs:
            self._menu = kwargs.pop("menu")
        if "state" in kwargs:
            self._state = str(kwargs.pop("state"))
            super().configure(cursor="hand2" if self._state == "normal" else "arrow")
        if "bootstyle" in kwargs:
            bs = str(kwargs.pop("bootstyle"))
            self._role = bs.split("-")[0] if bs else "secondary"
            self._variant = "outline" if "outline" in bs else "solid"
        if "width" in kwargs:
            w_val = int(kwargs.pop("width"))
            px_w = max(self._font.measure(self._text) + 44, int(w_val * 8 + 30)) if w_val <= 42 else w_val
            self._base_px_width = px_w
            kwargs["width"] = px_w
        elif text_changed:
            kwargs["width"] = max(self._base_px_width, self._font.measure(self._text) + 44)
        kwargs.pop("style", None)
        if kwargs:
            super().configure(**kwargs)
        self._redraw()

    config = configure

    def cget(self, key: str):
        if key == "text":
            return self._text
        if key == "menu":
            return self._menu
        if key == "state":
            return self._state
        if key == "style":
            return "TMenubutton"
        return super().cget(key)

    def __getitem__(self, key: str):
        return self.cget(key)

    def __setitem__(self, key: str, value) -> None:
        self.configure(**{key: value})

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

        is_open = bool(self._menu and getattr(self._menu, "is_open", False))
        accent = p.primary if is_open else p.role_color(self._role)

        if self._variant == "outline":
            fill_col = p.role_subtle_bg("primary" if is_open else self._role) if (is_open or self._is_hovered) else p.surface
            border_col = p.primary if is_open else (accent if self._is_hovered else p.border_strong)
            border_w = 2 if is_open else 1
            fg_col = p.primary if is_open else p.fg
        else:
            fill_col = p.role_hover(self._role) if (is_open or self._is_hovered) else accent
            border_col = fill_col
            border_w = 0
            fg_col = p.role_text(self._role)

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            r,
            fill_hex=fill_col,
            border_hex=border_col,
            border_width=border_w,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw")

        self.create_text(
            14,
            h // 2,
            text=self._text,
            fill=p.fg_subtle if self._state == "disabled" else fg_col,
            font=self._font,
            anchor="w",
        )

        chev_name = "chevron_up" if is_open else "chevron_down"
        chev_col = p.primary if is_open else (fg_col if self._is_hovered else p.fg_muted)
        self._chev_img = create_icon_image(chev_name, size=14, color=chev_col)
        self.create_image(w - 14, h // 2, image=self._chev_img, anchor="center")


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

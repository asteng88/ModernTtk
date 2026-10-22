"""Modern Treeview / DataTable and Scrollbar widgets for ModernTkk."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ..themes import SEMANTIC_ROLES, ThemePalette
from ..utils import blend_colors, create_rounded_rect_image
from .base import ModernFrame, ThemedWidgetMixin


class ModernScrollbar(tk.Canvas, ThemedWidgetMixin):
    """Sleek rounded pill scrollbar (vertical or horizontal) that replaces the blocky native scrollbar."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        orient: str = "vertical",
        command: Optional[Callable[..., Any]] = None,
        bootstyle: str = "secondary",
        thickness: int = 10,
        **kwargs,
    ) -> None:
        self._orient = orient
        self._command = command
        self._role = bootstyle.split("-")[0] if bootstyle else "secondary"
        self._first = 0.0
        self._last = 1.0
        self._is_hovered = False
        self._is_dragging = False
        self._drag_start_pos = 0
        self._drag_start_first = 0.0

        w = thickness if orient == "vertical" else 100
        h = 100 if orient == "vertical" else thickness

        super().__init__(
            master,
            width=w,
            height=h,
            bd=0,
            highlightthickness=0,
            relief="flat",
            **kwargs,
        )
        self._init_themed()

        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._redraw())

    def set(self, first: float | str, last: float | str) -> None:
        """Standard Tkinter scrollbar `set(first, last)` method."""
        self._first = max(0.0, min(1.0, float(first)))
        self._last = max(0.0, min(1.0, float(last)))
        self._redraw()

    def _set_hover(self, hovered: bool) -> None:
        self._is_hovered = hovered
        self._redraw()

    def _on_press(self, e: tk.Event) -> None:
        if self._last - self._first >= 0.999:
            return
        self._is_dragging = True
        self._drag_start_pos = e.y if self._orient == "vertical" else e.x
        self._drag_start_first = self._first
        self._redraw()

    def _on_drag(self, e: tk.Event) -> None:
        if not self._is_dragging or self._command is None:
            return
        total = self.winfo_height() if self._orient == "vertical" else self.winfo_width()
        if total <= 1:
            return
        delta_px = (e.y if self._orient == "vertical" else e.x) - self._drag_start_pos
        new_first = max(0.0, min(1.0 - (self._last - self._first), self._drag_start_first + delta_px / total))
        self._command("moveto", new_first)

    def _on_release(self, _e: tk.Event) -> None:
        self._is_dragging = False
        self._redraw()

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        # Auto-hide thumb when all content fits
        if self._last - self._first >= 0.999:
            return

        w = max(4, self.winfo_width())
        h = max(4, self.winfo_height())

        if self._is_dragging:
            thumb_col = p.role_color("primary")
        elif self._is_hovered:
            thumb_col = p.fg_muted
        else:
            thumb_col = p.border_strong

        if self._orient == "vertical":
            thumb_h = max(24, int((self._last - self._first) * h))
            avail_h = h - thumb_h
            denom = max(0.001, 1.0 - (self._last - self._first))
            y1 = int((self._first / denom) * avail_h)
            pad = 2
            tw = max(4, w - pad * 2)
            self._thumb_img = create_rounded_rect_image(
                tw,
                thumb_h,
                tw // 2,
                fill_hex=thumb_col,
                bg_hex=parent_bg,
            )
            self.create_image(pad, y1, image=self._thumb_img, anchor="nw")
        else:
            thumb_w = max(24, int((self._last - self._first) * w))
            avail_w = w - thumb_w
            denom = max(0.001, 1.0 - (self._last - self._first))
            x1 = int((self._first / denom) * avail_w)
            pad = 2
            th = max(4, h - pad * 2)
            self._thumb_img = create_rounded_rect_image(
                thumb_w,
                th,
                th // 2,
                fill_hex=thumb_col,
                bg_hex=parent_bg,
            )
            self.create_image(x1, pad, image=self._thumb_img, anchor="nw")


class ModernTreeview(tk.Canvas, ThemedWidgetMixin):
    """Modern rounded data table / treeview with sortable headers, striped rows, hover highlights, and semantic row tags.

    Features:
    - Rounded anti-aliased surface card container (`ModernTreeview` is a Canvas wrapping a custom header bar,
      borderless `ttk.Treeview`, and a sleek `ModernScrollbar`).
    - Clickable column headers with interactive ascending/descending sort (`▲` / `▼`).
    - Automatic alternating striped rows and smooth hover row highlight.
    - Built-in semantic row tags (`tag="success"`, `"warning"`, `"danger"`, `"info"`, `"primary"`).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Sequence[Tuple[str, str, int] | str] = (),
        rows: Optional[Sequence[Sequence[Any]]] = None,
        height: int = 8,
        striped: bool = True,
        sortable: bool = True,
        bootstyle: str = "primary",
        surface_role: str = "surface",
        on_select: Optional[Callable[[List[Tuple[Any, ...]]], None]] = None,
        **kwargs,
    ) -> None:
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._surface_role = surface_role
        self._striped = striped
        self._sortable = sortable
        self._on_select = on_select
        self._row_count = height
        self._row_px = 36
        self._header_h = 40

        # Normalize column specs: list of (col_id, heading_text, width)
        self._col_specs: List[Tuple[str, str, int]] = []
        for c in columns:
            if isinstance(c, (tuple, list)):
                cid = str(c[0])
                htitle = str(c[1]) if len(c) > 1 else cid.capitalize()
                cwidth = int(c[2]) if len(c) > 2 else 140
                self._col_specs.append((cid, htitle, cwidth))
            else:
                cid = str(c)
                self._col_specs.append((cid, cid.capitalize(), 140))

        self._sort_col: Optional[str] = None
        self._sort_desc: bool = False
        self._hovered_row: Optional[str] = None
        self._row_base_tags: Dict[str, Tuple[str, ...]] = {}

        total_w = sum(c[2] for c in self._col_specs) + 28 if self._col_specs else 640
        total_h = self._header_h + height * self._row_px + 12

        super().__init__(
            master,
            width=total_w,
            height=total_h,
            bd=0,
            highlightthickness=0,
            relief="flat",
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        surf_bg = getattr(p, self._surface_role, p.surface)

        self._inner = ModernFrame(self, surface_role=self._surface_role)

        # Custom modern header bar (avoids legacy ttk bevel headers)
        self._header_canvas = tk.Canvas(
            self._inner,
            height=self._header_h,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if sortable else "arrow",
        )
        self._header_canvas.pack(fill="x")
        self._header_canvas.bind("<ButtonRelease-1>", self._on_header_click)
        self._header_canvas.bind("<Configure>", lambda e: self._draw_header())

        body_frame = ModernFrame(self._inner, surface_role=self._surface_role)
        body_frame.pack(fill="both", expand=True)

        col_ids = [c[0] for c in self._col_specs]
        self.tree = ttk.Treeview(
            body_frame,
            columns=col_ids,
            show="headings",  # Hide tree column #0; we render our own modern header above
            height=height,
            selectmode="browse",
        )
        # Hide native ttk headings since we render a custom rounded header bar
        self.tree["show"] = ""
        for cid, htitle, cwidth in self._col_specs:
            self.tree.heading(cid, text=htitle, anchor="w")
            self.tree.column(cid, width=cwidth, anchor="w", stretch=True)

        self._scrollbar = ModernScrollbar(
            body_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=self._scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y", padx=(4, 0))

        self._win_id = self.create_window(6, 6, window=self._inner, anchor="nw")

        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.bind("<Configure>", self._on_canvas_configure)

        self._configure_tags()

        if rows:
            for r in rows:
                self.insert_row(r)

        self._redraw()

    def insert_row(
        self,
        values: Sequence[Any],
        tag: Optional[str] = None,
        index: str | int = "end",
    ) -> str:
        """Insert a row into the modern table with optional semantic tag ('success', 'warning', 'danger', 'info')."""
        row_idx = len(self.tree.get_children())
        stripe_tag = "even" if row_idx % 2 == 0 else "odd"
        tags = (stripe_tag, tag) if tag else (stripe_tag,)
        iid = self.tree.insert("", index, values=tuple(values), tags=tags)
        self._row_base_tags[iid] = tags
        return iid

    def clear(self) -> None:
        """Delete all rows from the table."""
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._row_base_tags.clear()
        self._hovered_row = None

    def get_selected_rows(self) -> List[Tuple[Any, ...]]:
        """Return the value tuples of all currently selected rows."""
        return [tuple(self.tree.item(iid, "values")) for iid in self.tree.selection()]

    def sort_by(self, col_id: str, descending: Optional[bool] = None) -> None:
        """Sort the table rows by a column ID."""
        col_ids = [c[0] for c in self._col_specs]
        if col_id not in col_ids:
            return
        if descending is None:
            if self._sort_col == col_id:
                self._sort_desc = not self._sort_desc
            else:
                self._sort_col = col_id
                self._sort_desc = False
        else:
            self._sort_col = col_id
            self._sort_desc = descending

        col_idx = col_ids.index(col_id)
        items = list(self.tree.get_children(""))

        def _sort_key(iid: str) -> Any:
            vals = self.tree.item(iid, "values")
            raw = str(vals[col_idx]) if col_idx < len(vals) else ""
            # Try numeric extraction (e.g. "11.4 ms" -> 11.4)
            num_part = raw.split()[0].replace(",", "").replace("%", "") if raw else ""
            try:
                return (0, float(num_part))
            except ValueError:
                return (1, raw.lower())

        items.sort(key=_sort_key, reverse=self._sort_desc)
        for idx, iid in enumerate(items):
            self.tree.move(iid, "", idx)
            base_tags = [t for t in self._row_base_tags.get(iid, ()) if t not in ("even", "odd")]
            stripe = "even" if idx % 2 == 0 else "odd"
            new_tags = (stripe, *base_tags)
            self._row_base_tags[iid] = new_tags
            self.tree.item(iid, tags=new_tags)

        self._draw_header()

    def _on_header_click(self, e: tk.Event) -> None:
        if not self._sortable or not self._col_specs:
            return
        cur_x = 0
        for cid, _, _ in self._col_specs:
            col_w = int(self.tree.column(cid, "width"))
            if cur_x <= e.x <= cur_x + col_w:
                self.sort_by(cid)
                return
            cur_x += col_w

    def _on_tree_motion(self, e: tk.Event) -> None:
        iid = self.tree.identify_row(e.y)
        if iid != self._hovered_row:
            if self._hovered_row and self.tree.exists(self._hovered_row):
                self.tree.item(self._hovered_row, tags=self._row_base_tags.get(self._hovered_row, ()))
            self._hovered_row = iid if iid else None
            if self._hovered_row and self.tree.exists(self._hovered_row):
                base = self._row_base_tags.get(self._hovered_row, ())
                self.tree.item(self._hovered_row, tags=("hover", *base))

    def _on_tree_leave(self, _e: tk.Event) -> None:
        if self._hovered_row and self.tree.exists(self._hovered_row):
            self.tree.item(self._hovered_row, tags=self._row_base_tags.get(self._hovered_row, ()))
        self._hovered_row = None

    def _on_tree_select(self, _e: tk.Event) -> None:
        if self._on_select is not None:
            self._on_select(self.get_selected_rows())

    def _on_canvas_configure(self, e: tk.Event) -> None:
        iw = max(40, e.width - 12)
        ih = max(40, e.height - 12)
        self.itemconfigure(self._win_id, width=iw, height=ih)
        self._redraw()

    def _configure_tags(self) -> None:
        p = self.palette
        surf = getattr(p, self._surface_role, p.surface)
        stripe_bg = blend_colors(surf, p.surface_alt, 0.45) if self._striped else surf

        self.tree.tag_configure("even", background=surf, foreground=p.fg)
        self.tree.tag_configure("odd", background=stripe_bg, foreground=p.fg)
        self.tree.tag_configure("hover", background=p.surface_hover)

        for role in SEMANTIC_ROLES:
            rc = p.role_color(role)
            self.tree.tag_configure(role, foreground=rc)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._configure_tags()
        self._redraw()

    def _draw_header(self) -> None:
        p = self.palette
        surf = getattr(p, self._surface_role, p.surface)
        self._header_canvas.configure(bg=surf)
        self._header_canvas.delete("all")

        w = max(self._header_canvas.winfo_width(), 200)
        h = self._header_h

        self._hdr_bg_img = create_rounded_rect_image(
            w,
            h - 4,
            p.radius_sm,
            fill_hex=p.surface_alt,
            bg_hex=surf,
        )
        self._header_canvas.create_image(0, 0, image=self._hdr_bg_img, anchor="nw")

        font_hdr = (p.font_family, p.font_size, "bold")
        accent = p.role_color(self._role)

        cur_x = 0
        for cid, htitle, _ in self._col_specs:
            col_w = int(self.tree.column(cid, "width"))
            is_sorted = self._sort_col == cid
            arrow = (" ▼" if self._sort_desc else " ▲") if is_sorted else ""
            fg = accent if is_sorted else p.fg_muted
            self._header_canvas.create_text(
                cur_x + 12,
                (h - 4) // 2,
                text=f"{htitle}{arrow}",
                fill=fg,
                font=font_hdr,
                anchor="w",
            )
            cur_x += col_w

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("card_bg")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        surf = getattr(p, self._surface_role, p.surface)

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            p.radius_lg,
            fill_hex=surf,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw", tags="card_bg")
        self.tag_lower("card_bg")
        self._draw_header()

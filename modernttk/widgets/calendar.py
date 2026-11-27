"""Modern interactive Calendar and DatePicker widgets for ModernTtk."""

from __future__ import annotations

import calendar
import datetime as dt
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, List, Optional, Tuple

from ..themes import ThemePalette
from ..utils import create_circle_image, create_rounded_rect_image
from .base import ThemedWidgetMixin


class ModernCalendar(tk.Canvas, ThemedWidgetMixin):
    """Interactive modern calendar supporting day/month/year drill-down and single or range date selection."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        selected_date: Optional[dt.date] = None,
        select_mode: str = "single",  # "single" or "range"
        on_select: Optional[Callable[[dt.date | Tuple[dt.date, Optional[dt.date]]], None]] = None,
        bootstyle: str = "primary",
        width: int = 304,
        height: int = 316,
        **kwargs,
    ) -> None:
        today = dt.date.today()
        self._today = today
        self._selected: dt.date = selected_date or today
        self._range_start: Optional[dt.date] = selected_date
        self._range_end: Optional[dt.date] = None
        self._select_mode = select_mode
        self._on_select = on_select
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"

        self._view_year = self._selected.year
        self._view_month = self._selected.month
        self._view_mode = "days"  # "days", "months", "years"
        self._hover_target: Optional[Tuple[str, int | dt.date]] = None
        self._highlighted_dates: dict[dt.date, str] = {}

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font_header = tkfont.Font(family=p.font_family, size=p.font_size + 1, weight="bold")
        self._font_Dow = tkfont.Font(family=p.font_family, size=p.font_size - 1, weight="bold")
        self._font_day = tkfont.Font(family=p.font_family, size=p.font_size)
        self._font_small = tkfont.Font(family=p.font_family, size=p.font_size - 1)

        self._hit_boxes: List[Tuple[int, int, int, int, str, int | dt.date]] = []
        self._cell_imgs: List[tk.PhotoImage] = []

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_hover(None))
        self.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get_date(self) -> dt.date:
        return self._selected

    def get_range(self) -> Tuple[Optional[dt.date], Optional[dt.date]]:
        return self._range_start, self._range_end

    def set_date(self, date_val: dt.date, notify: bool = False) -> None:
        self._selected = date_val
        self._range_start = date_val
        self._range_end = None
        self._view_year = date_val.year
        self._view_month = date_val.month
        self._redraw()
        if notify and self._on_select:
            self._on_select(date_val if self._select_mode == "single" else (self._range_start, self._range_end))

    def highlight_date(self, date_val: dt.date, bootstyle: str = "warning") -> None:
        """Highlight a specific date (e.g. holiday, fiscal start/end) with a semantic color role."""
        self._highlighted_dates[date_val] = bootstyle.split("-")[0]
        self._redraw()

    def unhighlight_date(self, date_val: dt.date) -> None:
        """Remove a highlight from a specific date."""
        if date_val in self._highlighted_dates:
            del self._highlighted_dates[date_val]
            self._redraw()

    def clear_highlights(self) -> None:
        """Clear all custom highlighted dates."""
        self._highlighted_dates.clear()
        self._redraw()

    def _set_hover(self, target: Optional[Tuple[str, int | dt.date]]) -> None:
        if self._hover_target != target:
            self._hover_target = target
            self._redraw()

    def _on_motion(self, e: tk.Event) -> None:
        for x1, y1, x2, y2, kind, payload in self._hit_boxes:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self._set_hover((kind, payload))
                return
        self._set_hover(None)

    def _on_click(self, e: tk.Event) -> None:
        for x1, y1, x2, y2, kind, payload in self._hit_boxes:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self._handle_action(kind, payload)
                return

    def _handle_action(self, kind: str, payload: int | dt.date) -> None:
        if kind == "prev":
            if self._view_mode == "days":
                if self._view_month == 1:
                    self._view_month = 12
                    self._view_year -= 1
                else:
                    self._view_month -= 1
            elif self._view_mode == "months":
                self._view_year -= 1
            else:
                self._view_year -= 12
            self._redraw()
        elif kind == "next":
            if self._view_mode == "days":
                if self._view_month == 12:
                    self._view_month = 1
                    self._view_year += 1
                else:
                    self._view_month += 1
            elif self._view_mode == "months":
                self._view_year += 1
            else:
                self._view_year += 12
            self._redraw()
        elif kind == "title":
            if self._view_mode == "days":
                self._view_mode = "months"
            elif self._view_mode == "months":
                self._view_mode = "years"
            else:
                self._view_mode = "days"
            self._redraw()
        elif kind == "today":
            self.set_date(self._today, notify=True)
            self._view_mode = "days"
            self._redraw()
        elif kind == "month" and isinstance(payload, int):
            self._view_month = payload
            self._view_mode = "days"
            self._redraw()
        elif kind == "year" and isinstance(payload, int):
            self._view_year = payload
            self._view_mode = "months"
            self._redraw()
        elif kind == "day" and isinstance(payload, dt.date):
            self._selected = payload
            self._view_year = payload.year
            self._view_month = payload.month
            if self._select_mode == "range":
                if self._range_start is None or (self._range_start is not None and self._range_end is not None):
                    self._range_start = payload
                    self._range_end = None
                else:
                    if payload < self._range_start:
                        self._range_end = self._range_start
                        self._range_start = payload
                    else:
                        self._range_end = payload
                self._redraw()
                if self._on_select:
                    self._on_select((self._range_start, self._range_end))
            else:
                self._redraw()
                if self._on_select:
                    self._on_select(payload)

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")
        self._hit_boxes.clear()
        self._cell_imgs.clear()

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))
        accent = p.role_color(self._role)

        # Outer card container
        self._card_img = create_rounded_rect_image(
            w,
            h,
            p.radius_lg,
            fill_hex=p.surface,
            border_hex=p.border,
            border_width=1,
            bg_hex=parent_bg,
            bottom_border_hex=p.border_strong,
        )
        self.create_image(0, 0, image=self._card_img, anchor="nw")

        # Header Bar
        if self._view_mode == "days":
            title_str = f"{calendar.month_name[self._view_month]} {self._view_year}"
        elif self._view_mode == "months":
            title_str = f"{self._view_year}"
        else:
            start_y = (self._view_year // 12) * 12
            title_str = f"{start_y} – {start_y + 11}"

        # Prev / Next buttons
        for bx, kind, glyph in [(24, "prev", "‹"), (w - 24, "next", "›")]:
            is_hov = self._hover_target == (kind, 0)
            if is_hov:
                btn_img = create_circle_image(28, fill_hex=p.surface_hover, bg_hex=p.surface)
                self._cell_imgs.append(btn_img)
                self.create_image(bx - 14, 12, image=btn_img, anchor="nw")
            self.create_text(bx, 26, text=glyph, fill=p.fg, font=self._font_header)
            self._hit_boxes.append((bx - 16, 10, bx + 16, 42, kind, 0))

        # Title drilldown button
        title_hov = self._hover_target == ("title", 0)
        self.create_text(
            w // 2,
            26,
            text=f"{title_str} ▾",
            fill=accent if title_hov else p.fg,
            font=self._font_header,
        )
        self._hit_boxes.append((60, 10, w - 60, 42, "title", 0))

        self.create_line(14, 46, w - 14, 46, fill=p.divider, width=1)

        if self._view_mode == "days":
            self._draw_days_grid(w, h, p, accent)
        elif self._view_mode == "months":
            self._draw_months_grid(w, h, p, accent)
        else:
            self._draw_years_grid(w, h, p, accent)

        # Footer "Today" shortcut
        footer_y = h - 22
        today_hov = self._hover_target == ("today", 0)
        self.create_line(14, h - 38, w - 14, h - 38, fill=p.divider, width=1)
        self.create_text(
            w // 2,
            footer_y,
            text=f"Today: {self._today.strftime('%b %d, %Y')}",
            fill=p.role_hover(self._role) if today_hov else accent,
            font=self._font_small,
        )
        self._hit_boxes.append((40, h - 36, w - 40, h - 6, "today", 0))

    def _draw_days_grid(self, w: int, h: int, p: ThemePalette, accent: str) -> None:
        pad_x = 14
        col_w = (w - pad_x * 2) / 7.0
        dow_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, name in enumerate(dow_names):
            cx = int(pad_x + col_w * (i + 0.5))
            self.create_text(cx, 62, text=name, fill=p.fg_muted, font=self._font_Dow)

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(self._view_year, self._view_month)
        while len(weeks) < 6:
            last_day = weeks[-1][-1]
            next_week = [last_day + dt.timedelta(days=i) for i in range(1, 8)]
            weeks.append(next_week)

        grid_top = 78
        row_h = (h - 38 - grid_top - 6) / 6.0
        cell_d = min(int(col_w) - 4, int(row_h) - 2, 34)

        for r_idx, week in enumerate(weeks[:6]):
            cy = int(grid_top + row_h * (r_idx + 0.5))
            for c_idx, d in enumerate(week):
                cx = int(pad_x + col_w * (c_idx + 0.5))
                in_month = d.month == self._view_month
                is_today = d == self._today
                is_hov = self._hover_target == ("day", d)

                if self._select_mode == "range" and self._range_start:
                    is_selected = d in (self._range_start, self._range_end)
                    in_range = (
                        self._range_end is not None
                        and self._range_start < d < self._range_end
                    )
                else:
                    is_selected = d == self._selected
                    in_range = False

                if is_selected:
                    img = create_circle_image(cell_d, fill_hex=accent, bg_hex=p.surface)
                    self._cell_imgs.append(img)
                    self.create_image(cx - cell_d // 2, cy - cell_d // 2, image=img, anchor="nw")
                    fg = p.role_text(self._role)
                elif in_range:
                    subtle = p.role_subtle_bg(self._role)
                    img = create_rounded_rect_image(
                        int(col_w),
                        cell_d - 4,
                        6,
                        fill_hex=subtle,
                        bg_hex=p.surface,
                    )
                    self._cell_imgs.append(img)
                    self.create_image(cx - int(col_w) // 2, cy - (cell_d - 4) // 2, image=img, anchor="nw")
                    fg = accent
                elif is_hov:
                    img = create_circle_image(cell_d, fill_hex=p.surface_hover, bg_hex=p.surface)
                    self._cell_imgs.append(img)
                    self.create_image(cx - cell_d // 2, cy - cell_d // 2, image=img, anchor="nw")
                    fg = p.fg
                elif is_today:
                    img = create_circle_image(
                        cell_d,
                        fill_hex=p.surface,
                        border_hex=accent,
                        border_width=1,
                        bg_hex=p.surface,
                    )
                    self._cell_imgs.append(img)
                    self.create_image(cx - cell_d // 2, cy - cell_d // 2, image=img, anchor="nw")
                    fg = accent
                elif d in self._highlighted_dates:
                    h_role = self._highlighted_dates[d]
                    h_col = p.role_color(h_role)
                    h_bg = p.role_subtle_bg(h_role)
                    img = create_circle_image(
                        cell_d,
                        fill_hex=h_bg,
                        border_hex=h_col,
                        border_width=1,
                        bg_hex=p.surface,
                    )
                    self._cell_imgs.append(img)
                    self.create_image(cx - cell_d // 2, cy - cell_d // 2, image=img, anchor="nw")
                    fg = h_col
                else:
                    fg = p.fg if in_month else p.fg_subtle

                self.create_text(cx, cy, text=str(d.day), fill=fg, font=self._font_day)
                self._hit_boxes.append((
                    cx - int(col_w // 2),
                    cy - int(row_h // 2),
                    cx + int(col_w // 2),
                    cy + int(row_h // 2),
                    "day",
                    d,
                ))

    def _draw_months_grid(self, w: int, h: int, p: ThemePalette, accent: str) -> None:
        pad_x = 18
        grid_top = 60
        col_w = (w - pad_x * 2) / 3.0
        row_h = (h - 46 - grid_top) / 4.0

        for m in range(1, 13):
            idx = m - 1
            r_idx, c_idx = divmod(idx, 3)
            cx = int(pad_x + col_w * (c_idx + 0.5))
            cy = int(grid_top + row_h * (r_idx + 0.5))
            bw, bh = int(col_w) - 10, int(row_h) - 10

            is_sel = m == self._view_month
            is_hov = self._hover_target == ("month", m)

            if is_sel or is_hov:
                fill = accent if is_sel else p.surface_hover
                img = create_rounded_rect_image(bw, bh, 8, fill_hex=fill, bg_hex=p.surface)
                self._cell_imgs.append(img)
                self.create_image(cx - bw // 2, cy - bh // 2, image=img, anchor="nw")

            fg = p.role_text(self._role) if is_sel else p.fg
            self.create_text(cx, cy, text=calendar.month_abbr[m], fill=fg, font=self._font_day)
            self._hit_boxes.append((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2, "month", m))

    def _draw_years_grid(self, w: int, h: int, p: ThemePalette, accent: str) -> None:
        pad_x = 18
        grid_top = 60
        col_w = (w - pad_x * 2) / 3.0
        row_h = (h - 46 - grid_top) / 4.0
        start_y = (self._view_year // 12) * 12

        for idx in range(12):
            yr = start_y + idx
            r_idx, c_idx = divmod(idx, 3)
            cx = int(pad_x + col_w * (c_idx + 0.5))
            cy = int(grid_top + row_h * (r_idx + 0.5))
            bw, bh = int(col_w) - 10, int(row_h) - 10

            is_sel = yr == self._view_year
            is_hov = self._hover_target == ("year", yr)

            if is_sel or is_hov:
                fill = accent if is_sel else p.surface_hover
                img = create_rounded_rect_image(bw, bh, 8, fill_hex=fill, bg_hex=p.surface)
                self._cell_imgs.append(img)
                self.create_image(cx - bw // 2, cy - bh // 2, image=img, anchor="nw")

            fg = p.role_text(self._role) if is_sel else p.fg
            self.create_text(cx, cy, text=str(yr), fill=fg, font=self._font_day)
            self._hit_boxes.append((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2, "year", yr))


class ModernDatePicker(tk.Canvas, ThemedWidgetMixin):
    """Rounded date input field with calendar icon that opens a popup ModernCalendar."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        selected_date: Optional[dt.date] = None,
        date_format: str = "%Y-%m-%d",
        on_select: Optional[Callable[[dt.date], None]] = None,
        bootstyle: str = "primary",
        width: int = 200,
        height: int = 38,
        **kwargs,
    ) -> None:
        self._date = selected_date or dt.date.today()
        self._date_format = date_format
        self._on_select = on_select
        self._role = bootstyle.split("-")[0] if bootstyle else "primary"
        self._is_hovered = False
        self._popup: Optional[tk.Toplevel] = None

        super().__init__(
            master,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
            **kwargs,
        )
        self._init_themed()

        p = self.palette
        self._font = tkfont.Font(family=p.font_family, size=p.font_size)

        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._toggle_popup())
        self.bind("<Configure>", lambda e: self._redraw())

        self._redraw()

    def get_date(self) -> dt.date:
        return self._date

    def set_date(self, new_date: dt.date, notify: bool = False) -> None:
        self._date = new_date
        self._redraw()
        if notify and self._on_select:
            self._on_select(new_date)

    def _set_hover(self, hovered: bool) -> None:
        self._is_hovered = hovered
        self._redraw()

    def _toggle_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
            return

        p = self.palette
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        pop = tk.Toplevel(self)
        pop.wm_overrideredirect(True)
        pop.configure(bg=p.bg)
        self._popup = pop

        def _picked(d: dt.date | Tuple[dt.date, Optional[dt.date]]) -> None:
            if isinstance(d, dt.date):
                self.set_date(d, notify=True)
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None

        cal = ModernCalendar(
            pop,
            selected_date=self._date,
            on_select=_picked,
            bootstyle=self._role,
        )
        cal.pack()
        pop.update_idletasks()
        pop.geometry(f"+{x}+{y}")
        pop.focus_force()
        pop.bind("<Escape>", lambda e: pop.destroy())

    def _on_theme_changed(self, _palette: ThemePalette) -> None:
        self._redraw()

    def _redraw(self) -> None:
        p = self.palette
        parent_bg = self._resolve_parent_bg()
        super().configure(bg=parent_bg)
        self.delete("all")

        w = max(self.winfo_width(), int(self["width"]))
        h = max(self.winfo_height(), int(self["height"]))

        border_col = p.role_color(self._role) if self._is_hovered else p.input_border
        fill_col = p.surface_hover if self._is_hovered else p.input_bg

        self._bg_img = create_rounded_rect_image(
            w,
            h,
            p.radius_md,
            fill_hex=fill_col,
            border_hex=border_col,
            border_width=1,
            bg_hex=parent_bg,
            bottom_border_hex=p.border_strong,
        )
        self.create_image(0, 0, image=self._bg_img, anchor="nw")

        self.create_text(
            14,
            h // 2,
            text=self._date.strftime(self._date_format),
            fill=p.input_fg,
            font=self._font,
            anchor="w",
        )
        self.create_text(
            w - 14,
            h // 2,
            text="📅",
            fill=p.role_color(self._role) if self._is_hovered else p.fg_muted,
            font=self._font,
            anchor="e",
        )

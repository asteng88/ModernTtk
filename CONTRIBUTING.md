# Contributing to ModernTtk

Thank you for your interest in contributing to **ModernTtk**! Every contribution—from bug reports and theme palettes to new supersampled widgets—is warmly welcomed.

## Getting Started

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/asteng88/ModernTtk.git
   cd ModernTtk
   ```
2. **Create a virtual environment** (Python 3.10+):
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```
3. **Install in editable mode**:
   ```bash
   pip install -e .
   ```
4. **Launch the interactive showcase** to verify everything runs:
   ```bash
   python demo.py
   ```

## Guidelines for New Widgets & Themes

- **Theme Reactivity**: Inherit from `ThemedWidgetMixin` (in `modernttk/widgets/base.py`) so widgets automatically respond to live theme switches (`mtk.set_theme(...)` / `mtk.toggle_theme()`) and unsubscribe cleanly on `<Destroy>`.
- **Anti-Aliased Rendering**: Render custom shapes/arcs/icons via Pillow (`PIL.ImageDraw`) at 2×–4× supersampling and downsample with `Image.Resampling.LANCZOS`. Always retain a strong reference to `ImageTk.PhotoImage` instances on the widget (`self._photo`) to prevent Tk garbage collection.
- **Animation Cleanup**: Cancel any `after()` callbacks in a `<Destroy>` handler and guard redraws with `self.winfo_exists()`.
- **Ergonomic API**: Support `bootstyle` semantic roles (`primary`, `secondary`, `success`, `info`, `warning`, `danger`) and export both `Modern<Name>` and short `<Name>` aliases in `modernttk/__init__.py`.
- **Showcase Coverage**: Add a live interactive preview of new widgets to `demo.py` and verify it in both dark (`fluent_dark`) and light (`fluent_light`) themes.

## Submitting a Pull Request

1. Create a feature branch from `main` (e.g. `git checkout -b feat/my-widget`).
2. Keep commits focused and descriptive.
3. Update `README.md` or `CHANGELOG.md` if adding public widgets or changing APIs.
4. Open a Pull Request describing your changes and include before/after screenshots for UI changes.

## Code of Conduct

Please note that this project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

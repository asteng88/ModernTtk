# Changelog

All notable changes to **ModernTtk** will be documented in this file.

## [0.2.0] - 2026-11-26

### Added
- **Expanded Gauge Suite** (`modernttk/widgets/gauges.py`):
  - `ModernSemiGauge` (`SemiGauge`, `ArcGauge`) — 180° executive KPI arch gauge with target marker and min/max scale.
  - `ModernSpeedometer` (`Speedometer`, `DialGauge`) — 240° instrument dial with major/minor ticks, color zones, animated needle, and digital readout pill.
  - `ModernSegmentedGauge` (`SegmentedGauge`, `LedGauge`) — discrete LED-block meter in radial `arc` and horizontal `bar` styles.
  - `ModernLinearGauge` (`LinearGauge`, `BulletGauge`) — executive bullet & scale gauge with range bands, benchmark target line, and calibrated ticks.
  - `ModernLiquidGauge` (`LiquidGauge`, `TankGauge`) — circular glass orb with 30 FPS animated dual-sine-wave liquid fill.
  - `ModernMultiRingGauge` (`MultiRingGauge`, `ActivityRings`) — concentric multi-metric activity rings with live legend.
- **Database ⇄ Computer Data Stream Animation** (`modernttk/widgets/datastream.py`):
  - `ModernDataStream` (`DataStream`, `DataTransferAnimation`) — 30 FPS 2× supersampled animation with glowing data packets streaming `db_to_pc`, `pc_to_db`, or `bidirectional`.
  - Integrated `animation="data_stream"` and `animation="auto"` (auto-switching after `long_running_threshold_sec`) into `ModernProgressDialog` and `ModernBusyOverlay`.
- **High-DPI Chronograph Timer & Uninterrupted Execution Engine** (`modernttk/widgets/timer.py`):
  - `ModernActivityTimer`, `ModernBusyOverlay`, `ModernSubprocessWorker`, and `ModernTaskRunner`.
- **6-Page Interactive Showcase** (`demo.py`) including the new **Gauges Gallery** tab and live `ModernDataStream` preview.

## [0.1.0] - 2026-10-22

### Added
- Initial release of ModernTtk with 10 built-in themes, OS dark/light detection, `auto_theme_tree`, 4× supersampled core widgets, procedural vector icon engine, and enterprise adapters (`Matplotlib`, `tksheet`).

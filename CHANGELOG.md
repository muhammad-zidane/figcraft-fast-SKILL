# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [4.0.0] - 2026-11-14

### Added
- **Auto-Launch Engine (`FigCraftClient`)**: Added `auto_launch: bool = True`, `app_path: Optional[str] = None`, `_find_figcraft_binary()`, and `_try_socket_connect()` to automatically launch FigCraft with `--control <port>` when no running instance is listening.
- **Live Streaming Mode**: Added `live_select: bool = True` and `step_delay_ms: float = 50.0` so each element renders step-by-step with live selection bounding boxes in the FigCraft GUI.
- **Height Equalization Alias**: Added `FigCraftClient.equalize_heights` as an alias for `equasize_heights`.
- **Example & Preview**: Added `examples/login_web_blue.py` (v4.0 Live Streaming showcase) and `examples/exports/01_Web_Login_Screen.png`.
- **GitHub Standards**: Added GitHub Actions CI workflow (`.github/workflows/ci.yml`), `.gitattributes`, `.github/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, and `CHANGELOG.md`.

### Changed
- **Breaking Default Update**: `FigCraftClient.__init__` now defaults to `auto_batch=False`, `live_select=True`, `step_delay_ms=50.0`, and `auto_launch=True` to match the v4.0 Live Streaming Interactive Protocol (`SKILL.md`). Pass `auto_batch=True` explicitly for atomic batch mode.
- Updated `SKILL.md` and `README.md` to v4.0 documentation.
- Updated unit tests (`scripts/test_socket_lifecycle.py`, `scripts/test_batch_reliability.py`) for v4.0 defaults and added coverage for `auto_launch` and live streaming behavior.

## [0.3.1-alpha] / [3.1] - 2026-11-08

### Added
- Hardened socket lifecycle (`_close_socket`, context manager cleanup), transport ID correlation, batch queue failure diagnostics (`last_failed_batch`, `last_error`, `last_failure_stage`), and recursive `verify_layout()` with `absoluteBounds` validation.
- Portable mock unit test suites (`test_socket_lifecycle.py`, `test_transport_reliability.py`, `test_batch_reliability.py`, `test_verify_layout.py`).
- Initial v3.1 skill documentation, design tokens, reusable UI components, smoke tests, and BerryCrumb Patisserie example.

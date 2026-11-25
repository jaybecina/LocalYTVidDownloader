# AGENTS.md

Local-only YouTube MP4 downloader. Tkinter GUI + yt-dlp. Quality: 1080p or 1440p.

## Setup

- Python 3.11 with Tk support (`python -c "import tkinter"` must work).
- **Mandatory `.venv/`.** Every package (yt-dlp, ffmpeg via `imageio-ffmpeg`, anything new) installs inside it only. Never `pip install` globally, never `brew install` app dependencies. `main.py` exits if run outside a venv.
- Only machine-level need: a Python built with Tk (see CLAUDE.md).
- Install: `.venv/bin/pip install -r requirements.txt`
- Run: `.venv/bin/python main.py`

## Layout

- `main.py` — Tkinter UI only. No download logic.
- `downloader.py` — `VideoDownloader` (yt-dlp wrapper). No UI imports.
- `tools/` — optional `ffmpeg` override. By default ffmpeg comes from `imageio-ffmpeg` inside `.venv`.
- `downloads/` — default output folder (git-ignored).

## Rules

- Output folder: user-selected folder, else `<project root>/downloads`. Create it if missing.
- Output format: MP4. Quality choices: `1080p`, `1440p`.
- Downloads run in a worker thread. Never block the Tk main loop; update the UI via `root.after`.
- Validate the URL before downloading. Show errors in a messagebox, never crash.
- Use `pathlib.Path` for all paths. No hardcoded absolute paths.
- Pin new dependencies in `requirements.txt`. Keep dependencies minimal.
- Never commit `.venv/`, `downloads/`, or media files.
- Download only content the user has the right to download.

## Style

- PEP 8, type hints on public functions, short docstrings.
- Small functions. One job each.
- Comments explain why, not what.

## Before finishing a change

- `.venv/bin/python -c "import main, downloader"` passes.
- App launches and window opens.
- Update this file if layout or rules change.

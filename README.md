# LocalYTVidDownloader

A small, local-only desktop app that saves YouTube videos as MP4 (1080p or 1440p). Tkinter GUI on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp). Nothing leaves your machine.

## Features

- Paste a link, pick **1080p** or **1440p**, click **Download MP4**
- Choose any output folder (defaults to `downloads/` in the project)
- Live progress bar, percent and status; cancel any time
- "Show in Finder" link when the download finishes
- ffmpeg is bundled through `imageio-ffmpeg`, so no system install is needed
- Downloads run in a worker thread, so the window never freezes

## Requirements

- Python 3.11 built with Tk support. Check with `python -c "import tkinter"`.
  On macOS with pyenv, install Tcl/Tk first (`brew install tcl-tk@8`), then build Python against it.

## Setup

All packages live in a project-local virtual environment. Do not install them globally.

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python main.py
```

`main.py` exits if it is not run inside a virtual environment.

## Project layout

| Path | Purpose |
|---|---|
| `main.py` | Tkinter UI only, no download logic |
| `downloader.py` | `VideoDownloader`, a yt-dlp wrapper with no UI imports |
| `tools/` | Optional `ffmpeg` binary override |
| `downloads/` | Default output folder (git-ignored) |

## Custom ffmpeg

By default ffmpeg comes from `imageio-ffmpeg`. To use your own build, drop the binary at `tools/ffmpeg`.

## Disclaimer

Only download content you own or have the right to download. Respect YouTube's Terms of Service and copyright law. You are responsible for how you use this tool.

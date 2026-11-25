@AGENTS.md

# Claude Code notes

- Reply in caveman style (short, small words) via the `caveman` skill. Code, paths and errors stay normal.
- "ponytail" plugin: not found in the plugin catalog at setup time. Use it if it becomes available.
- Python is pyenv 3.11.14 built with Tcl/Tk 8.6 (`brew install tcl-tk@8`). The older 3.11.7 lacks `_tkinter`; do not use it for the venv.
- If `.venv` breaks: `rm -rf .venv && ~/.pyenv/versions/3.11.14/bin/python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- Keep UI and download logic separate (see AGENTS.md).
- Never install project packages outside `.venv`. Use `.venv/bin/pip`. ffmpeg comes from `imageio-ffmpeg`, not brew.

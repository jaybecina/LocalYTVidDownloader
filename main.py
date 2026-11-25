import sys

# Mandatory virtualenv: refuse to run on the system/global Python.
if sys.prefix == sys.base_prefix:
    sys.exit(
        "Run this app inside the project virtualenv:\n"
        "  source .venv/bin/activate && python main.py\n"
        "or: .venv/bin/python main.py"
    )

import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse

import yt_dlp

from downloader import VideoDownloader

# Palette: cool paper, ink text, one blue accent.
PAPER = "#EEF1F4"
CARD = "#FFFFFF"
INK = "#17202A"
MUTED = "#5C6773"
LINE = "#D3D9E0"
ACCENT = "#2F6FED"
ACCENT_DARK = "#2459C4"
OK = "#1F7A52"
ERR = "#B3261E"

FONT = "Helvetica Neue"
QUALITIES = ("1080p", "1440p")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def is_youtube_url(text: str) -> bool:
    """Return True if text looks like a YouTube http(s) link."""
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in YOUTUBE_HOSTS


class YTDownloaderApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LocalYTVideoDownloader")
        self.root.geometry("680x700")
        self.root.minsize(620, 660)
        self.root.configure(bg=PAPER)

        self.project_dir = Path(__file__).resolve().parent
        self.default_download_dir = self.project_dir / "downloads"
        self.default_download_dir.mkdir(parents=True, exist_ok=True)

        # None means "use the default downloads folder"
        self.selected_folder = None
        self.downloader = VideoDownloader()
        self.busy = False
        self.cancel_event = threading.Event()

        self.url = tk.StringVar()
        self.quality = tk.StringVar(value=QUALITIES[0])
        self.folder_display = tk.StringVar(value=self._default_label())
        self.status = tk.StringVar(value="Paste a YouTube link to begin.")
        self.percent = tk.StringVar(value="0%")
        self.detail = tk.StringVar(value="")

        self._build_styles()
        self._build_interface()

    # ---------- styling ----------

    def _build_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")  # clam honors custom colors on macOS

        style.configure("TFrame", background=PAPER)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=PAPER, foreground=INK, font=(FONT, 13))
        style.configure("Card.TLabel", background=CARD, foreground=INK, font=(FONT, 13))
        style.configure("Muted.TLabel", background=PAPER, foreground=MUTED, font=(FONT, 12))
        style.configure("Title.TLabel", font=(FONT, 26, "bold"))
        style.configure("Field.TLabel", background=CARD, foreground=MUTED, font=(FONT, 12, "bold"))
        style.configure("Percent.TLabel", background=CARD, foreground=INK, font=(FONT, 34, "bold"))
        style.configure(
            "Link.TLabel", background=CARD, foreground=ACCENT, font=(FONT, 13, "underline")
        )
        style.configure("Detail.TLabel", background=CARD, foreground=MUTED, font=(FONT, 12))

        style.configure(
            "TEntry", fieldbackground=PAPER, foreground=INK,
            bordercolor=LINE, lightcolor=LINE, darkcolor=LINE, padding=8,
        )
        style.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])

        style.configure(
            "Ghost.TButton", background=CARD, foreground=INK,
            bordercolor=LINE, padding=(14, 8), font=(FONT, 12),
        )
        style.map("Ghost.TButton", background=[("active", PAPER)])

        style.configure(
            "Primary.TButton", background=ACCENT, foreground="#FFFFFF",
            bordercolor=ACCENT, padding=(14, 12), font=(FONT, 14, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", LINE), ("active", ACCENT_DARK)],
            foreground=[("disabled", MUTED)],
        )

        # Quality picker: two segments that read as a toggle
        style.configure(
            "Seg.TRadiobutton", background=CARD, foreground=INK,
            padding=(22, 8), font=(FONT, 13), indicatorsize=0,
            bordercolor=LINE, relief="solid", borderwidth=1,
        )
        style.map(
            "Seg.TRadiobutton",
            background=[("selected", ACCENT), ("active", PAPER)],
            foreground=[("selected", "#FFFFFF")],
        )

        style.configure(
            "Horizontal.TProgressbar", troughcolor=PAPER, background=ACCENT,
            bordercolor=PAPER, lightcolor=ACCENT, darkcolor=ACCENT, thickness=10,
        )

    # ---------- layout ----------

    def _build_interface(self):
        outer = ttk.Frame(self.root, padding=(32, 28))
        outer.pack(fill="both", expand=True)

        # Action bar is packed first so it is never pushed off-screen.
        bar = ttk.Frame(outer)
        bar.pack(side="bottom", fill="x", pady=(8, 0))
        self.download_btn = ttk.Button(
            bar, text="Download MP4", style="Primary.TButton", command=self.start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True)
        self.cancel_btn = ttk.Button(
            bar, text="Cancel", style="Ghost.TButton", command=self.cancel_download
        )
        self.cancel_btn.pack(side="left", padx=(10, 0), ipady=6)
        self.cancel_btn.state(["disabled"])

        ttk.Label(outer, text="Save a video to this Mac", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer, text="MP4 · runs locally · nothing leaves your machine", style="Muted.TLabel"
        ).pack(anchor="w", pady=(4, 20))

        # Inputs card
        card = ttk.Frame(outer, style="Card.TFrame", padding=22)
        card.pack(fill="x")

        ttk.Label(card, text="Video link", style="Field.TLabel").pack(anchor="w")
        self.url_entry = ttk.Entry(card, textvariable=self.url, font=(FONT, 13))
        self.url_entry.pack(fill="x", pady=(6, 18))
        self.url_entry.bind("<Return>", lambda _e: self.start_download())

        ttk.Label(card, text="Resolution", style="Field.TLabel").pack(anchor="w")
        seg = ttk.Frame(card, style="Card.TFrame")
        seg.pack(anchor="w", pady=(6, 18))
        for q in QUALITIES:
            ttk.Radiobutton(
                seg, text=q, value=q, variable=self.quality, style="Seg.TRadiobutton"
            ).pack(side="left", padx=(0, 8))

        ttk.Label(card, text="Save to", style="Field.TLabel").pack(anchor="w")
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", pady=(6, 0))
        ttk.Entry(row, textvariable=self.folder_display, state="readonly").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(row, text="Choose…", style="Ghost.TButton", command=self.select_folder).pack(
            side="left", padx=(10, 0)
        )
        ttk.Button(row, text="Reset", style="Ghost.TButton", command=self.reset_folder).pack(
            side="left", padx=(8, 0)
        )

        # Progress card: the percent readout is the one big element
        prog = ttk.Frame(outer, style="Card.TFrame", padding=22)
        prog.pack(fill="x", pady=(16, 16))

        top = ttk.Frame(prog, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, textvariable=self.percent, style="Percent.TLabel").pack(side="left")
        ttk.Label(top, textvariable=self.detail, style="Detail.TLabel").pack(side="right")

        self.progress = ttk.Progressbar(prog, maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 10))

        self.status_label = ttk.Label(prog, textvariable=self.status, style="Card.TLabel")
        self.status_label.pack(anchor="w")

        # Clickable link, shown only after a successful download.
        self.open_link = ttk.Label(
            prog, text="Show in Finder", style="Link.TLabel", cursor="pointinghand"
        )
        self.open_link.bind("<Button-1>", lambda _e: self.reveal_result())
        self.result_path = None

        self.url_entry.focus_set()

    # ---------- folder handling ----------

    def _default_label(self) -> str:
        return f"Default: {self.default_download_dir}"

    def select_folder(self):
        folder = filedialog.askdirectory(
            title="Choose download folder", initialdir=str(self.default_download_dir)
        )
        if folder:
            self.selected_folder = Path(folder)
            self.folder_display.set(str(self.selected_folder))
            self._set_status("Custom folder selected.")

    def reset_folder(self):
        self.selected_folder = None
        self.folder_display.set(self._default_label())
        self._set_status("Using the default downloads folder.")

    def get_download_directory(self) -> Path:
        destination = self.selected_folder or self.default_download_dir
        destination.mkdir(parents=True, exist_ok=True)
        return destination

    # ---------- download flow ----------

    def start_download(self):
        if self.busy:
            return

        video_url = self.url.get().strip()
        if not is_youtube_url(video_url):
            messagebox.showwarning(
                "Link not recognized",
                "Paste a full YouTube link, for example https://www.youtube.com/watch?v=…",
            )
            return

        destination = self.get_download_directory()
        self.cancel_event.clear()
        self.open_link.pack_forget()
        self._set_busy(True)
        self._set_progress(0, "Starting…", "")

        threading.Thread(
            target=self._worker,
            args=(video_url, self.quality.get(), destination),
            daemon=True,
        ).start()

    def _worker(self, video_url: str, quality: str, destination: Path):
        """Runs off the UI thread; talks to Tk only through root.after."""
        try:
            result = self.downloader.download_video(
                video_url, quality, destination, progress_hook=self._progress_hook
            )
        except yt_dlp.utils.DownloadCancelled:
            self.root.after(0, self._on_cancelled)
        except Exception as exc:  # yt-dlp raises many error types
            self.root.after(0, self._on_error, str(exc))
        else:
            self.root.after(0, self._on_done, result)

    def cancel_download(self):
        if self.busy:
            self.cancel_event.set()
            self.cancel_btn.state(["disabled"])
            self._set_status("Cancelling…")

    def _progress_hook(self, info: dict):
        if self.cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled()
        if info.get("status") == "downloading":
            total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
            done = info.get("downloaded_bytes") or 0
            pct = (done / total * 100) if total else 0
            speed = (info.get("_speed_str") or "").strip()
            eta = (info.get("_eta_str") or "").strip()
            detail = f"{speed}  ·  {eta} left" if speed and eta else speed
            self.root.after(0, self._set_progress, pct, "Downloading…", detail)
        elif info.get("status") == "finished":
            self.root.after(0, self._set_progress, 100, "Merging into MP4…", "")

    def reveal_result(self):
        """Open Finder with the downloaded file selected (or the folder)."""
        if self.result_path is None:
            return
        flag = ["-R"] if self.result_path.is_file() else []
        subprocess.run(["open", *flag, str(self.result_path)], check=False)

    def _on_done(self, result: Path):
        self.result_path = result
        self._set_progress(100, f"Saved: {result.name}", "")
        self.status_label.configure(foreground=OK)
        self.open_link.pack(anchor="w", pady=(8, 0))
        self._set_busy(False)

    def _on_cancelled(self):
        self._set_progress(0, "Download cancelled.", "")
        self._set_busy(False)

    def _on_error(self, message: str):
        self._set_progress(0, "Download failed. Check the link, your connection and ffmpeg.", "")
        self.status_label.configure(foreground=ERR)
        self._set_busy(False)
        messagebox.showerror("Download failed", message)

    # ---------- ui helpers ----------

    def _set_busy(self, busy: bool):
        self.busy = busy
        self.download_btn.state(["disabled"] if busy else ["!disabled"])
        self.download_btn.configure(text="Downloading…" if busy else "Download MP4")
        self.cancel_btn.state(["!disabled"] if busy else ["disabled"])

    def _set_status(self, text: str):
        self.status.set(text)
        self.status_label.configure(foreground=INK)

    def _set_progress(self, pct: float, status: str, detail: str):
        self.progress["value"] = pct
        self.percent.set(f"{pct:.0f}%")
        self.detail.set(detail)
        self._set_status(status)


def main():
    root = tk.Tk()
    YTDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

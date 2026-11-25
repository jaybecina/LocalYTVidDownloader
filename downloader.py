
import imageio_ffmpeg
import yt_dlp
from pathlib import Path


class VideoDownloader:

    def __init__(self):

        self.project_dir = Path(__file__).resolve().parent

        self.tools_dir = self.project_dir / "tools"

        self.ffmpeg_path = self.tools_dir / "ffmpeg"

    def download_video(self, url, quality, output_folder, progress_hook=None) -> Path:

        output_folder = Path(output_folder)

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        height = int(quality.replace("p", ""))

        # Prefer native MP4/M4A; fall back to any codec (1440p is usually
        # VP9/AV1) and let ffmpeg merge into MP4.
        format_selector = (
            f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/"
            f"bv*[height<={height}]+ba/"
            f"b[height<={height}]"
        )

        options = {
            "format": format_selector,
            "merge_output_format": "mp4",
            "outtmpl": str(
                output_folder / "%(title).180B [%(id)s].%(ext)s"
            ),
            "noplaylist": True,
            "progress_hooks": [progress_hook] if progress_hook else [],
        }

        # ffmpeg ships inside .venv (imageio-ffmpeg); tools/ffmpeg overrides it.
        if self.ffmpeg_path.exists():
            options["ffmpeg_location"] = str(self.ffmpeg_path)
        else:
            options["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

        # Final merged file path (falls back to the output folder).
        downloads = info.get("requested_downloads") or []
        if downloads and downloads[0].get("filepath"):
            return Path(downloads[0]["filepath"])
        return output_folder

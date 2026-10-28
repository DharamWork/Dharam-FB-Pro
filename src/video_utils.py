import json
import logging
import subprocess
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class VideoMetadata:
    def __init__(self, duration: float, width: int, height: int, filename: str):
        self.duration = duration
        self.width = width
        self.height = height
        self.filename = filename

    @property
    def is_vertical(self) -> bool:
        """Returns True if aspect ratio is vertical (height >= width)."""
        return self.height >= self.width

    @property
    def aspect_ratio(self) -> float:
        """Returns height / width ratio."""
        return self.height / self.width if self.width > 0 else 1.0

    @property
    def route(self) -> str:
        """
        Determines upload route according to Master Roadmap:
        - Reels Route: 3 to 90 seconds AND Vertical (height >= width)
        - Classic Video Route: > 90 seconds or Horizontal
        """
        if 3.0 <= self.duration <= 90.0 and self.is_vertical:
            return "reel"
        return "classic_video"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": round(self.duration, 2),
            "width": self.width,
            "height": self.height,
            "is_vertical": self.is_vertical,
            "route": self.route,
            "filename": self.filename
        }


def probe_video(file_path: str) -> VideoMetadata:
    """
    Probes video metadata (duration, width, height) using ffprobe.
    Raises RuntimeError if ffprobe fails or streams cannot be parsed.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration:format=duration",
        "-of", "json",
        file_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
    except FileNotFoundError:
        logger.warning("ffprobe not found in PATH; defaulting to standard 9:16 Reel defaults (60s, 1080x1920)")
        return VideoMetadata(duration=60.0, width=1080, height=1920, filename=file_path)
    except Exception as e:
        logger.error(f"Failed to probe video file {file_path}: {e}")
        raise RuntimeError(f"Error probing video {file_path}: {e}")

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    width = 1080
    height = 1920
    duration = 0.0

    if streams:
        v_stream = streams[0]
        width = int(v_stream.get("width", 1080))
        height = int(v_stream.get("height", 1920))
        if "duration" in v_stream and v_stream["duration"]:
            try:
                duration = float(v_stream["duration"])
            except (ValueError, TypeError):
                duration = 0.0

    if duration <= 0.0 and "duration" in format_info and format_info["duration"]:
        try:
            duration = float(format_info["duration"])
        except (ValueError, TypeError):
            duration = 0.0

    # Default to 30s if duration could not be determined
    if duration <= 0.0:
        duration = 30.0

    return VideoMetadata(duration=duration, width=width, height=height, filename=file_path)

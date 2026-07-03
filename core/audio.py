"""Tách âm thanh MP3 từ video bằng ffmpeg (binary đóng gói qua imageio-ffmpeg).

Không cần cài ffmpeg thủ công: imageio-ffmpeg mang sẵn binary cho Windows/macOS/Linux.
Các preset tối ưu cho bài NÓI (giọng người), không phải nhạc — nên mono là đủ trong.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"


@dataclass(frozen=True)
class Mp3Preset:
    """Một cấu hình xuất MP3."""

    key: str
    label: str
    bitrate: str  # VD "128k"
    channels: int  # 1 = mono, 2 = stereo
    sample_rate: int  # Hz


# Preset tối ưu cho giọng nói: mono cắt nửa dung lượng mà không mất độ rõ.
MP3_PRESETS: dict[str, Mp3Preset] = {
    "compact": Mp3Preset("compact", "Nhỏ gọn (giọng nói, mono 64k)", "64k", 1, 22050),
    "balanced": Mp3Preset("balanced", "Cân bằng (mono 128k)", "128k", 1, 44100),
    "high": Mp3Preset("high", "Chất lượng cao (stereo 192k)", "192k", 2, 44100),
}
DEFAULT_MP3_PRESET = "balanced"


class AudioError(RuntimeError):
    """Lỗi khi tách âm thanh từ video."""


def extract_mp3(
    video_path: str | Path,
    *,
    preset: str = DEFAULT_MP3_PRESET,
    out_dir: str | Path = EXPORT_DIR,
) -> Path:
    """Tách MP3 từ video theo preset. Trả về đường dẫn file MP3 đã tạo."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise AudioError(f"Không tìm thấy file video: {video_path}")

    cfg = MP3_PRESETS.get(preset) or MP3_PRESETS[DEFAULT_MP3_PRESET]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{video_path.stem}_{cfg.key}.mp3"

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
        "-vn",  # bỏ hình, chỉ lấy tiếng
        "-acodec", "libmp3lame",
        "-b:a", cfg.bitrate,
        "-ac", str(cfg.channels),
        "-ar", str(cfg.sample_rate),
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.exists():
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise AudioError("Tách âm thanh thất bại: " + " | ".join(tail))
    return out_path

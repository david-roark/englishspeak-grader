"""Nén video bằng ffmpeg (binary đóng gói qua imageio-ffmpeg).

Giảm dung lượng video trước khi gửi lên Gemini để tiết kiệm băng thông và chi phí.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"


@dataclass(frozen=True)
class VideoPreset:
    """Cấu hình nén video."""

    key: str
    label: str
    preset: str
    audio_bitrate: str
    crf: int | None = None
    video_bitrate: str | None = None
    scale: str | None = None


VIDEO_PRESETS: dict[str, VideoPreset] = {
    "tiny": VideoPreset("tiny", "Siêu tiết kiệm (540p, file cực nhẹ)", "slow", "48k", video_bitrate="900k", scale="-2:540"),
    "light": VideoPreset("light", "Siêu nhẹ (CRF 28, preset fast)", "fast", "96k", crf=28),
    "balanced": VideoPreset("balanced", "Cân bằng (CRF 26, preset medium)", "medium", "96k", crf=26),
    "high": VideoPreset("high", "Chất lượng cao (CRF 23, preset slow)", "slow", "128k", crf=23),
}
DEFAULT_VIDEO_PRESET = "balanced"


class VideoError(RuntimeError):
    """Lỗi khi nén video."""


def compress_video(
    video_path: str | Path,
    *,
    preset: str = DEFAULT_VIDEO_PRESET,
    out_dir: str | Path = EXPORT_DIR,
) -> Path:
    """Nén video bằng ffmpeg. Trả về đường dẫn file video đã nén."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise VideoError(f"Không tìm thấy file video: {video_path}")

    cfg = VIDEO_PRESETS.get(preset) or VIDEO_PRESETS[DEFAULT_VIDEO_PRESET]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # File nén sẽ có đuôi _compressed_xxx.mp4
    out_path = out_dir / f"{video_path.stem}_compressed_{cfg.key}.mp4"

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    # Lệnh ffmpeg để nén
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
    ]

    # Bộ lọc scale nếu có
    if cfg.scale is not None:
        cmd.extend(["-vf", f"scale={cfg.scale}"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", cfg.preset,
    ])

    if cfg.crf is not None:
        cmd.extend(["-crf", str(cfg.crf)])
    if cfg.video_bitrate is not None:
        cmd.extend(["-b:v", cfg.video_bitrate])

    cmd.extend([
        "-c:a", "aac",
        "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
        str(out_path),
    ])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.exists():
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise VideoError("Nén video thất bại: " + " | ".join(tail))

    return out_path

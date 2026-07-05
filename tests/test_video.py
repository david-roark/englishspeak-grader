"""Test core/video: preset, dựng lệnh ffmpeg nén video.

Không chạy ffmpeg thật: giả lập subprocess.run để kiểm lệnh được dựng đúng
và các nhánh lỗi được xử lý.
"""

from __future__ import annotations

import subprocess
import types

import pytest

from core import video
from core.video import (
    DEFAULT_VIDEO_PRESET,
    VIDEO_PRESETS,
    VideoError,
    compress_video,
)


def test_preset_mặc_định_hợp_lệ():
    assert DEFAULT_VIDEO_PRESET in VIDEO_PRESETS


def test_compress_video_không_tồn_tại():
    with pytest.raises(VideoError, match="Không tìm thấy"):
        compress_video("/khong/co/that.mp4")


def _fake_run_factory(returncode: int, make_output: bool):
    """Trả về hàm thay subprocess.run; tùy chọn tạo file output để mô phỏng ffmpeg."""
    captured = {}

    def _fake_run(cmd, capture_output=True, text=True):
        captured["cmd"] = cmd
        if make_output:
            # cmd[-1] là đường dẫn output -> tạo file rỗng để qua kiểm tra exists().
            open(cmd[-1], "wb").close()
        return types.SimpleNamespace(returncode=returncode, stderr="lỗi giả\ndòng 2")

    return _fake_run, captured


def test_compress_video_dựng_lệnh_đúng(tmp_path, monkeypatch):
    video_file = tmp_path / "bai.mp4"
    video_file.write_bytes(b"fake")
    fake_run, captured = _fake_run_factory(0, make_output=True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(video.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    out = compress_video(video_file, preset="light", out_dir=tmp_path)

    cmd = captured["cmd"]
    cfg = VIDEO_PRESETS["light"]
    assert cmd[0] == "/fake/ffmpeg"
    assert "-c:v" in cmd
    assert "libx264" in cmd
    assert "-preset" in cmd
    assert cfg.preset in cmd
    assert "-crf" in cmd
    assert str(cfg.crf) in cmd
    assert "-c:a" in cmd
    assert "aac" in cmd
    assert "-b:a" in cmd
    assert cfg.audio_bitrate in cmd
    assert "-movflags" in cmd
    assert "+faststart" in cmd
    assert out.name == f"bai_compressed_{cfg.key}.mp4"


def test_compress_video_preset_sai_fallback_balanced(tmp_path, monkeypatch):
    video_file = tmp_path / "bai.mp4"
    video_file.write_bytes(b"fake")
    fake_run, captured = _fake_run_factory(0, make_output=True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(video.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    out = compress_video(video_file, preset="khong_ton_tai", out_dir=tmp_path)
    assert out.name == f"bai_compressed_{DEFAULT_VIDEO_PRESET}.mp4"


def test_compress_video_ffmpeg_lỗi_raise(tmp_path, monkeypatch):
    video_file = tmp_path / "bai.mp4"
    video_file.write_bytes(b"fake")
    fake_run, _ = _fake_run_factory(1, make_output=False)  # returncode != 0
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(video.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    with pytest.raises(VideoError, match="Nén video thất bại"):
        compress_video(video_file, out_dir=tmp_path)


def test_compress_video_preset_tiny_dựng_lệnh_đúng(tmp_path, monkeypatch):
    video_file = tmp_path / "bai.mp4"
    video_file.write_bytes(b"fake")
    fake_run, captured = _fake_run_factory(0, make_output=True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(video.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    out = compress_video(video_file, preset="tiny", out_dir=tmp_path)

    cmd = captured["cmd"]
    cfg = VIDEO_PRESETS["tiny"]
    assert cmd[0] == "/fake/ffmpeg"
    assert "-vf" in cmd
    assert f"scale={cfg.scale}" in cmd
    assert "-b:v" in cmd
    assert cfg.video_bitrate in cmd
    assert "-preset" in cmd
    assert cfg.preset in cmd
    assert "-c:a" in cmd
    assert "aac" in cmd
    assert "-b:a" in cmd
    assert cfg.audio_bitrate in cmd
    assert out.name == f"bai_compressed_{cfg.key}.mp4"

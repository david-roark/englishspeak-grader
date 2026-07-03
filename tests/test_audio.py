"""Test core/audio: guard file, preset, dựng lệnh ffmpeg.

Không chạy ffmpeg thật: giả lập subprocess.run để kiểm lệnh được dựng đúng
và nhánh lỗi được xử lý.
"""

from __future__ import annotations

import subprocess
import types

import pytest

from core import audio
from core.audio import (
    DEFAULT_MP3_PRESET,
    MP3_PRESETS,
    AudioError,
    extract_mp3,
)


# --- preset --------------------------------------------------------------- #

def test_preset_mặc_định_hợp_lệ():
    assert DEFAULT_MP3_PRESET in MP3_PRESETS


def test_preset_giọng_nói_là_mono():
    # compact & balanced tối ưu cho giọng nói -> mono (1 kênh).
    assert MP3_PRESETS["compact"].channels == 1
    assert MP3_PRESETS["balanced"].channels == 1
    assert MP3_PRESETS["high"].channels == 2


# --- guard ---------------------------------------------------------------- #

def test_extract_mp3_video_không_tồn_tại():
    with pytest.raises(AudioError, match="Không tìm thấy"):
        extract_mp3("/khong/co/that.mp4")


# --- dựng lệnh + nhánh kết quả (giả lập subprocess) ---------------------- #

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


def test_extract_mp3_dựng_lệnh_đúng(tmp_path, monkeypatch):
    video = tmp_path / "bai.mp4"
    video.write_bytes(b"fake")
    fake_run, captured = _fake_run_factory(0, make_output=True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(audio.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    out = extract_mp3(video, preset="compact", out_dir=tmp_path)

    cmd = captured["cmd"]
    cfg = MP3_PRESETS["compact"]
    assert cmd[0] == "/fake/ffmpeg"
    assert "-vn" in cmd                       # bỏ hình
    assert cfg.bitrate in cmd                 # bitrate đúng preset
    assert str(cfg.channels) in cmd           # số kênh
    assert out.name == "bai_compact.mp3"


def test_extract_mp3_preset_sai_fallback_balanced(tmp_path, monkeypatch):
    video = tmp_path / "bai.mp4"
    video.write_bytes(b"fake")
    fake_run, captured = _fake_run_factory(0, make_output=True)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(audio.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    out = extract_mp3(video, preset="khong_ton_tai", out_dir=tmp_path)
    assert out.name == "bai_balanced.mp3"     # fallback về DEFAULT_MP3_PRESET


def test_extract_mp3_ffmpeg_lỗi_raise(tmp_path, monkeypatch):
    video = tmp_path / "bai.mp4"
    video.write_bytes(b"fake")
    fake_run, _ = _fake_run_factory(1, make_output=False)  # returncode != 0
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(audio.imageio_ffmpeg, "get_ffmpeg_exe", lambda: "/fake/ffmpeg")

    with pytest.raises(AudioError, match="Tách âm thanh thất bại"):
        extract_mp3(video, out_dir=tmp_path)

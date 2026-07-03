"""Test app.get_or_upload: logic tái dùng video đã upload (cache).

Không gọi mạng: giả lập upload_video / cleanup_file và client.files.get.
Đây là logic dễ sinh bug (dùng lại nhầm / không dọn file cũ / bỏ qua TTL).
"""

from __future__ import annotations

import time
import types

import app
from app import _UPLOAD_TTL_SECONDS, get_or_upload


def _noop_progress(*args, **kwargs):
    return None


class _Uploaded:
    def __init__(self, name):
        self.name = name


class _FilesActive:
    """client.files.get trả file ACTIVE."""
    def get(self, name):
        return types.SimpleNamespace(name=name, state=types.SimpleNamespace(name="ACTIVE"))


class _FilesDead:
    """client.files.get ném lỗi (file hết hạn / không còn)."""
    def get(self, name):
        raise RuntimeError("404 not found")


class _Client:
    def __init__(self, files):
        self.files = files


def _patch_upload(monkeypatch):
    """Thay upload_video bằng bản giả, ghi lại số lần gọi."""
    calls = {"upload": 0, "cleanup": []}

    def fake_upload(client, video_path, on_progress=None):
        calls["upload"] += 1
        return _Uploaded(f"files/new-{video_path}")

    def fake_cleanup(client, uploaded):
        calls["cleanup"].append(uploaded.name)

    monkeypatch.setattr(app, "upload_video", fake_upload)
    monkeypatch.setattr(app, "cleanup_file", fake_cleanup)
    return calls


def test_cache_hit_dùng_lại_không_upload(monkeypatch):
    calls = _patch_upload(monkeypatch)
    cache = {"video_path": "a.mp4", "uploaded": _Uploaded("files/old"), "ts": time.time()}
    client = _Client(_FilesActive())

    result, new_cache = get_or_upload(client, "a.mp4", cache, _noop_progress)

    assert calls["upload"] == 0                 # KHÔNG upload lại
    assert new_cache["video_path"] == "a.mp4"
    assert result.name == "files/old"           # dùng lại file cũ (fresh)


def test_cache_miss_video_khác_dọn_cũ_rồi_upload(monkeypatch):
    calls = _patch_upload(monkeypatch)
    cache = {"video_path": "a.mp4", "uploaded": _Uploaded("files/old"), "ts": time.time()}
    client = _Client(_FilesActive())

    _, new_cache = get_or_upload(client, "b.mp4", cache, _noop_progress)

    assert calls["upload"] == 1                  # upload video mới
    assert calls["cleanup"] == ["files/old"]     # đã dọn file cũ
    assert new_cache["video_path"] == "b.mp4"


def test_cache_hết_hạn_upload_lại(monkeypatch):
    calls = _patch_upload(monkeypatch)
    old_ts = time.time() - _UPLOAD_TTL_SECONDS - 10   # quá hạn TTL
    cache = {"video_path": "a.mp4", "uploaded": _Uploaded("files/old"), "ts": old_ts}
    client = _Client(_FilesActive())

    _, new_cache = get_or_upload(client, "a.mp4", cache, _noop_progress)

    assert calls["upload"] == 1                  # hết hạn -> upload lại
    assert new_cache["ts"] > old_ts


def test_cache_file_chết_trên_gemini_upload_lại(monkeypatch):
    calls = _patch_upload(monkeypatch)
    cache = {"video_path": "a.mp4", "uploaded": _Uploaded("files/old"), "ts": time.time()}
    client = _Client(_FilesDead())              # files.get ném lỗi

    _, _ = get_or_upload(client, "a.mp4", cache, _noop_progress)

    assert calls["upload"] == 1                  # file chết -> upload lại


def test_không_có_cache_thì_upload(monkeypatch):
    calls = _patch_upload(monkeypatch)
    client = _Client(_FilesActive())

    _, new_cache = get_or_upload(client, "a.mp4", None, _noop_progress)

    assert calls["upload"] == 1
    assert new_cache["video_path"] == "a.mp4"

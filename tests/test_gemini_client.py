"""Test core/gemini_client: lọc/xếp model, guard client, JSON fallback.

Không gọi mạng: dùng fake client giả lập cho list_models và grade_video.
"""

from __future__ import annotations

import pytest

from core import gemini_client as gc
from core.gemini_client import (
    FALLBACK_MODELS,
    GeminiError,
    _is_gradable_model,
    _rank_model,
    grade_video,
    list_models,
    make_client,
)
from core.rubrics import DEFAULT_RUBRICS
from core.schemas import AssessmentResult

RUBRIC = DEFAULT_RUBRICS["ielts_speaking"]


# --- _is_gradable_model --------------------------------------------------- #

@pytest.mark.parametrize("mid", [
    "gemini-flash-latest", "gemini-2.5-pro", "models/gemini-2.5-flash",
    "gemini-flash-lite-latest",
])
def test_model_hợp_lệ_được_nhận(mid):
    assert _is_gradable_model(mid) is True


@pytest.mark.parametrize("mid", [
    "gemini-2.5-flash-tts",       # tts
    "gemini-live-2.5-flash",      # live
    "gemini-2.0-flash-image",     # sinh ảnh
    "text-embedding-004",         # embedding, không phải gemini
    "gemma-2-9b",                 # gemma text-only
    "veo-2",                      # video-gen
    "gemini-robotics-er",         # robotics
    "gemini-2.0-flash-nano-banana",
])
def test_model_không_hợp_lệ_bị_loại(mid):
    assert _is_gradable_model(mid) is False


def test_model_gemini_không_flash_không_pro_bị_loại():
    # Dòng gemini nhưng không phải flash/pro (vd bản base) -> loại.
    assert _is_gradable_model("gemini-1.0-ultra") is False


# --- _rank_model ---------------------------------------------------------- #

def test_rank_ưu_tiên_flash_lite_rồi_flash_rồi_pro():
    ids = ["gemini-2.5-pro", "gemini-flash-latest", "gemini-flash-lite-latest"]
    assert sorted(ids, key=_rank_model) == [
        "gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.5-pro",
    ]


# --- make_client ---------------------------------------------------------- #

def test_make_client_key_rỗng_báo_lỗi(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(GeminiError):
        make_client("")


def test_make_client_key_placeholder_báo_lỗi():
    with pytest.raises(GeminiError):
        make_client("dan_key_cua_ban_vao_day")


# --- list_models (fake client) ------------------------------------------- #

class _FakeModel:
    def __init__(self, name, actions=None):
        self.name = name
        self.supported_actions = actions


class _FakeModels:
    def __init__(self, models):
        self._models = models

    def list(self):
        return self._models


class _FakeClient:
    def __init__(self, models):
        self.models = _FakeModels(models)


def test_list_models_lọc_và_xếp():
    client = _FakeClient([
        _FakeModel("models/gemini-2.5-pro", ["generateContent"]),
        _FakeModel("models/gemini-flash-lite-latest", ["generateContent"]),
        _FakeModel("models/gemini-2.5-flash-tts", ["generateContent"]),  # bị loại
        _FakeModel("models/text-embedding-004", ["embedContent"]),        # bị loại
    ])
    result = list_models(client)
    assert result == ["gemini-flash-lite-latest", "gemini-2.5-pro"]


def test_list_models_rỗng_trả_fallback():
    client = _FakeClient([_FakeModel("models/text-embedding-004", ["embedContent"])])
    assert list_models(client) == list(FALLBACK_MODELS)


def test_list_models_lỗi_trả_fallback():
    class _Boom:
        @property
        def models(self):
            raise RuntimeError("offline")
    assert list_models(_Boom()) == list(FALLBACK_MODELS)


# --- grade_video (fake client, không mạng) ------------------------------- #

class _Resp:
    def __init__(self, parsed=None, text=""):
        self.parsed = parsed
        self.text = text


class _GenModels:
    def __init__(self, resp):
        self._resp = resp

    def generate_content(self, **kwargs):
        if isinstance(self._resp, Exception):
            raise self._resp
        return self._resp


class _GenClient:
    def __init__(self, resp):
        self.models = _GenModels(resp)


def _valid_result_json() -> str:
    return AssessmentResult(
        task_summary="x", detected_language="English", students=[],
    ).model_dump_json()


def test_grade_video_trả_parsed_trực_tiếp(sample_result):
    client = _GenClient(_Resp(parsed=sample_result))
    out = grade_video(client, object(), RUBRIC)
    assert out is sample_result


def test_grade_video_fallback_parse_json():
    client = _GenClient(_Resp(parsed=None, text=_valid_result_json()))
    out = grade_video(client, object(), RUBRIC)
    assert isinstance(out, AssessmentResult)
    assert out.detected_language == "English"


def test_grade_video_text_rỗng_báo_lỗi():
    client = _GenClient(_Resp(parsed=None, text="  "))
    with pytest.raises(GeminiError):
        grade_video(client, object(), RUBRIC)


def test_grade_video_json_hỏng_báo_lỗi():
    client = _GenClient(_Resp(parsed=None, text="{not json}"))
    with pytest.raises(GeminiError):
        grade_video(client, object(), RUBRIC)


def test_grade_video_api_ném_lỗi_được_gói_lại():
    client = _GenClient(RuntimeError("429 quota"))
    with pytest.raises(GeminiError):
        grade_video(client, object(), RUBRIC)

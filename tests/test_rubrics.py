"""Test cấu trúc rubric mặc định + chuyển đổi dict."""

from __future__ import annotations

from core.rubrics import (
    DEFAULT_RUBRICS,
    Criterion,
    Rubric,
    get_default_rubric,
    rubric_from_dict,
)


def test_max_total_là_tổng_max_score():
    r = Rubric(
        key="k", name="n", description="d",
        criteria=[Criterion("a", "", 0, 5), Criterion("b", "", 0, 10)],
    )
    assert r.max_total == 15


def test_max_total_rubric_rỗng_bằng_0():
    assert Rubric(key="k", name="n", description="d").max_total == 0


def test_default_rubrics_có_đủ_5_bộ():
    assert set(DEFAULT_RUBRICS) == {
        "ielts_speaking", "cefr", "cambridge_school", "toefl_speaking", "classroom_10"
    }


def test_get_default_rubric():
    assert get_default_rubric("ielts_speaking").name == "IELTS Speaking"
    assert get_default_rubric("khong_ton_tai") is None


def test_to_prompt_block_chứa_tên_và_tiêu_chí():
    block = DEFAULT_RUBRICS["ielts_speaking"].to_prompt_block()
    assert "IELTS Speaking" in block
    assert "Fluency and Coherence" in block
    assert "Tổng điểm tối đa: 36" in block  # 4 tiêu chí x 9


def test_rubric_from_dict_roundtrip():
    data = {
        "key": "custom", "name": "Của tôi", "description": "mô tả",
        "scale_note": "0-10",
        "criteria": [
            {"name": "Ý", "description": "nội dung", "min_score": 0, "max_score": 10},
            {"name": "Từ", "max_score": 5},  # thiếu min_score/description -> mặc định
        ],
    }
    r = rubric_from_dict(data)
    assert r.key == "custom"
    assert len(r.criteria) == 2
    assert r.criteria[1].min_score == 0.0
    assert r.criteria[1].description == ""
    assert r.max_total == 15

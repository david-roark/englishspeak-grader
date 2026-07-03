"""Test dựng prompt gửi Gemini."""

from __future__ import annotations

from core.prompts import build_grading_prompt
from core.rubrics import DEFAULT_RUBRICS

RUBRIC = DEFAULT_RUBRICS["ielts_speaking"]


def test_prompt_nhúng_rubric_và_loại_bài():
    p = build_grading_prompt(RUBRIC, task_type="presentation")
    assert "IELTS Speaking" in p
    assert "thuyết trình cá nhân" in p.lower()


def test_prompt_có_tên_học_sinh_khi_được_cung_cấp():
    p = build_grading_prompt(RUBRIC, student_names=["An", "Bình"])
    assert "An, Bình" in p
    assert "gán kết quả theo đúng các tên này" in p


def test_prompt_không_có_tên_hướng_dẫn_tự_lấy():
    p = build_grading_prompt(RUBRIC, student_names=None)
    assert "KHÔNG cung cấp tên" in p
    assert "name_confident=false" in p


def test_prompt_ngôn_ngữ_nhận_xét():
    assert "TIẾNG VIỆT" in build_grading_prompt(RUBRIC, feedback_language="vi")
    assert "ENGLISH" in build_grading_prompt(RUBRIC, feedback_language="en")
    assert "SONG NGỮ" in build_grading_prompt(RUBRIC, feedback_language="bilingual")


def test_prompt_yêu_cầu_bổ_sung():
    p = build_grading_prompt(RUBRIC, extra_instructions="Chú trọng phát âm")
    assert "YÊU CẦU BỔ SUNG" in p
    assert "Chú trọng phát âm" in p


def test_prompt_bỏ_qua_yêu_cầu_bổ_sung_rỗng():
    p = build_grading_prompt(RUBRIC, extra_instructions="   ")
    assert "YÊU CẦU BỔ SUNG" not in p


def test_prompt_loại_bài_không_hợp_lệ_fallback_other():
    from core.prompts import TASK_TYPES
    p = build_grading_prompt(RUBRIC, task_type="khong_ton_tai")
    assert TASK_TYPES["other"] in p  # so trực tiếp với hằng số, tránh lệch unicode

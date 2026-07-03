"""Test lớp lưu trữ SQLite: rubric tùy chỉnh + kết quả chấm."""

from __future__ import annotations

from core import database as db
from core.rubrics import Criterion, Rubric


def _make_rubric(key="my_rubric") -> Rubric:
    return Rubric(
        key=key, name="Rubric Của Tôi", description="mô tả", scale_note="0-10",
        criteria=[Criterion("Nội dung", "ý tưởng", 0, 10), Criterion("Phát âm", "rõ", 0, 10)],
    )


# --- Rubric tùy chỉnh ----------------------------------------------------- #

def test_save_và_list_custom_rubric():
    db.save_custom_rubric(_make_rubric())
    rows = db.list_custom_rubrics()
    assert len(rows) == 1
    r = rows[0]
    assert r["key"] == "my_rubric"
    assert r["name"] == "Rubric Của Tôi"
    assert len(r["criteria"]) == 2
    assert r["criteria"][0]["max_score"] == 10


def test_save_custom_rubric_upsert_ghi_đè():
    db.save_custom_rubric(_make_rubric())
    updated = Rubric(key="my_rubric", name="Tên Mới", description="", criteria=[Criterion("X", "", 0, 5)])
    db.save_custom_rubric(updated)
    rows = db.list_custom_rubrics()
    assert len(rows) == 1  # vẫn 1 bản, không nhân đôi
    assert rows[0]["name"] == "Tên Mới"
    assert len(rows[0]["criteria"]) == 1


def test_delete_custom_rubric():
    db.save_custom_rubric(_make_rubric())
    db.delete_custom_rubric("my_rubric")
    assert db.list_custom_rubrics() == []


# --- Kết quả chấm --------------------------------------------------------- #

def test_save_và_get_assessment_roundtrip(sample_result):
    aid = db.save_assessment(
        sample_result, video_name="bai1.mp4", rubric_key="ielts_speaking",
        rubric_name="IELTS Speaking", task_type="presentation",
        model="gemini-flash", feedback_lang="vi",
    )
    assert aid > 0
    data = db.get_assessment(aid)
    assert data is not None
    assert data["video_name"] == "bai1.mp4"
    assert data["task_summary"] == sample_result.task_summary
    # result_json được dựng lại thành AssessmentResult
    assert data["result"].students[0].student_name == "An"
    assert len(data["result"].students) == 2


def test_get_assessment_không_tồn_tại_trả_None():
    assert db.get_assessment(99999) is None


def test_list_assessments_mới_nhất_trước(sample_result):
    a1 = db.save_assessment(sample_result, video_name="v1", rubric_key="k",
                            rubric_name="R", task_type="t", model="m", feedback_lang="vi")
    a2 = db.save_assessment(sample_result, video_name="v2", rubric_key="k",
                            rubric_name="R", task_type="t", model="m", feedback_lang="vi")
    rows = db.list_assessments()
    assert [r["id"] for r in rows] == [a2, a1]  # DESC theo id

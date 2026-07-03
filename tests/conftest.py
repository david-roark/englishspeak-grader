"""Fixtures dùng chung cho test.

Cách ly DB: mỗi test dùng một file SQLite riêng trong thư mục tạm (không đụng
tới data/app.db thật). Ta vá `core.database.DB_PATH` — vì `_connect()` đọc biến
này lúc gọi nên chỉ cần đổi hằng số là đủ.
"""

from __future__ import annotations

import pytest

from core import database as db
from core.schemas import (
    AssessmentResult,
    CriterionScore,
    Evidence,
    StudentAssessment,
)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Trỏ DB sang file tạm và khởi tạo bảng cho từng test."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    yield


@pytest.fixture
def sample_result() -> AssessmentResult:
    """Một kết quả chấm mẫu, đủ 2 học sinh + dẫn chứng để test export/DB."""
    return AssessmentResult(
        task_summary="Hai học sinh thuyết trình về sở thích.",
        detected_language="English",
        general_notes="Cả lớp tiến bộ tốt.",
        students=[
            StudentAssessment(
                student_name="An",
                name_confident=True,
                criteria=[
                    CriterionScore(criterion="Fluency", score=6.5, max_score=9, comment="Trôi chảy."),
                    CriterionScore(criterion="Pronunciation", score=6.0, max_score=9, comment="Rõ ràng."),
                ],
                total_score=6.5,
                max_total_score=9,
                overall_level="Band 6.5",
                strengths=["Nói tự tin"],
                weaknesses=["Còn ngập ngừng"],
                improvement_suggestions=["Luyện nói theo chủ đề"],
                practice_directions=["Shadowing 10 phút/ngày"],
                evidence=[Evidence(timestamp="00:12", quote="I love reading", note="Câu mở đầu tốt")],
            ),
            StudentAssessment(
                student_name="Học sinh 2",
                name_confident=False,
                criteria=[
                    CriterionScore(criterion="Fluency", score=5.0, max_score=9, comment="Tạm ổn."),
                ],
                total_score=5.0,
                max_total_score=9,
                overall_level="Band 5.0",
                strengths=[],
                weaknesses=["Vốn từ hạn chế"],
                improvement_suggestions=[],
                practice_directions=[],
                evidence=[],
            ),
        ],
    )

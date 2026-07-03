"""Định nghĩa cấu trúc kết quả chấm điểm (Pydantic).

Các schema này được truyền cho Gemini qua `response_schema` để model trả về
JSON có cấu trúc chặt chẽ, thay vì phải parse văn bản tự do.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    """Điểm cho một tiêu chí trong rubric."""

    criterion: str = Field(description="Tên tiêu chí, đúng như trong rubric.")
    score: float = Field(description="Điểm số đạt được cho tiêu chí này.")
    max_score: float = Field(description="Điểm tối đa của tiêu chí này.")
    comment: str = Field(description="Nhận xét ngắn gọn lý do cho điểm này.")


class Evidence(BaseModel):
    """Dẫn chứng cụ thể trích từ video kèm mốc thời gian."""

    timestamp: str = Field(
        description="Mốc thời gian trong video, định dạng MM:SS hoặc HH:MM:SS."
    )
    quote: str = Field(description="Trích dẫn hoặc mô tả điều học sinh nói/làm.")
    note: str = Field(description="Vì sao dẫn chứng này đáng chú ý (tốt hoặc cần sửa).")


class StudentAssessment(BaseModel):
    """Kết quả đánh giá cho MỘT học sinh."""

    student_name: str = Field(
        description=(
            "Tên học sinh nếu nghe được trong phần tự giới thiệu. "
            "Nếu không xác định được tên, dùng nhãn như 'Học sinh 1', 'Học sinh 2'."
        )
    )
    name_confident: bool = Field(
        description="True nếu tên lấy trực tiếp từ lời giới thiệu trong video; False nếu chỉ là nhãn tạm."
    )
    criteria: list[CriterionScore] = Field(description="Điểm theo từng tiêu chí của rubric.")
    total_score: float = Field(description="Tổng điểm.")
    max_total_score: float = Field(description="Tổng điểm tối đa có thể đạt.")
    overall_level: str = Field(
        description="Xếp loại/mức tổng quát (vd: band 6.5, mức B1, Khá...) phù hợp rubric."
    )
    strengths: list[str] = Field(description="Danh sách điểm mạnh.")
    weaknesses: list[str] = Field(description="Danh sách điểm yếu.")
    improvement_suggestions: list[str] = Field(
        description="Gợi ý cải thiện cụ thể, khả thi."
    )
    practice_directions: list[str] = Field(
        description="Hướng luyện tập/bài tập gợi ý để tiến bộ."
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Các dẫn chứng kèm timestamp minh hoạ cho nhận xét.",
    )


class AssessmentResult(BaseModel):
    """Kết quả chấm cho toàn bộ video (có thể gồm nhiều học sinh)."""

    task_summary: str = Field(
        description="Tóm tắt ngắn nội dung/bối cảnh bài nói trong video."
    )
    detected_language: str = Field(
        description="Ngôn ngữ chính học sinh sử dụng trong video (vd: English)."
    )
    students: list[StudentAssessment] = Field(
        description="Danh sách kết quả đánh giá cho từng học sinh."
    )
    general_notes: str = Field(
        default="",
        description="Ghi chú chung của giám khảo về cả buổi (nếu có).",
    )

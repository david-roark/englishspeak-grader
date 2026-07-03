"""Rubric chấm điểm: bộ mặc định phổ biến + rubric tùy chỉnh do giáo viên tạo.

Rubric tùy chỉnh được lưu trong SQLite (xem database.py). Module này cung cấp
các rubric mặc định và cấu trúc dữ liệu chung.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Criterion:
    """Một tiêu chí chấm điểm."""

    name: str
    description: str
    min_score: float
    max_score: float


@dataclass
class Rubric:
    """Một bộ tiêu chí chấm điểm hoàn chỉnh."""

    key: str
    name: str
    description: str
    criteria: list[Criterion] = field(default_factory=list)
    scale_note: str = ""

    @property
    def max_total(self) -> float:
        return sum(c.max_score for c in self.criteria)

    def to_prompt_block(self) -> str:
        """Chuyển rubric thành đoạn text mô tả để nhúng vào prompt gửi Gemini."""
        lines = [f"RUBRIC: {self.name}", self.description]
        if self.scale_note:
            lines.append(f"Thang điểm: {self.scale_note}")
        lines.append("Các tiêu chí:")
        for i, c in enumerate(self.criteria, 1):
            lines.append(
                f"  {i}. {c.name} (điểm {c.min_score}–{c.max_score}): {c.description}"
            )
        lines.append(f"Tổng điểm tối đa: {self.max_total}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Các rubric mặc định
# --------------------------------------------------------------------------- #

IELTS_SPEAKING = Rubric(
    key="ielts_speaking",
    name="IELTS Speaking",
    description="Chuẩn IELTS Speaking, 4 tiêu chí, mỗi tiêu chí thang band 0–9.",
    scale_note="Mỗi tiêu chí 0–9 (bước 0.5). Band tổng là trung bình cộng làm tròn 0.5.",
    criteria=[
        Criterion("Fluency and Coherence", "Độ trôi chảy, mạch lạc, khả năng nói liên tục, dùng từ nối, triển khai ý.", 0, 9),
        Criterion("Lexical Resource", "Vốn từ vựng, độ chính xác và linh hoạt khi dùng từ, collocation, paraphrase.", 0, 9),
        Criterion("Grammatical Range and Accuracy", "Đa dạng cấu trúc ngữ pháp và độ chính xác.", 0, 9),
        Criterion("Pronunciation", "Phát âm, trọng âm, ngữ điệu, độ dễ nghe hiểu.", 0, 9),
    ],
)

CEFR = Rubric(
    key="cefr",
    name="CEFR (Khung tham chiếu châu Âu)",
    description="Đánh giá theo khung CEFR, quy về thang 0–6 tương ứng A1→C2.",
    scale_note="0=dưới A1, 1=A1, 2=A2, 3=B1, 4=B2, 5=C1, 6=C2. Ghi overall_level bằng nhãn A1..C2.",
    criteria=[
        Criterion("Range (Vốn ngôn ngữ)", "Khả năng diễn đạt đa dạng ý tưởng, chủ đề.", 0, 6),
        Criterion("Accuracy (Độ chính xác)", "Mức độ chính xác về ngữ pháp và từ vựng.", 0, 6),
        Criterion("Fluency (Độ trôi chảy)", "Khả năng nói liên tục, tự nhiên.", 0, 6),
        Criterion("Interaction (Tương tác)", "Khả năng bắt nhịp hội thoại, phản hồi phù hợp.", 0, 6),
        Criterion("Coherence (Mạch lạc)", "Khả năng liên kết ý, dùng từ nối logic.", 0, 6),
    ],
)

CAMBRIDGE_SCHOOL = Rubric(
    key="cambridge_school",
    name="Cambridge (KET/PET style)",
    description="Phong cách Cambridge cho học sinh phổ thông, mỗi tiêu chí thang 0–5.",
    scale_note="Mỗi tiêu chí 0–5.",
    criteria=[
        Criterion("Grammar and Vocabulary", "Ngữ pháp và từ vựng phù hợp trình độ.", 0, 5),
        Criterion("Pronunciation", "Phát âm rõ, đúng trọng âm và ngữ điệu.", 0, 5),
        Criterion("Interactive Communication", "Khả năng khởi xướng và duy trì hội thoại.", 0, 5),
        Criterion("Discourse Management", "Độ dài, mạch lạc, liên quan của phần trả lời.", 0, 5),
    ],
)

TOEFL_SPEAKING = Rubric(
    key="toefl_speaking",
    name="TOEFL Speaking",
    description="Chuẩn TOEFL Speaking, mỗi tiêu chí thang 0–4.",
    scale_note="Mỗi tiêu chí 0–4 (có thể quy đổi ra thang 30 sau).",
    criteria=[
        Criterion("Delivery", "Độ trôi chảy, phát âm, nhịp độ, dễ nghe.", 0, 4),
        Criterion("Language Use", "Sử dụng ngữ pháp và từ vựng hiệu quả, chính xác.", 0, 4),
        Criterion("Topic Development", "Triển khai ý đầy đủ, mạch lạc, liên kết tốt.", 0, 4),
    ],
)

CLASSROOM_10 = Rubric(
    key="classroom_10",
    name="Lớp học chung (thang 10)",
    description="Rubric tổng quát cho lớp học, mỗi tiêu chí thang 0–10.",
    scale_note="Mỗi tiêu chí 0–10.",
    criteria=[
        Criterion("Nội dung", "Ý tưởng phong phú, đúng chủ đề, thuyết phục.", 0, 10),
        Criterion("Từ vựng", "Dùng từ đa dạng, chính xác, phù hợp ngữ cảnh.", 0, 10),
        Criterion("Ngữ pháp", "Câu đúng ngữ pháp, đa dạng cấu trúc.", 0, 10),
        Criterion("Phát âm", "Phát âm rõ ràng, đúng trọng âm, ngữ điệu tự nhiên.", 0, 10),
        Criterion("Trôi chảy", "Nói liên tục, ít ngập ngừng.", 0, 10),
        Criterion("Tự tin và tương tác", "Thái độ tự tin, giao tiếp bằng mắt, phản hồi tốt.", 0, 10),
    ],
)

DEFAULT_RUBRICS: dict[str, Rubric] = {
    r.key: r
    for r in [IELTS_SPEAKING, CEFR, CAMBRIDGE_SCHOOL, TOEFL_SPEAKING, CLASSROOM_10]
}


def get_default_rubric(key: str) -> Rubric | None:
    return DEFAULT_RUBRICS.get(key)


def rubric_from_dict(data: dict) -> Rubric:
    """Dựng Rubric từ dict (dùng khi đọc rubric tùy chỉnh từ DB)."""
    return Rubric(
        key=data["key"],
        name=data["name"],
        description=data.get("description", ""),
        scale_note=data.get("scale_note", ""),
        criteria=[
            Criterion(
                name=c["name"],
                description=c.get("description", ""),
                min_score=float(c.get("min_score", 0)),
                max_score=float(c["max_score"]),
            )
            for c in data.get("criteria", [])
        ],
    )

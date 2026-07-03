"""Dựng prompt gửi cho Gemini dựa trên rubric, loại bài và tùy chọn."""

from __future__ import annotations

from core.rubrics import Rubric

# Loại bài nói -> mô tả bối cảnh cho model.
TASK_TYPES: dict[str, str] = {
    "presentation": "Bài thuyết trình cá nhân: một học sinh trình bày một chủ đề.",
    "qa": "Hỏi–đáp: giáo viên đặt câu hỏi, học sinh trả lời.",
    "dialogue": "Đối thoại: hai (hoặc nhiều) học sinh nói chuyện với nhau.",
    "group": "Thảo luận nhóm: nhiều học sinh cùng trao đổi.",
    "other": "Bài nói tiếng Anh nói chung.",
}

# Ngôn ngữ nhận xét -> chỉ dẫn.
FEEDBACK_LANGUAGES: dict[str, str] = {
    "vi": "Viết TẤT CẢ nhận xét, điểm mạnh, điểm yếu, gợi ý bằng TIẾNG VIỆT.",
    "en": "Write ALL feedback, strengths, weaknesses, and suggestions in ENGLISH.",
    "bilingual": (
        "Viết nhận xét SONG NGỮ: mỗi mục ghi tiếng Việt trước, rồi tiếng Anh trong ngoặc. "
        "Ví dụ: 'Phát âm rõ ràng (Clear pronunciation)'."
    ),
}


def build_grading_prompt(
    rubric: Rubric,
    task_type: str = "other",
    feedback_language: str = "vi",
    student_names: list[str] | None = None,
    extra_instructions: str = "",
) -> str:
    """Tạo prompt hoàn chỉnh để chấm một video."""
    task_desc = TASK_TYPES.get(task_type, TASK_TYPES["other"])
    lang_instr = FEEDBACK_LANGUAGES.get(feedback_language, FEEDBACK_LANGUAGES["vi"])

    if student_names:
        names_line = (
            "Giáo viên cung cấp sẵn danh sách học sinh (theo thứ tự xuất hiện): "
            + ", ".join(student_names)
            + ". Hãy gán kết quả theo đúng các tên này."
        )
    else:
        names_line = (
            "Giáo viên KHÔNG cung cấp tên. Hãy lắng nghe phần tự giới thiệu trong video "
            "để lấy tên học sinh (đặt name_confident=true). Nếu không nghe được tên, "
            "hãy đặt nhãn 'Học sinh 1', 'Học sinh 2'... theo thứ tự xuất hiện và "
            "đặt name_confident=false để giáo viên gán tên sau."
        )

    parts = [
        "Bạn là một giám khảo chấm thi nói tiếng Anh giàu kinh nghiệm, công tâm và chi tiết.",
        "Nhiệm vụ: xem video học sinh nói tiếng Anh và chấm điểm theo rubric dưới đây.",
        "",
        f"LOẠI BÀI: {task_desc}",
        "",
        rubric.to_prompt_block(),
        "",
        "PHÂN BIỆT HỌC SINH:",
        names_line,
        "",
        "YÊU CẦU CHẤM:",
        "- Xem cả HÌNH ẢNH và ÂM THANH (phát âm, ngữ điệu, cử chỉ, sự tự tin).",
        "- Chấm điểm CHÍNH XÁC theo từng tiêu chí của rubric, không tự thêm/bớt tiêu chí.",
        "- Với mỗi học sinh: nêu điểm mạnh, điểm yếu, gợi ý cải thiện cụ thể và hướng luyện tập.",
        "- Đưa dẫn chứng kèm mốc thời gian (timestamp) cho các nhận xét quan trọng.",
        "- Chấm công bằng theo trình độ; giải thích ngắn gọn lý do mỗi mức điểm.",
        f"- NGÔN NGỮ NHẬN XÉT: {lang_instr}",
        "- Tên tiêu chí trong kết quả phải GIỮ NGUYÊN như trong rubric.",
    ]

    if extra_instructions.strip():
        parts += ["", "YÊU CẦU BỔ SUNG TỪ GIÁO VIÊN:", extra_instructions.strip()]

    parts += [
        "",
        "Trả về kết quả đúng theo cấu trúc JSON được yêu cầu (không thêm văn bản ngoài JSON).",
    ]
    return "\n".join(parts)

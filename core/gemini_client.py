"""Giao tiếp với Gemini API: upload video (File API) và chấm điểm có cấu trúc.

Dùng SDK chính thức `google-genai`.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from google import genai
from google.genai import types

from core.prompts import build_grading_prompt
from core.rubrics import Rubric
from core.schemas import AssessmentResult

# Các model miễn phí tốt (Free tier, không cần thẻ). Xếp theo ưu tiên.
FREE_TIER_MODELS = [
    "gemini-2.5-flash",       # mặc định: mạnh, 500 RPD free, context 1M
    "gemini-2.5-flash-lite",  # nhẹ/nhanh hơn, cũng 500 RPD free
    "gemini-2.0-flash",       # dự phòng
]

# Model chất lượng cao hơn (có thể cần billing -> để tùy chọn, không mặc định).
PREMIUM_MODELS = ["gemini-2.5-pro"]

ALL_MODELS = FREE_TIER_MODELS + PREMIUM_MODELS
DEFAULT_MODEL = FREE_TIER_MODELS[0]

# Trạng thái file sau khi upload.
_STATE_ACTIVE = "ACTIVE"
_STATE_FAILED = "FAILED"


class GeminiError(RuntimeError):
    """Lỗi khi gọi Gemini (thiếu key, upload lỗi, model từ chối...)."""


def make_client(api_key: str | None = None) -> genai.Client:
    """Tạo client. Ưu tiên api_key truyền vào, sau đó biến môi trường."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key or key == "dan_key_cua_ban_vao_day":
        raise GeminiError(
            "Chưa có GEMINI_API_KEY. Lấy key miễn phí tại https://aistudio.google.com "
            "(Get API key), rồi dán vào ô API key hoặc file .env."
        )
    return genai.Client(api_key=key)


def upload_video(
    client: genai.Client,
    video_path: str | Path,
    *,
    poll_interval: float = 2.0,
    timeout: float = 600.0,
    on_progress: Callable[[str], None] | None = None,
) -> types.File:
    """Upload video qua File API và chờ tới khi ACTIVE.

    Trả về đối tượng File để dùng trong request chấm điểm.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise GeminiError(f"Không tìm thấy file video: {video_path}")

    def report(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    report("Đang tải video lên Gemini...")
    uploaded = client.files.upload(file=video_path)

    # Chờ Gemini xử lý xong (PROCESSING -> ACTIVE).
    deadline = time.time() + timeout
    while getattr(uploaded.state, "name", uploaded.state) not in (_STATE_ACTIVE, _STATE_FAILED):
        if time.time() > deadline:
            raise GeminiError("Hết thời gian chờ Gemini xử lý video.")
        report("Gemini đang xử lý video...")
        time.sleep(poll_interval)
        if not uploaded.name:
            raise GeminiError("Upload video lỗi: không nhận được mã file từ Gemini.")
        uploaded = client.files.get(name=uploaded.name)

    state_name = getattr(uploaded.state, "name", uploaded.state)
    if state_name == _STATE_FAILED:
        raise GeminiError("Gemini xử lý video thất bại. Thử lại hoặc đổi định dạng video.")

    report("Video sẵn sàng để chấm.")
    return uploaded


def grade_video(
    client: genai.Client,
    uploaded_file: types.File,
    rubric: Rubric,
    *,
    model: str = DEFAULT_MODEL,
    task_type: str = "other",
    feedback_language: str = "vi",
    student_names: list[str] | None = None,
    extra_instructions: str = "",
    on_progress: Callable[[str], None] | None = None,
) -> AssessmentResult:
    """Gửi video + prompt + schema cho Gemini, nhận kết quả có cấu trúc."""
    if on_progress:
        on_progress(f"Đang chấm bằng model {model}...")

    prompt = build_grading_prompt(
        rubric,
        task_type=task_type,
        feedback_language=feedback_language,
        student_names=student_names,
        extra_instructions=extra_instructions,
    )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AssessmentResult,
        temperature=0.4,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=[uploaded_file, prompt],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 - gói lại cho UI dễ đọc
        raise GeminiError(f"Lỗi khi gọi Gemini: {exc}") from exc

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, AssessmentResult):
        return parsed

    # Dự phòng: tự parse JSON text nếu SDK không trả .parsed
    text = getattr(response, "text", "") or ""
    if not text.strip():
        raise GeminiError("Gemini không trả về kết quả. Thử lại hoặc đổi model.")
    try:
        return AssessmentResult.model_validate_json(text)
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(
            f"Không đọc được kết quả JSON từ Gemini: {exc}\n---\n{text[:500]}"
        ) from exc


def cleanup_file(client: genai.Client, uploaded_file: types.File) -> None:
    """Xóa file đã upload khỏi Gemini (nếu muốn dọn sớm; nếu không cũng tự xóa sau 48h)."""
    try:
        if uploaded_file.name:
            client.files.delete(name=uploaded_file.name)
    except Exception:  # noqa: BLE001 - dọn dẹp, lỗi thì bỏ qua
        pass

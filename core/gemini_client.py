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

# Danh sách model TĨNH dùng làm fallback khi chưa nhập key / API lỗi.
# ID API có thể sai theo thời gian -> ưu tiên lấy động qua list_models() (dưới đây).
# Giới hạn free tier (RPD) thay đổi theo tài khoản; xem lại tại aistudio.google.com.
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",  # mặc định: nhiều lượt nhất (Flash Lite ~500 RPD)
    "gemini-flash-latest",       # Flash mới nhất, chất lượng cao hơn (ít lượt hơn)
    "gemini-2.5-flash",          # Flash ổn định
    "gemini-2.5-flash-lite",     # Flash Lite ổn định
    "gemini-2.0-flash",          # dự phòng
]

DEFAULT_MODEL = FALLBACK_MODELS[0]

# Tương thích ngược (mã cũ tham chiếu ALL_MODELS).
ALL_MODELS = FALLBACK_MODELS

# Độ phân giải media cho video. LOW (~100 token/giây) an toàn với free tier TPM;
# MEDIUM (~300 token/giây) chi tiết hơn nhưng video dài dễ vượt giới hạn token/phút.
MEDIA_RESOLUTIONS = {
    "low": types.MediaResolution.MEDIA_RESOLUTION_LOW,
    "default": types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
    "high": types.MediaResolution.MEDIA_RESOLUTION_HIGH,
}
DEFAULT_MEDIA_RESOLUTION = "low"

# Trạng thái file sau khi upload.
_STATE_ACTIVE = "ACTIVE"
_STATE_FAILED = "FAILED"


# Từ khóa loại các model KHÔNG dùng để chấm video (không nhận video hoặc không
# trả văn bản có cấu trúc): TTS, live/audio, sinh ảnh (Nano Banana), robotics,
# embedding, computer-use, veo/imagen/lyria... Gemma (text-only) tự loại vì
# không bắt đầu bằng "gemini".
_EXCLUDE_KEYWORDS = (
    "tts", "audio", "live", "image", "nano-banana", "robotics", "embedding",
    "computer-use", "veo", "imagen", "lyria", "aqa", "learnlm",
)


def _is_gradable_model(model_id: str) -> bool:
    """True nếu model dùng được để chấm video: dòng Gemini Flash/Pro đa phương thức."""
    mid = model_id.lower().removeprefix("models/")
    if not mid.startswith("gemini"):
        return False
    if any(k in mid for k in _EXCLUDE_KEYWORDS):
        return False
    return "flash" in mid or "pro" in mid


def _rank_model(mid: str) -> tuple[int, str]:
    """Sắp xếp: Flash Lite trước (nhiều lượt free nhất), rồi Flash, cuối là Pro."""
    if "flash-lite" in mid or "flash-8b" in mid:
        return (0, mid)
    if "flash" in mid:
        return (1, mid)
    if "pro" in mid:
        return (2, mid)
    return (3, mid)


def list_models(client: genai.Client) -> list[str]:
    """Lấy danh sách model chấm video được từ API (bằng key của người dùng).

    Chỉ giữ dòng Gemini Flash/Pro đa phương thức, bỏ TTS/live/ảnh/robotics/...
    Sắp Flash Lite trước. Lỗi hoặc không có kết quả thì trả về FALLBACK_MODELS.
    """
    try:
        ids: list[str] = []
        for m in client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if actions and "generateContent" not in actions:
                continue
            name = (getattr(m, "name", "") or "").removeprefix("models/")
            if _is_gradable_model(name):
                ids.append(name)
        if not ids:
            return list(FALLBACK_MODELS)
        return sorted(dict.fromkeys(ids), key=_rank_model)
    except Exception:  # noqa: BLE001 - offline / key lỗi -> dùng fallback
        return list(FALLBACK_MODELS)


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
    media_resolution: str = DEFAULT_MEDIA_RESOLUTION,
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
        media_resolution=MEDIA_RESOLUTIONS.get(media_resolution, MEDIA_RESOLUTIONS[DEFAULT_MEDIA_RESOLUTION]),
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

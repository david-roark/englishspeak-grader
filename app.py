"""Speak Grader — App AI (Gemini) hỗ trợ giáo viên chấm bài nói tiếng Anh.

Chạy web cục bộ bằng Gradio. Khởi động: `uv run app.py` (hoặc run.sh / run.bat).
"""

from __future__ import annotations

import json
import os

import gradio as gr
from dotenv import load_dotenv

from core import database as db
from core.export import export_to_excel
from core.gemini_client import (
    ALL_MODELS,
    DEFAULT_MEDIA_RESOLUTION,
    DEFAULT_MODEL,
    GeminiError,
    cleanup_file,
    grade_video,
    list_models,
    make_client,
    upload_video,
)
from core.prompts import FEEDBACK_LANGUAGES, TASK_TYPES
from core.rubrics import DEFAULT_RUBRICS, Criterion, Rubric, rubric_from_dict
from core.schemas import AssessmentResult

load_dotenv()
db.init_db()

# Nhãn hiển thị thân thiện cho các lựa chọn.
TASK_LABELS = {
    "presentation": "Thuyết trình cá nhân",
    "qa": "Hỏi – đáp",
    "dialogue": "Đối thoại (2 người)",
    "group": "Thảo luận nhóm",
    "other": "Khác / nói chung",
}
LANG_LABELS = {
    "vi": "Tiếng Việt",
    "en": "English",
    "bilingual": "Song ngữ (Việt + Anh)",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def all_rubrics() -> dict[str, Rubric]:
    """Gộp rubric mặc định + rubric tùy chỉnh (từ DB)."""
    merged: dict[str, Rubric] = dict(DEFAULT_RUBRICS)
    for data in db.list_custom_rubrics():
        merged[data["key"]] = rubric_from_dict(data)
    return merged


def default_rubrics_markdown() -> str:
    """Bảng tra cứu (read-only) toàn bộ rubric mặc định đang dùng."""
    blocks: list[str] = []
    for r in DEFAULT_RUBRICS.values():
        rows = "\n".join(
            f"| {c.name} | {c.description} | {c.min_score:g}–{c.max_score:g} |"
            for c in r.criteria
        )
        blocks.append(
            f"### {r.name}\n"
            f"`{r.key}` · Tổng tối đa: **{r.max_total:g}** điểm\n\n"
            f"{r.description}\n\n"
            + (f"*Thang điểm:* {r.scale_note}\n\n" if r.scale_note else "")
            + "| Tiêu chí | Mô tả | Điểm |\n|---|---|---|\n"
            + rows
        )
    return "\n\n---\n\n".join(blocks)


def rubric_choices() -> list[tuple[str, str]]:
    choices = []
    for key, r in DEFAULT_RUBRICS.items():
        choices.append((f"[Mặc định] {r.name}", key))
    for data in db.list_custom_rubrics():
        choices.append((f"[Tùy chỉnh] {data['name']}", data["key"]))
    return choices


def format_result_markdown(result: AssessmentResult) -> str:
    """Chuyển kết quả thành markdown để hiển thị đẹp."""
    lines = [f"## Kết quả chấm điểm", ""]
    lines.append(f"**Ngôn ngữ nói:** {result.detected_language}  ")
    lines.append(f"**Tóm tắt:** {result.task_summary}")
    if result.general_notes:
        lines.append(f"\n**Ghi chú chung:** {result.general_notes}")
    lines.append("")

    for i, s in enumerate(result.students, 1):
        conf = "" if s.name_confident else "  _(tên tạm — cần gán lại)_"
        lines.append(f"---\n### {i}. {s.student_name}{conf}")
        lines.append(
            f"**Tổng điểm:** {s.total_score} / {s.max_total_score}  |  "
            f"**Xếp loại:** {s.overall_level}\n"
        )
        lines.append("| Tiêu chí | Điểm | Nhận xét |")
        lines.append("|---|---|---|")
        for c in s.criteria:
            comment = c.comment.replace("\n", " ").replace("|", "/")
            lines.append(f"| {c.criterion} | {c.score}/{c.max_score} | {comment} |")
        lines.append("")

        def _block(title: str, items: list[str]) -> None:
            if items:
                lines.append(f"**{title}:**")
                for it in items:
                    lines.append(f"- {it}")
                lines.append("")

        _block("Điểm mạnh", s.strengths)
        _block("Điểm yếu", s.weaknesses)
        _block("Gợi ý cải thiện", s.improvement_suggestions)
        _block("Hướng luyện tập", s.practice_directions)

        if s.evidence:
            lines.append("**Dẫn chứng (timestamp):**")
            for ev in s.evidence:
                lines.append(f"- `{ev.timestamp}` — {ev.quote} _({ev.note})_")
            lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Hành động chính: chấm bài
# --------------------------------------------------------------------------- #

def run_grading(
    api_key: str,
    video_path: str,
    rubric_key: str,
    task_type: str,
    feedback_lang: str,
    model: str,
    student_names_raw: str,
    extra_instructions: str,
    media_resolution: str,
    progress: gr.Progress = gr.Progress(),
):
    """Trả về (markdown_kết_quả, đường_dẫn_excel, trạng_thái, state_result)."""
    if not video_path:
        return "⚠️ Chưa chọn video.", None, "Chưa chấm.", None

    rubrics = all_rubrics()
    rubric = rubrics.get(rubric_key)
    if rubric is None:
        return "⚠️ Chưa chọn rubric hợp lệ.", None, "Chưa chấm.", None

    names = [n.strip() for n in student_names_raw.split(",") if n.strip()] or None

    try:
        progress(0.05, desc="Kết nối Gemini...")
        client = make_client(api_key)

        uploaded = upload_video(
            client, video_path,
            on_progress=lambda m: progress(0.3, desc=m),
        )

        progress(0.6, desc="Đang chấm điểm...")
        result = grade_video(
            client, uploaded, rubric,
            model=model,
            task_type=task_type,
            feedback_language=feedback_lang,
            student_names=names,
            extra_instructions=extra_instructions,
            media_resolution=media_resolution,
            on_progress=lambda m: progress(0.7, desc=m),
        )

        cleanup_file(client, uploaded)

        progress(0.9, desc="Lưu kết quả & xuất Excel...")
        video_name = os.path.basename(video_path)
        db.save_assessment(
            result,
            video_name=video_name,
            rubric_key=rubric.key,
            rubric_name=rubric.name,
            task_type=task_type,
            model=model,
            feedback_lang=feedback_lang,
        )
        xlsx = export_to_excel(result, video_name=video_name, rubric_name=rubric.name)

        progress(1.0, desc="Xong!")
        md = format_result_markdown(result)
        status = f"✅ Đã chấm {len(result.students)} học sinh. Excel: {xlsx.name}"
        return md, str(xlsx), status, result.model_dump_json()

    except GeminiError as e:
        return f"❌ {e}", None, "Lỗi.", None
    except Exception as e:  # noqa: BLE001
        return f"❌ Lỗi không mong muốn: {e}", None, "Lỗi.", None


# --------------------------------------------------------------------------- #
# Rubric tùy chỉnh
# --------------------------------------------------------------------------- #

def save_rubric(key: str, name: str, description: str, scale_note: str, table):
    key = (key or "").strip()
    name = (name or "").strip()
    if not key or not name:
        return "⚠️ Cần nhập cả mã (key) và tên rubric.", gr.update()
    if key in DEFAULT_RUBRICS:
        return f"⚠️ Mã '{key}' trùng rubric mặc định. Dùng mã khác.", gr.update()

    criteria = []
    for row in table:
        if not row or not str(row[0]).strip():
            continue
        try:
            criteria.append(
                Criterion(
                    name=str(row[0]).strip(),
                    description=str(row[1]).strip() if len(row) > 1 else "",
                    min_score=float(row[2]) if len(row) > 2 and row[2] != "" else 0.0,
                    max_score=float(row[3]) if len(row) > 3 and row[3] != "" else 10.0,
                )
            )
        except (ValueError, TypeError):
            return "⚠️ Điểm min/max phải là số.", gr.update()

    if not criteria:
        return "⚠️ Cần ít nhất 1 tiêu chí.", gr.update()

    rubric = Rubric(key=key, name=name, description=description, scale_note=scale_note, criteria=criteria)
    db.save_custom_rubric(rubric)
    return (
        f"✅ Đã lưu rubric '{name}' ({len(criteria)} tiêu chí).",
        gr.update(choices=rubric_choices()),
    )


def delete_rubric(key: str):
    key = (key or "").strip()
    if not key:
        return "⚠️ Nhập mã rubric cần xóa.", gr.update()
    if key in DEFAULT_RUBRICS:
        return "⚠️ Không thể xóa rubric mặc định.", gr.update()
    db.delete_custom_rubric(key)
    return f"✅ Đã xóa rubric '{key}'.", gr.update(choices=rubric_choices())


# --------------------------------------------------------------------------- #
# Lịch sử
# --------------------------------------------------------------------------- #

def load_history():
    rows = db.list_assessments()
    if not rows:
        return [["—", "Chưa có bản ghi nào", "", "", ""]]
    return [
        [r["id"], r["created_at"], r["video_name"] or "", r["rubric_name"] or "", r["task_summary"] or ""]
        for r in rows
    ]


def view_history_item(assessment_id: str):
    try:
        aid = int(str(assessment_id).strip())
    except (ValueError, TypeError):
        return "⚠️ Nhập ID hợp lệ (số).", None
    data = db.get_assessment(aid)
    if not data:
        return f"⚠️ Không tìm thấy bản ghi ID {aid}.", None
    result: AssessmentResult = data["result"]
    md = format_result_markdown(result)
    xlsx = export_to_excel(result, video_name=data.get("video_name") or "", rubric_name=data.get("rubric_name") or "")
    return md, str(xlsx)


# --------------------------------------------------------------------------- #
# Giao diện
# --------------------------------------------------------------------------- #

def build_ui() -> gr.Blocks:
    env_key = os.getenv("GEMINI_API_KEY", "")
    has_env_key = bool(env_key) and env_key != "dan_key_cua_ban_vao_day"

    with gr.Blocks(title="Speak Grader — Chấm bài nói tiếng Anh bằng AI") as demo:
        gr.Markdown(
            "# 🎓 Speak Grader\n"
            "Chấm bài nói tiếng Anh qua video bằng Gemini AI: bảng điểm, nhận xét, "
            "gợi ý cải thiện theo chuẩn quốc tế hoặc rubric riêng của bạn."
        )

        with gr.Row():
            api_key = gr.Textbox(
                label="Gemini API Key",
                type="password",
                value="" if has_env_key else "",
                placeholder=("Đã đọc từ .env ✓ (để trống để dùng key này)" if has_env_key
                             else "Dán key từ https://aistudio.google.com"),
                scale=3,
            )
            model = gr.Dropdown(
                label="Model", choices=ALL_MODELS, value=DEFAULT_MODEL, scale=2,
                info="Flash Lite: nhiều lượt free nhất. Flash/Pro: chất lượng cao hơn, ít lượt hơn.",
            )
            load_models_btn = gr.Button("🔄 Tải model", scale=1)

        gr.Markdown(
            "Rate limit (RPM/TPM/RPD) khác nhau theo model và theo tài khoản, không lấy được "
            "qua API — xem số thật của bạn tại "
            "[AI Studio · Rate limits](https://aistudio.google.com/app/rate-limit)."
        )

        with gr.Row():
            media_res = gr.Radio(
                label="Độ phân giải video",
                choices=[("Thấp — tiết kiệm token, an toàn free tier", "low"),
                         ("Trung bình — chi tiết hơn, video dài dễ vượt giới hạn", "default"),
                         ("Cao — chi tiết nhất, tốn token nhất", "high")],
                value=DEFAULT_MEDIA_RESOLUTION,
                info="Nên để Thấp cho video dài hoặc khi dùng free tier.",
            )

        with gr.Tabs():
            # ---- Tab 1: Chấm bài -------------------------------------------- #
            with gr.Tab("Chấm bài"):
                with gr.Row():
                    with gr.Column(scale=1):
                        video = gr.Video(label="Video bài nói của học sinh")
                        rubric_dd = gr.Dropdown(
                            label="Rubric (tiêu chuẩn chấm)",
                            choices=rubric_choices(),
                            value="ielts_speaking",
                        )
                        task_dd = gr.Dropdown(
                            label="Loại bài",
                            choices=[(v, k) for k, v in TASK_LABELS.items()],
                            value="presentation",
                        )
                        lang_dd = gr.Dropdown(
                            label="Ngôn ngữ nhận xét",
                            choices=[(v, k) for k, v in LANG_LABELS.items()],
                            value="vi",
                        )
                        names_tb = gr.Textbox(
                            label="Tên học sinh (tùy chọn, cách nhau bằng dấu phẩy)",
                            placeholder="VD: An, Bình  — để trống nếu muốn AI tự lấy tên từ video",
                        )
                        extra_tb = gr.Textbox(
                            label="Yêu cầu bổ sung (tùy chọn)",
                            placeholder="VD: chú trọng phát âm; bỏ qua phần chào hỏi...",
                            lines=2,
                        )
                        grade_btn = gr.Button("🚀 Chấm điểm", variant="primary")
                    with gr.Column(scale=2):
                        status = gr.Markdown("Sẵn sàng. Chọn video và bấm *Chấm điểm*.")
                        result_md = gr.Markdown()
                        excel_file = gr.File(label="Tải file Excel kết quả")
                        result_state = gr.State()

                grade_btn.click(
                    run_grading,
                    inputs=[api_key, video, rubric_dd, task_dd, lang_dd, model,
                            names_tb, extra_tb, media_res],
                    outputs=[result_md, excel_file, status, result_state],
                )

            # ---- Tab 2: Rubric tùy chỉnh ------------------------------------ #
            with gr.Tab("Rubric tùy chỉnh"):
                gr.Markdown(
                    "Tạo rubric riêng của bạn. Mỗi dòng trong bảng là một tiêu chí. "
                    "Rubric đã lưu sẽ xuất hiện trong danh sách ở tab Chấm bài."
                )
                with gr.Row():
                    r_key = gr.Textbox(label="Mã (key, không dấu, VD: my_rubric)")
                    r_name = gr.Textbox(label="Tên hiển thị")
                r_desc = gr.Textbox(label="Mô tả", lines=2)
                r_scale = gr.Textbox(label="Ghi chú thang điểm (tùy chọn)")
                r_table = gr.Dataframe(
                    headers=["Tên tiêu chí", "Mô tả", "Điểm min", "Điểm max"],
                    datatype=["str", "str", "number", "number"],
                    row_count=(4, "dynamic"),
                    column_count=(4, "fixed"),
                    label="Tiêu chí",
                )
                with gr.Row():
                    save_btn = gr.Button("💾 Lưu rubric", variant="primary")
                    del_key = gr.Textbox(label="Mã rubric cần xóa", scale=2)
                    del_btn = gr.Button("🗑️ Xóa")
                rubric_status = gr.Markdown()

                save_btn.click(
                    save_rubric,
                    inputs=[r_key, r_name, r_desc, r_scale, r_table],
                    outputs=[rubric_status, rubric_dd],
                )
                del_btn.click(delete_rubric, inputs=[del_key], outputs=[rubric_status, rubric_dd])

            # ---- Tab 3: Rubric mặc định (xem) ------------------------------- #
            with gr.Tab("Rubric mặc định"):
                gr.Markdown(
                    "Các bộ tiêu chí có sẵn đang dùng để chấm (chỉ xem). "
                    "Muốn thay đổi thì tạo bản riêng ở tab *Rubric tùy chỉnh*."
                )
                gr.Markdown(default_rubrics_markdown())

            # ---- Tab 4: Lịch sử --------------------------------------------- #
            with gr.Tab("Lịch sử"):
                gr.Markdown("Các lần chấm đã lưu (SQLite). Nhập ID để xem lại và tải Excel.")
                hist_df = gr.Dataframe(
                    headers=["ID", "Thời gian", "Video", "Rubric", "Tóm tắt"],
                    interactive=False,
                    label="Lịch sử chấm",
                )
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Tải lại danh sách")
                    hist_id = gr.Textbox(label="Xem ID", scale=1)
                    view_btn = gr.Button("👁️ Xem lại")
                hist_result = gr.Markdown()
                hist_excel = gr.File(label="Excel")

                refresh_btn.click(load_history, outputs=[hist_df])
                view_btn.click(view_history_item, inputs=[hist_id], outputs=[hist_result, hist_excel])
                demo.load(load_history, outputs=[hist_df])

        def refresh_models(key: str):
            """Lấy danh sách model động bằng key của người dùng."""
            try:
                client = make_client(key)
            except GeminiError as e:
                return gr.update(), f"⚠️ {e}"
            models = list_models(client)
            value = DEFAULT_MODEL if DEFAULT_MODEL in models else models[0]
            return (gr.update(choices=models, value=value),
                    f"✅ Đã tải {len(models)} model từ tài khoản của bạn.")

        load_models_btn.click(refresh_models, inputs=[api_key], outputs=[model, status])

        gr.Markdown(
            "---\n*Chạy cục bộ trên máy bạn. API key và video không gửi đi đâu khác ngoài Google Gemini.*"
        )

    return demo


def main() -> None:
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", inbrowser=True, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()

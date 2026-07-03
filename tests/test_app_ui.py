"""Test tầng UI (Mức 1): các callback còn lại + smoke build_ui + nối dây nút.

Không mở trình duyệt, không gọi Gemini. Ta kiểm:
- Từng callback trả đúng giá trị mong đợi (kể cả nhánh cảnh báo).
- build_ui() dựng được Blocks không lỗi.
- Các nút đã gắn ĐÚNG callback (đọc từ demo.fns của Gradio) — đây chính là
  lớp lỗi kiểu "bấm nút mà không có gì xảy ra".
"""

from __future__ import annotations

import app
from core import database as db
from core.rubrics import Criterion, Rubric


# --- delete_rubric -------------------------------------------------------- #

def test_delete_rubric_key_rỗng_báo_lỗi():
    msg, _ = app.delete_rubric("")
    assert msg.startswith("⚠️")


def test_delete_rubric_mặc_định_bị_chặn():
    msg, _ = app.delete_rubric("ielts_speaking")
    assert msg.startswith("⚠️")
    assert "ielts_speaking" in app.DEFAULT_RUBRICS  # vẫn còn


def test_delete_rubric_thành_công():
    db.save_custom_rubric(Rubric(key="tmp", name="Tmp", description="",
                                 criteria=[Criterion("A", "", 0, 10)]))
    msg, _ = app.delete_rubric("tmp")
    assert msg.startswith("✅")
    assert "tmp" not in [r["key"] for r in db.list_custom_rubrics()]


# --- load_history --------------------------------------------------------- #

def test_load_history_rỗng_trả_placeholder():
    rows = app.load_history()
    assert len(rows) == 1
    assert "Chưa có bản ghi" in rows[0][1]


def test_load_history_có_dữ_liệu(sample_result):
    db.save_assessment(sample_result, video_name="v.mp4", rubric_key="k",
                       rubric_name="R", task_type="t", model="m", feedback_lang="vi")
    rows = app.load_history()
    assert len(rows) == 1
    assert rows[0][2] == "v.mp4"       # cột video_name
    assert rows[0][3] == "R"           # cột rubric_name


# --- view_history_item ---------------------------------------------------- #

def test_view_history_item_id_không_hợp_lệ():
    md, xlsx = app.view_history_item("abc")
    assert md.startswith("⚠️")
    assert xlsx is None


def test_view_history_item_không_tồn_tại():
    md, xlsx = app.view_history_item("99999")
    assert md.startswith("⚠️")
    assert xlsx is None


def test_view_history_item_roundtrip(sample_result):
    aid = db.save_assessment(sample_result, video_name="v.mp4", rubric_key="k",
                             rubric_name="IELTS", task_type="t", model="m", feedback_lang="vi")
    md, xlsx = app.view_history_item(str(aid))
    assert "Kết quả chấm điểm" in md
    assert "An" in md                  # tên học sinh trong markdown
    assert xlsx is not None and xlsx.endswith(".xlsx")


# --- format_result_markdown ---------------------------------------------- #

def test_format_result_markdown_đủ_thành_phần(sample_result):
    md = app.format_result_markdown(sample_result)
    assert "An" in md and "Học sinh 2" in md
    assert "Band 6.5" in md
    assert "Fluency" in md
    assert "_(tên tạm — cần gán lại)_" in md   # HS name_confident=False
    assert "`00:12`" in md                     # dẫn chứng timestamp


# --- default_rubrics_markdown -------------------------------------------- #

def test_default_rubrics_markdown_liệt_kê_đủ():
    md = app.default_rubrics_markdown()
    for r in app.DEFAULT_RUBRICS.values():
        assert r.name in md


# --- run_extract_mp3 (chỉ nhánh cảnh báo, không cần ffmpeg) --------------- #

def test_run_extract_mp3_thiếu_video():
    msg, out = app.run_extract_mp3(None, app.DEFAULT_MP3_PRESET)
    assert msg.startswith("⚠️")
    assert out is None


# --- run_grading (nhánh guard, không gọi Gemini) ------------------------- #

def test_run_grading_thiếu_video():
    md, xlsx, status, state, cache = app.run_grading(
        "key", "", "ielts_speaking", "presentation", "vi", "model", "", "", "default", None)
    assert md.startswith("⚠️")
    assert xlsx is None and state is None


def test_run_grading_rubric_sai():
    md, *_ = app.run_grading(
        "key", "/tmp/x.mp4", "rubric_khong_ton_tai", "presentation", "vi",
        "model", "", "", "default", None)
    assert md.startswith("⚠️")


# --- Smoke + nối dây UI --------------------------------------------------- #

def test_build_ui_dựng_không_lỗi(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    demo = app.build_ui()
    assert demo is not None
    assert len(demo.fns) > 0


def test_các_nút_gắn_đúng_callback(monkeypatch):
    """Kiểm nút bấm nối vào đúng hàm — bắt lỗi 'bấm mà không có gì xảy ra'."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    demo = app.build_ui()
    wired = {getattr(f.fn, "__name__", None) for f in demo.fns.values()}
    # delete_rubric giờ nằm trong closure của gr.render (danh sách động) nên
    # không xuất hiện theo tên ở demo.fns lúc build — nó được test trực tiếp riêng.
    for expected in {
        "run_grading", "save_rubric",
        "run_extract_mp3", "load_history", "view_history_item", "refresh_models",
    }:
        assert expected in wired, f"Callback '{expected}' chưa được gắn vào UI"

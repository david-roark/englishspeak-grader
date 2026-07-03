"""Test callback lưu rubric tùy chỉnh ở tab UI.

Trọng tâm: regression cho lỗi Gradio 6 — gr.Dataframe mặc định trả pandas
DataFrame, khiến save_rubric (viết cho list-of-lists) lưu hỏng âm thầm nên
không báo thành công và rubric không hiện trong dropdown Chấm bài.
"""

from __future__ import annotations

import pandas as pd

import app
from core import database as db


def _ok(msg: str) -> bool:
    return msg.startswith("✅")


def test_save_rubric_list_of_lists():
    """type='array': đường đi chính hiện tại."""
    table = [
        ["Nội dung", "Ý rõ ràng", 0, 10],
        ["Phát âm", "Đúng trọng âm", "", ""],  # ô số trống -> mặc định 0/10
        ["", "", "", ""],                      # dòng trống -> bỏ qua
    ]
    msg, _ = app.save_rubric("r_arr", "Rubric Array", "d", "s", table)
    assert _ok(msg)
    saved = {r["key"]: r for r in db.list_custom_rubrics()}
    assert "r_arr" in saved
    assert len(saved["r_arr"]["criteria"]) == 2
    assert saved["r_arr"]["criteria"][1]["max_score"] == 10  # ô trống -> default


def test_save_rubric_pandas_dataframe():
    """Nhánh phòng hờ: nếu Dataframe trả pandas thì vẫn phải lưu đúng."""
    df = pd.DataFrame(
        [["Nội dung", "desc", 0, 10], ["", "", None, None]],
        columns=["Tên tiêu chí", "Mô tả", "Điểm min", "Điểm max"],
    )
    msg, _ = app.save_rubric("r_df", "Rubric DF", "d", "s", df)
    assert _ok(msg)
    saved = {r["key"]: r for r in db.list_custom_rubrics()}
    assert "r_df" in saved
    assert len(saved["r_df"]["criteria"]) == 1  # dòng NaN bị bỏ


def test_rubric_lưu_xong_xuất_hiện_trong_dropdown():
    """Sau khi lưu, rubric phải nằm trong danh sách chọn ở tab Chấm bài."""
    app.save_rubric("r_dd", "Rubric Dropdown", "d", "s", [["Ý", "", 0, 10]])
    keys = [v for _, v in app.rubric_choices()]
    assert "r_dd" in keys
    # nhãn có tiền tố [Tùy chỉnh]
    labels = {v: label for label, v in app.rubric_choices()}
    assert labels["r_dd"].startswith("[Tùy chỉnh]")


def test_save_rubric_thiếu_key_hoặc_tên_báo_lỗi():
    msg, _ = app.save_rubric("", "Tên", "", "", [["Ý", "", 0, 10]])
    assert msg.startswith("⚠️")
    msg, _ = app.save_rubric("k", "", "", "", [["Ý", "", 0, 10]])
    assert msg.startswith("⚠️")


def test_save_rubric_trùng_mã_mặc_định_bị_chặn():
    msg, _ = app.save_rubric("ielts_speaking", "Trùng", "", "", [["Ý", "", 0, 10]])
    assert msg.startswith("⚠️")
    assert "ielts_speaking" not in [r["key"] for r in db.list_custom_rubrics()]


def test_save_rubric_không_có_tiêu_chí_báo_lỗi():
    msg, _ = app.save_rubric("k", "Tên", "", "", [["", "", "", ""]])
    assert msg.startswith("⚠️")
    assert "ít nhất 1 tiêu chí" in msg


def test_save_rubric_điểm_không_phải_số_báo_lỗi():
    msg, _ = app.save_rubric("k", "Tên", "", "", [["Ý", "", "abc", 10]])
    assert msg.startswith("⚠️")


def test_all_rubrics_gộp_mặc_định_và_tùy_chỉnh():
    app.save_rubric("r_merge", "Merge", "d", "s", [["Ý", "", 0, 10]])
    merged = app.all_rubrics()
    assert "ielts_speaking" in merged   # mặc định
    assert "r_merge" in merged          # tùy chỉnh

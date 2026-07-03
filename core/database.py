"""Lớp lưu trữ SQLite: rubric tùy chỉnh và kết quả chấm điểm.

DB nằm ở data/app.db (tự tạo lần chạy đầu). Không commit vào git.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from core.rubrics import Rubric
from core.schemas import AssessmentResult

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Tạo bảng nếu chưa có."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS custom_rubrics (
                key         TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                scale_note  TEXT,
                criteria    TEXT NOT NULL,          -- JSON list
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assessments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,
                video_name    TEXT,
                rubric_key    TEXT,
                rubric_name   TEXT,
                task_type     TEXT,
                model         TEXT,
                feedback_lang TEXT,
                result_json   TEXT NOT NULL,        -- AssessmentResult dạng JSON
                task_summary  TEXT
            );
            """
        )


# --------------------------------------------------------------------------- #
# Rubric tùy chỉnh
# --------------------------------------------------------------------------- #

def save_custom_rubric(rubric: Rubric) -> None:
    criteria = [
        {
            "name": c.name,
            "description": c.description,
            "min_score": c.min_score,
            "max_score": c.max_score,
        }
        for c in rubric.criteria
    ]
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO custom_rubrics (key, name, description, scale_note, criteria, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                scale_note=excluded.scale_note,
                criteria=excluded.criteria
            """,
            (
                rubric.key,
                rubric.name,
                rubric.description,
                rubric.scale_note,
                json.dumps(criteria, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def list_custom_rubrics() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM custom_rubrics ORDER BY created_at DESC"
        ).fetchall()
    result = []
    for r in rows:
        result.append(
            {
                "key": r["key"],
                "name": r["name"],
                "description": r["description"] or "",
                "scale_note": r["scale_note"] or "",
                "criteria": json.loads(r["criteria"]),
            }
        )
    return result


def delete_custom_rubric(key: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM custom_rubrics WHERE key = ?", (key,))


# --------------------------------------------------------------------------- #
# Kết quả chấm điểm
# --------------------------------------------------------------------------- #

def save_assessment(
    result: AssessmentResult,
    *,
    video_name: str,
    rubric_key: str,
    rubric_name: str,
    task_type: str,
    model: str,
    feedback_lang: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO assessments
                (created_at, video_name, rubric_key, rubric_name, task_type,
                 model, feedback_lang, result_json, task_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                video_name,
                rubric_key,
                rubric_name,
                task_type,
                model,
                feedback_lang,
                result.model_dump_json(),
                result.task_summary,
            ),
        )
        return int(cur.lastrowid or 0)


def list_assessments(limit: int = 100) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, video_name, rubric_name, task_type, model, task_summary
            FROM assessments ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_assessment(assessment_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["result"] = AssessmentResult.model_validate_json(data["result_json"])
    return data

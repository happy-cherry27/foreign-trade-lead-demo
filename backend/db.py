from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .config import DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_lead(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT 'unknown',
                email TEXT NOT NULL DEFAULT 'unknown',
                company TEXT NOT NULL DEFAULT 'unknown',
                country TEXT NOT NULL DEFAULT 'unknown',
                phone TEXT NOT NULL DEFAULT 'unknown',
                product_need TEXT NOT NULL DEFAULT 'unknown',
                budget TEXT NOT NULL DEFAULT 'unknown',
                quantity TEXT NOT NULL DEFAULT 'unknown',
                urgency TEXT NOT NULL DEFAULT 'unknown',
                priority TEXT NOT NULL DEFAULT 'medium',
                follow_up_time TEXT NOT NULL DEFAULT 'unknown',
                lead_score INTEGER NOT NULL DEFAULT 0,
                score_breakdown TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending_review',
                original_email TEXT NOT NULL,
                follow_up_suggestion TEXT NOT NULL DEFAULT '',
                reply_draft TEXT NOT NULL DEFAULT '',
                source_channel TEXT NOT NULL DEFAULT 'manual',
                sync_target TEXT NOT NULL DEFAULT '',
                sync_status TEXT NOT NULL DEFAULT 'not_synced',
                synced_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_extraction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                raw_email TEXT NOT NULL,
                extracted_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT NOT NULL,
                model_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
        migrations = {
            "follow_up_time": "ALTER TABLE leads ADD COLUMN follow_up_time TEXT NOT NULL DEFAULT 'unknown'",
            "lead_score": "ALTER TABLE leads ADD COLUMN lead_score INTEGER NOT NULL DEFAULT 0",
            "score_breakdown": "ALTER TABLE leads ADD COLUMN score_breakdown TEXT NOT NULL DEFAULT '{}'",
            "reply_draft": "ALTER TABLE leads ADD COLUMN reply_draft TEXT NOT NULL DEFAULT ''",
            "source_channel": "ALTER TABLE leads ADD COLUMN source_channel TEXT NOT NULL DEFAULT 'manual'",
            "sync_target": "ALTER TABLE leads ADD COLUMN sync_target TEXT NOT NULL DEFAULT ''",
            "sync_status": "ALTER TABLE leads ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'not_synced'",
            "synced_at": "ALTER TABLE leads ADD COLUMN synced_at TEXT NOT NULL DEFAULT ''",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS review_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                before_json TEXT NOT NULL,
                after_json TEXT NOT NULL,
                reviewer_note TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
            """
        )


def insert_log(conn: sqlite3.Connection, lead_id: int | None, raw_email: str, extracted: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO ai_extraction_logs
        (lead_id, raw_email, extracted_json, confidence, evidence, model_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            raw_email,
            json.dumps(extracted, ensure_ascii=False),
            float(extracted.get("confidence", 0)),
            json.dumps(extracted.get("evidence", []), ensure_ascii=False),
            extracted.get("model_name", "unknown"),
            now_iso(),
        ),
    )


def insert_event(conn: sqlite3.Connection, lead_id: int, event_type: str, title: str, detail: str) -> None:
    conn.execute(
        """
        INSERT INTO lead_events (lead_id, event_type, title, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (lead_id, event_type, title, detail, now_iso()),
    )

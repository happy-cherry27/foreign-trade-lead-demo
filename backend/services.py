from __future__ import annotations

import json
from typing import Any

from .db import get_conn, insert_event, insert_log, now_iso, row_to_lead


def create_lead_record(raw_email: str, extracted: dict[str, Any], source_channel: str = "manual") -> dict[str, Any]:
    created_at = now_iso()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads
            (name, email, company, country, phone, product_need, budget, quantity, urgency, priority,
             follow_up_time, lead_score, score_breakdown, status, original_email, follow_up_suggestion,
             reply_draft, source_channel, sync_target, sync_status, synced_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                extracted.get("name", "unknown"),
                extracted.get("email", "unknown"),
                extracted.get("company", "unknown"),
                extracted.get("country", "unknown"),
                extracted.get("phone", "unknown"),
                extracted.get("product_need", "unknown"),
                extracted.get("budget", "unknown"),
                extracted.get("quantity", "unknown"),
                extracted.get("urgency", "unknown"),
                extracted.get("priority", "medium"),
                extracted.get("follow_up_time", "unknown"),
                int(extracted.get("lead_score", 0)),
                json.dumps(extracted.get("score_breakdown", {}), ensure_ascii=False),
                "pending_review",
                raw_email,
                extracted.get("follow_up_suggestion", ""),
                extracted.get("reply_draft", ""),
                source_channel,
                "",
                "not_synced",
                "",
                created_at,
                created_at,
            ),
        )
        lead_id = int(cursor.lastrowid)
        insert_log(conn, lead_id, raw_email, extracted)
        insert_event(
            conn,
            lead_id,
            "created",
            "Lead saved for human review",
            f"Lead entered pending review from {source_channel} with score {extracted.get('lead_score', 0)}.",
        )
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return row_to_lead(row)

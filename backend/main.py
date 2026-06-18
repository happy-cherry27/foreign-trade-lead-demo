from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import DOCS_DIR, FRONTEND_DIR, SHOW_PICTURES_DIR, allowed_cors_origins
from .db import get_conn, init_db, insert_event, now_iso, row_to_lead
from .extractor import extract_lead
from .integrations.feishu import sync_to_feishu_bitable
from .scoring import build_score
from .schemas import BatchImportRequest, EmailWebhookRequest, ExtractRequest, LeadCreate, ReviewRequest
from .services import create_lead_record


app = FastAPI(
    title="外贸客户邮件线索自动录入与跟进建议系统",
    description="A closed-loop demo for extracting, reviewing, scoring, and syncing foreign trade email leads.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/show_pictures", StaticFiles(directory=SHOW_PICTURES_DIR), name="show_pictures")


init_db()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(DOCS_DIR / "showcase.html")


@app.get("/app")
def app_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/showcase")
def showcase() -> FileResponse:
    return FileResponse(DOCS_DIR / "showcase.html")


@app.get("/showcase/friend")
def friend_showcase() -> FileResponse:
    return FileResponse(DOCS_DIR / "showcase_trade_ai_interaction(1).html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/leads/extract")
def extract_endpoint(payload: ExtractRequest) -> dict[str, Any]:
    return extract_lead(payload.raw_email)


@app.post("/api/leads")
def create_lead(payload: LeadCreate) -> dict[str, Any]:
    return create_lead_record(payload.raw_email, payload.extracted, "manual")


@app.post("/api/webhooks/email")
def email_webhook(payload: EmailWebhookRequest) -> dict[str, Any]:
    raw_email = "\n\n".join(
        part
        for part in [
            f"Subject: {payload.subject}" if payload.subject else "",
            f"From: {payload.sender}" if payload.sender else "",
            payload.body,
        ]
        if part
    )
    extracted = extract_lead(raw_email)
    lead = create_lead_record(raw_email, extracted, f"{payload.source}:{payload.channel}")
    with get_conn() as conn:
        insert_event(
            conn,
            int(lead["id"]),
            "webhook",
            "Email received from webhook",
            f"Accepted email payload from {payload.source} / {payload.channel}.",
        )
    return {"lead": lead, "extracted": extracted}


@app.post("/api/leads/import-batch")
def import_batch(payload: BatchImportRequest) -> dict[str, Any]:
    imported: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for item in payload.emails:
        try:
            raw_email = item.content.strip()
            extracted = extract_lead(raw_email)
            lead = create_lead_record(raw_email, extracted, "batch_import")
            with get_conn() as conn:
                insert_event(
                    conn,
                    int(lead["id"]),
                    "batch_import",
                    "Email imported from batch upload",
                    f"Imported source file: {item.filename}.",
                )
            imported.append({"filename": item.filename, "lead": lead})
        except Exception as exc:  # noqa: BLE001 - return per-file import errors for the UI
            errors.append({"filename": item.filename, "error": str(exc)})
    return {"imported_count": len(imported), "error_count": len(errors), "imported": imported, "errors": errors}


@app.get("/api/leads")
def list_leads(status: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM leads WHERE status = ? ORDER BY lead_score DESC, id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM leads ORDER BY lead_score DESC, id DESC").fetchall()
    return [row_to_lead(row) for row in rows]


@app.get("/api/leads/export.csv")
def export_leads_csv() -> Response:
    columns = {
        "id": "线索ID",
        "name": "客户姓名",
        "email": "邮箱",
        "company": "公司",
        "country": "国家",
        "phone": "电话",
        "product_need": "产品需求",
        "budget": "预算",
        "quantity": "数量",
        "priority": "优先级",
        "lead_score": "线索评分",
        "follow_up_time": "适合跟进时间",
        "status": "审核状态",
        "source_channel": "来源",
        "sync_status": "同步状态",
        "created_at": "创建时间",
    }
    priority_labels = {"high": "高", "medium": "中", "low": "低"}
    status_labels = {"pending_review": "待审核", "confirmed": "已确认", "rejected": "已拒绝"}
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, email, company, country, phone, product_need, budget, quantity,
                   priority, lead_score, follow_up_time, status, created_at, source_channel, sync_status
            FROM leads
            ORDER BY lead_score DESC, id DESC
            """
        ).fetchall()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(columns.values()))
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                label: priority_labels.get(row[column], row[column])
                if column == "priority"
                else status_labels.get(row[column], row[column])
                if column == "status"
                else row[column]
                for column, label in columns.items()
            }
        )

    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="foreign_trade_leads.csv"'},
    )


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


@app.patch("/api/leads/{lead_id}/review")
def review_lead(lead_id: int, payload: ReviewRequest) -> dict[str, Any]:
    allowed_fields = {
        "name",
        "email",
        "company",
        "country",
        "phone",
        "product_need",
        "budget",
        "quantity",
        "urgency",
        "priority",
        "follow_up_time",
        "follow_up_suggestion",
        "reply_draft",
    }
    updates = {key: value for key, value in payload.updates.items() if key in allowed_fields}
    with get_conn() as conn:
        before = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not before:
            raise HTTPException(status_code=404, detail="Lead not found")
        before_json = row_to_lead(before)
        assignments = [f"{field} = ?" for field in updates]
        values = list(updates.values())
        recalculated = {**before_json, **updates}
        recalculated_score, recalculated_breakdown = build_score(recalculated, before_json["original_email"])
        assignments.extend(["lead_score = ?", "score_breakdown = ?"])
        values.extend([recalculated_score, json.dumps(recalculated_breakdown, ensure_ascii=False)])
        assignments.extend(["status = ?", "updated_at = ?"])
        values.extend([payload.action, now_iso(), lead_id])
        conn.execute(f"UPDATE leads SET {', '.join(assignments)} WHERE id = ?", values)
        after = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        after_json = row_to_lead(after)
        conn.execute(
            """
            INSERT INTO review_records
            (lead_id, action, before_json, after_json, reviewer_note, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                payload.action,
                json.dumps(before_json, ensure_ascii=False),
                json.dumps(after_json, ensure_ascii=False),
                payload.reviewer_note,
                now_iso(),
            ),
        )
        insert_event(
            conn,
            lead_id,
            "review",
            f"Human review: {payload.action}",
            payload.reviewer_note or "No reviewer note.",
        )
    return after_json


@app.post("/api/leads/{lead_id}/sync/feishu")
def sync_lead_to_feishu(lead_id: int) -> dict[str, Any]:
    synced_at = now_iso()
    with get_conn() as conn:
        before = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not before:
            raise HTTPException(status_code=404, detail="Lead not found")
        if before["status"] != "confirmed":
            raise HTTPException(status_code=400, detail="Only confirmed leads can be synced to Feishu")
        try:
            sync_result = sync_to_feishu_bitable(row_to_lead(before))
        except HTTPException as exc:
            detail = str(exc.detail)
            conn.execute(
                """
                UPDATE leads
                SET sync_target = ?, sync_status = ?, synced_at = ?, updated_at = ?
                WHERE id = ?
                """,
                ("feishu_bitable", "failed", synced_at, synced_at, lead_id),
            )
            insert_event(conn, lead_id, "sync_failed", "Feishu sync failed", detail)
            failed = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return {
                "target": "feishu_bitable",
                "status": "failed",
                "detail": detail,
                "lead": row_to_lead(failed),
            }
        conn.execute(
            """
            UPDATE leads
            SET sync_target = ?, sync_status = ?, synced_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (sync_result["target"], sync_result["status"], synced_at, synced_at, lead_id),
        )
        insert_event(conn, lead_id, "sync", "Synced to Feishu", sync_result["detail"])
        after = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return {"target": sync_result["target"], "status": sync_result["status"], "lead": row_to_lead(after)}


@app.get("/api/leads/{lead_id}/logs")
def get_logs(lead_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        logs = conn.execute(
            "SELECT * FROM ai_extraction_logs WHERE lead_id = ? ORDER BY id DESC", (lead_id,)
        ).fetchall()
        reviews = conn.execute(
            "SELECT * FROM review_records WHERE lead_id = ? ORDER BY id DESC", (lead_id,)
        ).fetchall()
        events = conn.execute("SELECT * FROM lead_events WHERE lead_id = ? ORDER BY id ASC", (lead_id,)).fetchall()

    timeline = [
        {
            "type": row["event_type"],
            "title": row["title"],
            "detail": row["detail"],
            "at": row["created_at"],
        }
        for row in events
    ]
    if not timeline:
        timeline.append(
            {
                "type": "created",
                "title": "Lead saved for human review",
                "detail": f"Lead #{lead_id} entered pending review with score {lead['lead_score']}.",
                "at": lead["created_at"],
            }
        )
    for row in logs:
        timeline.append(
            {
                "type": "ai_extraction",
                "title": "AI extraction completed",
                "detail": f"{row['model_name']} returned confidence {row['confidence']}.",
                "at": row["created_at"],
            }
        )
    if not any(item["type"] == "review" for item in timeline):
        for row in reviews:
            timeline.append(
                {
                    "type": "review",
                    "title": f"Human review: {row['action']}",
                    "detail": row["reviewer_note"] or "No reviewer note.",
                    "at": row["reviewed_at"],
                }
            )
    timeline.sort(key=lambda item: item["at"])
    return {
        "timeline": timeline,
        "ai_logs": [row_to_lead(row) for row in logs],
        "review_records": [row_to_lead(row) for row in reviews],
    }

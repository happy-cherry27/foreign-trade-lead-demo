from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "leads.db"
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(
    title="外贸客户邮件线索自动录入与跟进建议系统",
    description="A small closed-loop demo for extracting, reviewing, and tracking foreign trade email leads.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ExtractRequest(BaseModel):
    raw_email: str = Field(min_length=10)


class LeadCreate(BaseModel):
    raw_email: str
    extracted: dict[str, Any]


class ReviewRequest(BaseModel):
    action: str = Field(pattern="^(confirmed|rejected)$")
    updates: dict[str, Any] = Field(default_factory=dict)
    reviewer_note: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
                status TEXT NOT NULL DEFAULT 'pending_review',
                original_email TEXT NOT NULL,
                follow_up_suggestion TEXT NOT NULL DEFAULT '',
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
        if "follow_up_time" not in columns:
            conn.execute("ALTER TABLE leads ADD COLUMN follow_up_time TEXT NOT NULL DEFAULT 'unknown'")
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


init_db()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def first_match(patterns: list[str], text: str, default: str = "unknown") -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1) if match.groups() else match.group(0)
            return value.strip(" .,:;")
    return default


def normalize_name(value: str) -> str:
    parts = [part for part in value.split() if "@" not in part]
    return " ".join(parts[:3]) or "unknown"


def normalize_company(value: str) -> str:
    cleaned = re.sub(
        r"\s+(?:in|from)\s+(Germany|United States|USA|Canada|Australia|United Kingdom|UK|France|Italy|Spain|Brazil|India|UAE|Saudi Arabia|Mexico|Netherlands)\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return cleaned.strip(" .,:;") or "unknown"


def infer_country(text: str) -> str:
    countries = [
        "Germany",
        "United States",
        "USA",
        "Canada",
        "Australia",
        "United Kingdom",
        "UK",
        "France",
        "Italy",
        "Spain",
        "Brazil",
        "India",
        "UAE",
        "Saudi Arabia",
        "Mexico",
        "Netherlands",
    ]
    for country in countries:
        if re.search(rf"\b{re.escape(country)}\b", text, re.IGNORECASE):
            return "United States" if country == "USA" else "United Kingdom" if country == "UK" else country
    return "unknown"


def infer_priority(text: str) -> tuple[str, str]:
    lowered = text.lower()
    high_signals = ["urgent", "asap", "immediately", "this week", "deadline", "within 3 days"]
    medium_signals = ["quotation", "quote", "price", "catalog", "sample", "lead time"]
    if any(signal in lowered for signal in high_signals):
        return "high", "Email contains urgent timing signals such as ASAP, deadline, or this week."
    if any(signal in lowered for signal in medium_signals):
        return "medium", "Email asks for quote, price, sample, catalog, or lead time."
    return "low", "Email has limited buying intent signals."


def infer_follow_up_time(priority: str, text: str) -> tuple[str, str]:
    lowered = text.lower()
    if priority == "high":
        if "within 3 days" in lowered or "immediately" in lowered or "asap" in lowered:
            return "same day", "Urgent words indicate the sales team should reply today."
        return "within 24 hours", "High-priority inquiry should be handled within 24 hours."
    if priority == "medium":
        return "within 2 business days", "Buying intent exists, but timing is not critical."
    return "within 3-5 business days", "Inquiry needs qualification before sales invests urgent effort."


def extract_lead(raw_email: str) -> dict[str, Any]:
    text = raw_email.strip()
    email = first_match([r"[\w.+-]+@[\w-]+\.[\w.-]+"], text)
    phone = first_match([r"(\+?\d[\d\s().-]{7,}\d)"], text)
    name = first_match(
        [
            r"(?:Best regards|Regards|Sincerely|Thanks|Thank you),?\s*\n\s*([A-Z][A-Za-z .'-]{1,40})",
            r"(?:I am|I'm|This is)\s+([A-Z][A-Za-z .'-]{1,40})(?:\s+(?:from|at)\b|[,.]|\n)",
            r"Name:\s*([^\n]+)",
        ],
        text,
    )
    name = normalize_name(name) if name != "unknown" else name
    company = first_match(
        [
            r"(?:from|at)\s+([A-Z][A-Za-z0-9&.,\- ]{2,60}?)(?:\s+(?:in|from)\s+[A-Z][A-Za-z ]+|\.|,|\n)",
            r"Company:\s*([^\n]+)",
        ],
        text,
    )
    company = normalize_company(company) if company != "unknown" else company
    product_need = first_match(
        [
            r"(?:interested in|looking for|need|purchase|buy)\s+([A-Za-z0-9,\-\s]{3,80})(?:\.|,|\n)",
            r"(?:quotation for|quote for|price for)\s+([A-Za-z0-9,\-\s]{3,80})(?:\.|,|\n)",
        ],
        text,
    )
    quantity = first_match([r"(\d{2,6}\s*(?:pcs|pieces|units|sets|containers|cartons))"], text)
    budget = first_match(
        [
            r"(?:budget is|budget around|budget:)\s*(\$?[0-9,]+(?:\s*-\s*\$?[0-9,]+)?)",
            r"(\$[0-9,]+(?:\s*-\s*\$[0-9,]+)?)",
        ],
        text,
    )
    country = infer_country(text)
    priority, priority_evidence = infer_priority(text)
    follow_up_time, follow_up_time_evidence = infer_follow_up_time(priority, text)
    urgency = "urgent" if priority == "high" else "normal" if priority == "medium" else "low"

    known_fields = [email, phone, name, company, product_need, quantity, budget, country]
    known_count = sum(1 for value in known_fields if value != "unknown")
    confidence = round(0.35 + known_count / len(known_fields) * 0.55, 2)

    evidence_items = [
        priority_evidence,
        follow_up_time_evidence,
        f"Detected email: {email}" if email != "unknown" else "Email address is missing.",
        f"Detected country: {country}" if country != "unknown" else "Country is missing or implicit.",
        f"Detected product need: {product_need}" if product_need != "unknown" else "Product need is unclear.",
    ]

    follow_up = (
        "Reply within 24 hours with quotation, lead time, and two clarifying questions."
        if priority == "high"
        else "Send product catalog, price range, and ask for quantity/use case."
        if priority == "medium"
        else "Ask for product details and confirm whether there is a purchase timeline."
    )

    return {
        "name": name,
        "email": email,
        "company": company,
        "country": country,
        "phone": phone,
        "product_need": product_need,
        "budget": budget,
        "quantity": quantity,
        "urgency": urgency,
        "priority": priority,
        "follow_up_time": follow_up_time,
        "follow_up_suggestion": follow_up,
        "confidence": confidence,
        "evidence": evidence_items,
        "model_name": "rule-based-mock-extractor-v0.1",
    }


@app.post("/api/leads/extract")
def extract_endpoint(payload: ExtractRequest) -> dict[str, Any]:
    return extract_lead(payload.raw_email)


def row_to_lead(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


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


@app.post("/api/leads")
def create_lead(payload: LeadCreate) -> dict[str, Any]:
    extracted = payload.extracted
    created_at = now_iso()
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO leads
            (name, email, company, country, phone, product_need, budget, quantity, urgency, priority,
             follow_up_time, status, original_email, follow_up_suggestion, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                "pending_review",
                payload.raw_email,
                extracted.get("follow_up_suggestion", ""),
                created_at,
                created_at,
            ),
        )
        lead_id = int(cursor.lastrowid)
        insert_log(conn, lead_id, payload.raw_email, extracted)
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return row_to_lead(row)


@app.get("/api/leads")
def list_leads(status: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if status:
            rows = conn.execute("SELECT * FROM leads WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    return [row_to_lead(row) for row in rows]


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
    }
    updates = {key: value for key, value in payload.updates.items() if key in allowed_fields}
    with get_conn() as conn:
        before = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not before:
            raise HTTPException(status_code=404, detail="Lead not found")
        before_json = row_to_lead(before)
        assignments = [f"{field} = ?" for field in updates]
        values = list(updates.values())
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
    return after_json


@app.get("/api/leads/{lead_id}/logs")
def get_logs(lead_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        logs = conn.execute(
            "SELECT * FROM ai_extraction_logs WHERE lead_id = ? ORDER BY id DESC", (lead_id,)
        ).fetchall()
        reviews = conn.execute(
            "SELECT * FROM review_records WHERE lead_id = ? ORDER BY id DESC", (lead_id,)
        ).fetchall()
    return {
        "ai_logs": [row_to_lead(row) for row in logs],
        "review_records": [row_to_lead(row) for row in reviews],
    }

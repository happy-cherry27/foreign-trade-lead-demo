# Architecture

## Product Positioning

This project is a human-in-the-loop sales operations demo for foreign-trade email inquiries.

It is not trying to replace a full CRM. The core promise is:

```text
Email inquiry -> structured lead -> lead score -> reply draft -> human review -> timeline -> CSV / Feishu / CRM sync
```

## Business Flow

```text
Gmail / IMAP / inquiry inbox
        |
        v
n8n Email Trigger
        |
        v
POST /api/webhooks/email
        |
        v
Rule-based extractor
        |
        +--> field_evidence
        +--> lead_score + score_breakdown
        +--> reply_draft
        +--> qualification_questions
        |
        v
pending_review
        |
        v
Human confirms or rejects
        |
        v
Timeline + CSV export + Feishu sync
```

## Backend Modules

```text
backend/main.py                  FastAPI routes and request orchestration
backend/config.py                Paths and runtime constants
backend/schemas.py               Pydantic request models
backend/db.py                    SQLite connection, table creation, events, logs
backend/extractor.py             Email extraction and field evidence
backend/scoring.py               Transparent lead scoring rules
backend/followup.py              Reply draft and qualification questions
backend/integrations/feishu.py   Feishu Bitable sync adapter with mock fallback
backend/services.py              Lead creation service
```

## Why n8n and Webhook

n8n is the workflow layer. It listens to Gmail, IMAP, or another inbox and sends the email content to this app.

The webhook is the app's inbound integration point:

```text
POST /api/webhooks/email
```

Recommended n8n mapping:

| n8n email field | App field |
| --- | --- |
| subject | subject |
| from / sender | sender |
| text plain / text html | body |
| fixed value: n8n | source |
| fixed value: gmail or imap | channel |

This keeps the lead system independent from a specific mailbox provider.

## Feishu Sync Strategy

The Feishu sync endpoint is:

```text
POST /api/leads/{id}/sync/feishu
```

By default it uses mock sync so the demo is stable. If these environment variables are configured, the adapter attempts a real Feishu Bitable OpenAPI write:

```text
FEISHU_APP_ID
FEISHU_APP_SECRET
FEISHU_BITABLE_APP_TOKEN
FEISHU_BITABLE_TABLE_ID
```

## Lead Scoring

The score is a transparent rule-based score, not a black-box prediction model.

Current dimensions:

- urgency
- commercial value
- contactability
- product clarity
- market fit
- risk penalty

This is appropriate for a demo because interviewers can see exactly why a lead is ranked higher.

## Audit Trail

The system keeps three layers:

- `ai_extraction_logs`: raw AI/mock extraction result
- `review_records`: before/after human review data
- `lead_events`: user-friendly timeline events

The UI presents `lead_events` plus extraction and review history as a timeline.

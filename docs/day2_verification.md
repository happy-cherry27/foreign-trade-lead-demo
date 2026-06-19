# Day 2 Verification

## Goal

Turn raw foreign-trade customer emails into structured leads, keep AI extraction evidence, save logs, and support human review.

## Changes completed on 2026-06-17

- Added `follow_up_time` to the lead data model, API response, SQLite table, and review form.
- Added a small SQLite migration in `init_db()` so the existing `leads.db` can be reused.
- Added follow-up timing inference:
  - high priority with immediate timing signals: `same day`
  - high priority without same-day trigger: `within 24 hours`
  - medium priority: `within 2 business days`
  - low priority: `within 3-5 business days`
- Included follow-up timing evidence in extraction logs.

## Actual checks

- `python -m compileall backend` passed.
- Three sample emails were checked through `extract_lead()`:
  - `email_a_complete.txt`: high priority, `within 24 hours`
  - `email_b_missing_budget.txt`: medium priority, missing budget and phone stay `unknown`
  - `email_c_urgent.txt`: high priority, `same day`
- API loop passed with FastAPI `TestClient`:
  - `GET /health` returned `200`
  - `POST /api/leads/extract` returned `priority=high`, `follow_up_time=same day`
  - `POST /api/leads` saved a pending-review lead
  - `PATCH /api/leads/{id}/review` changed status to confirmed
  - `GET /api/leads/{id}/logs` returned 1 AI log and 1 review record

## Day 2 interview sentence

我没有让 AI 直接改数据库或直接发消息，而是让它先生成结构化建议，再进入人工审核流程。这样更符合外贸客户关系比较敏感的场景。

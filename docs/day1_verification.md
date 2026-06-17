# Day 1 Verification

## Minimum checks

- `GET /health` returns `{"status":"ok"}`.
- `POST /api/leads/extract` returns structured fields from an email.
- `POST /api/leads` saves a lead.
- `GET /api/leads` returns saved leads.
- The browser page can complete extract -> save -> select detail.

## 2026-06-16 actual verification

- Python compile check passed: `python -m compileall backend`.
- API loop passed: health -> extract -> save -> review -> logs.
- Local service started on `http://127.0.0.1:8000`.
- `GET /health` returned `ok`.
- `GET /` returned HTTP `200`.

## Known environment note

PowerShell prints an old Anaconda profile warning about `D:\anaconda3\Scripts\conda.exe`, but the app commands still run successfully. This is an environment-profile issue, not a demo app failure.

## Interview sentence

我先没有急着接 N8N 或邮箱，而是先把核心数据模型和后端接口搭起来，因为真实业务系统首先要保证数据能稳定落库。

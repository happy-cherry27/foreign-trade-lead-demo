# Day 4 Verification

## Goal

Turn the runnable demo into a presentable project artifact: add CSV export, document the project clearly, add a minimal Dockerfile, and verify the core loop still works.

## Changes completed on 2026-06-17

- Added `GET /api/leads/export.csv`.
- Added a front-end `导出 CSV` button.
- Added `Dockerfile`.
- Expanded `README.md` with:
  - project background
  - business pain point
  - core flow
  - feature list
  - data tables
  - API list
  - local startup
  - Docker startup
  - demo flow
  - project boundaries
  - future expansion
- Restarted the local FastAPI service so the browser uses the latest Day4 code.

## Actual checks

- `python -m compileall backend` passed.
- `GET /api/leads/export.csv` returned `200`.
- CSV header includes:
  - `id`
  - `name`
  - `email`
  - `company`
  - `country`
  - `product_need`
  - `priority`
  - `follow_up_time`
  - `status`
- API loop passed:
  - extract missing-field sample
  - save lead
  - confirm lead
  - read AI log and review record
- Browser check passed:
  - page loaded at `http://127.0.0.1:8000/`
  - `导出 CSV` button is visible
  - lead list renders clean sample names
- Docker CLI exists locally. Full image build was not run because the local Docker config produced an access warning; the Dockerfile and commands are documented for later build verification.

## Day 4 interview sentence

这版 demo 先完成核心闭环，后续如果接入公司真实系统，可以把邮箱 Webhook 或 N8N 放在输入端，把飞书多维表格或正式 CRM 放在输出端。

# Day 7 Interview Readiness

## Goal

Make the project easier to explain in a technical interview:

- clarify the difference between n8n, webhook, and Feishu API
- make lead scoring understandable
- add qualification questions for missing fields
- provide a real Feishu OpenAPI integration skeleton while keeping mock sync as the default

## Changes completed on 2026-06-18

- Added `qualification_questions` to extraction results.
- Displayed qualification questions in the extraction result panel.
- Added Feishu environment variables to `.env.example`.
- Added a `sync_to_feishu_bitable` skeleton using Feishu tenant token and Bitable record creation.
- Kept mock sync as the default when Feishu variables are not configured.
- Expanded README with a real business architecture diagram, n8n field mapping, and interview explanation.

## Interview sentence

这版的飞书同步默认走 mock，是为了保证 Demo 稳定；但后端已经有真实飞书 OpenAPI 的切换点，配置环境变量后就可以从 mock 切到真实多维表格写入。

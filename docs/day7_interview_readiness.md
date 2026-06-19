# Day 7 Interview Readiness

## Goal

Make the project easier to explain in a technical interview:

- clarify the difference between n8n, webhook, and Feishu API
- make lead scoring understandable
- add qualification questions for missing fields
- provide a real Feishu OpenAPI integration path with a local demo fallback

## Changes completed on 2026-06-18

- Added `qualification_questions` to extraction results.
- Displayed qualification questions in the extraction result panel.
- Added Feishu environment variables to `.env.example`.
- Added a `sync_to_feishu_bitable` skeleton using Feishu tenant token and Bitable record creation.
- Kept a local demo fallback when Feishu variables are not configured.
- Expanded README with a real business architecture diagram, n8n field mapping, and interview explanation.

## Interview sentence

这版的飞书同步保留本地演示兜底，是为了保证 Demo 稳定；后端已经有真实飞书 OpenAPI 路径，配置环境变量后就可以写入真实多维表格。

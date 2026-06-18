# Day 9 Sync Failure and CORS Hardening

## Goal

Address the remaining self-check items that matter for interview follow-up:

- CORS should be configurable instead of hard-coded
- real Feishu sync failures should be visible in timeline
- failed sync should be retry-friendly

## Changes completed on 2026-06-18

- Added `CORS_ALLOW_ORIGINS` environment variable support.
- Added sync failure handling in `/api/leads/{id}/sync/feishu`.
- When real Feishu sync fails, the lead is updated with `sync_status = failed`.
- Added a `sync_failed` timeline event with the failure detail.
- Documented retry behavior in README.

## Interview sentence

生产环境里，飞书同步失败不会静默丢失；系统会把状态标为 failed，并把失败原因写进 timeline，修正配置后可以再次点击同步重试。

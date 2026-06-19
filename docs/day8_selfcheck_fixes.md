# Day 8 Self-check Fixes

## Goal

Fix the three highest-impact issues found during self-check:

- external email text should be rendered safely
- only confirmed leads should sync downstream
- lead score should update after human edits

## Changes completed on 2026-06-18

- Replaced dynamic `innerHTML` rendering in `frontend/app.js` with DOM creation and `textContent`.
- Blocked Feishu sync unless `status == confirmed`.
- Recalculated `lead_score` and `score_breakdown` after review updates.

## Verification

- `python -m compileall backend` passed.
- `rg innerHTML frontend/app.js` returned no matches.
- Pending review lead sync returns `400 Only confirmed leads can be synced to Feishu`.
- Review updates can increase score, verified from `19` to `48` after adding budget, quantity, and phone.
- Confirmed urgent lead can still sync to Feishu and writes timeline events.

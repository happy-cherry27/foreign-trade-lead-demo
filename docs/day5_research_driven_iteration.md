# Day 5 Research-driven Iteration

## Goal

Apply the full-web research findings to upgrade the demo from a basic email parser into a more credible sales operations loop.

## Changes completed on 2026-06-18

- Added field-level evidence to extraction results.
- Added `lead_score` and `score_breakdown`.
- Added English `reply_draft`.
- Persisted the new score and reply fields in SQLite.
- Sorted leads by score before id.
- Added CSV export column for lead score.
- Replaced raw JSON log display with a human-readable timeline.
- Updated the front-end extraction panel with score summary, scoring breakdown, next actions, field evidence cards, and reply draft.
- Updated README with the research-driven product positioning.

## Interview sentence

这次迭代不是单纯多加字段，而是把系统从“邮件解析 Demo”升级成“可解释、可排序、可行动、可追责的销售运营闭环”。

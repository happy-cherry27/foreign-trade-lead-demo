# Day 3 Verification

## Goal

Make the browser demo flow smoother: choose a sample email, extract a lead, save it, review it, and inspect logs from the page.

## Changes completed on 2026-06-17

- Added three front-end sample buttons:
  - complete inquiry
  - missing-field inquiry
  - urgent inquiry
- Improved extraction quality for demo-visible fields:
  - prevented customer names from swallowing the next email line
  - removed country phrases from company names
  - tightened budget extraction so it keeps only the amount
- Added review success status text after confirming or rejecting a lead.

## Actual browser walkthrough

- Opened `http://127.0.0.1:8000/` in the in-app browser.
- Clicked the urgent sample.
- Extracted a clean urgent lead:
  - name: `Daniel Smith`
  - company: `NorthPeak Supplies`
  - country: `Canada`
  - priority: `high`
  - follow-up time: `same day`
  - budget: `unknown`
- Saved the lead and confirmed that the detail form auto-filled.
- Confirmed the lead and verified:
  - status changed to confirmed
  - review status text appeared
  - AI extraction log and review record were visible in the log panel

## Notes

The local `leads.db` still contains older test records from before the extractor cleanup. New records use the corrected extraction rules. Before recording or presenting the final demo, reset or clean the local demo database so the list starts from clean examples.

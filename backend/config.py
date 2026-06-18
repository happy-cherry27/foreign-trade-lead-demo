from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "leads.db"))
FRONTEND_DIR = BASE_DIR / "frontend"
DOCS_DIR = BASE_DIR / "docs"
SHOW_PICTURES_DIR = BASE_DIR / "show_pictures"


def allowed_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

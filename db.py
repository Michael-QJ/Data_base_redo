"""Shared Railway Postgres connection helpers."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def load_database_url() -> str:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        env_path = ROOT / ".env"
        if env_path.exists():
            first_line = env_path.read_text(encoding="utf-8").strip().splitlines()
            first = first_line[0].strip() if first_line else ""
            if first.startswith("postgresql://") or first.startswith("postgres://"):
                url = first
    if not url:
        raise RuntimeError(
            "Missing DATABASE_URL. Set it in .env or the Railway service variables."
        )
    if "sslmode=" not in url and "railway.internal" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    return url

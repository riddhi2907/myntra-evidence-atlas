"""
Credential lookup, in the order that works both locally and on Streamlit
Community Cloud.

Phase 2's clients read keys via `dotenv_values(ENV_FILE)` only, which works
on a laptop and fails silently on a host that has no .env file. This looks
in three places instead -- Streamlit's secrets manager first (how the
deployed app gets its keys), then the process environment, then a local
.env -- so the same code path runs in both places.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CODEBOOK_JSON = DATA_DIR / "codebook.json"
THEMES_JSON = DATA_DIR / "themes.json"

_ENV_FILE = ROOT / ".env"
_dotenv_cache: dict | None = None


def _dotenv() -> dict:
    global _dotenv_cache
    if _dotenv_cache is None:
        _dotenv_cache = dotenv_values(_ENV_FILE) if _ENV_FILE.exists() else {}
    return _dotenv_cache


def get_key(*names: str) -> str | None:
    """First non-empty value for any of `names`, checked across all three
    sources. Multiple names because the two upstream phases spell some keys
    differently (GROK_API_KEY vs GROQ_API_KEY, gemini-api-key vs GEMINI_API_KEY)."""
    try:
        import streamlit as st

        for name in names:
            try:
                value = st.secrets.get(name)
            except Exception:
                value = None
            if value:
                return str(value)
    except Exception:
        pass

    for name in names:
        value = os.environ.get(name) or _dotenv().get(name)
        if value:
            return str(value)
    return None


def gemini_key() -> str | None:
    return get_key("GEMINI_API_KEY", "gemini-api-key")


def youtube_key() -> str | None:
    return get_key("YOUTUBE_API_KEY")


def groq_key() -> str | None:
    # Phase 2's .env spells this GROK_API_KEY though the key itself is a Groq
    # (groq.com) key, not xAI's -- both spellings are accepted so an existing
    # .env keeps working.
    return get_key("GROQ_API_KEY", "GROK_API_KEY")

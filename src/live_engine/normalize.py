"""
Normalization -- ported from phase1_collection/src/myntra_research/normalization.py
and models.py, trimmed to what a 10-record live run needs.

Same rules as Phase 1, deliberately: collapse whitespace, keep punctuation
and emoji, never sentiment-clean, never fabricate a date. Usernames are
hashed before they leave this module -- the live demo shows real public
text but never a real handle.

Dropped vs. Phase 1: the full EvidenceRecord dataclass (30+ fields for
provenance/raw-file references), RawWriter, and run metadata. A live run
writes nothing to disk, so `LiveRecord` carries only what the classifier
and the UI actually read.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Union

_WHITESPACE_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def normalize_date(value: Union[str, int, float, datetime, None]) -> Optional[str]:
    """Best-effort ISO-8601 UTC. Returns None rather than fabricating a date."""
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    if isinstance(value, (int, float)):
        # epoch seconds (YouTube/Reddit style) vs. milliseconds
        ts = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(value, fmt)
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except ValueError:
                continue
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            return None

    return None


def hash_author(author_identifier: Optional[str]) -> Optional[str]:
    """Anonymize handles before they leave the collector. Never identifies real people."""
    if not author_identifier:
        return None
    return hashlib.sha256(author_identifier.strip().lower().encode("utf-8")).hexdigest()[:16]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LiveRecord:
    """The one schema every source normalizes into -- the live-run analogue of
    Phase 1's EvidenceRecord, cut to the fields a 10-record demo uses."""

    evidence_id: str
    source: str          # app_store | google_play | youtube | reddit
    source_type: str     # app_review | video_comment | forum_post
    text: str
    url: Optional[str] = None
    author_id_hash: Optional[str] = None
    published_at: Optional[str] = None
    rating: Optional[float] = None
    query_used: Optional[str] = None
    collected_at: str = field(default_factory=utc_now_iso)
    relevance_score: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_evidence_id(source: str, source_item_id: str) -> str:
    """Stable ID from source + the source's own item id -- same construction as
    Phase 1's dedup key, so a live record and a corpus record for the same item
    would collide rather than double-count."""
    return hashlib.sha256(f"{source}:{source_item_id}".encode("utf-8")).hexdigest()[:24]

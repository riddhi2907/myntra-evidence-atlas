"""
Post-response validation -- ported from
phase2_analysis/src/myntra_analysis/validation.py, extended to cover the
live engine's `theme_matches`.

This is the layer that makes the output trustworthy rather than merely
plausible, and it is worth surfacing in the UI: every quote the model
produces is checked to be a verbatim substring of the record it came from.
A model that paraphrases a quote is a model that may be paraphrasing the
finding too, so an unverifiable quote is either dropped or has its
confidence halved and its quote blanked -- never silently kept.

Quotes appear in four places now: journey_signals, event_timeline,
future_purchase_relevance, and theme_matches.

The strictest rule is on the two claims that assert something about *future*
behavior or about a corpus-level theme:
  - future_purchase_relevance direct/indirect without a verifiable quote is
    downgraded to "unclear" (Phase 2 behaviour, unchanged).
  - a theme_match without a verifiable quote is DROPPED outright. There is no
    weaker version of "this record is evidence for T3" to fall back to.
"""

from __future__ import annotations

import re

VALID_THEME_IDS = {f"T{i}" for i in range(1, 13)}


# Typographic variants the model reproduces inconsistently: a curly apostrophe
# copied back as a straight one is the same quote, not a paraphrase. Folding
# these removes false negatives without loosening the check -- the words still
# have to match exactly, in order, character for character.
_PUNCT_FOLD = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "–": "-", "—": "-", "‒": "-", "−": "-",
    " ": " ", "​": "", "﻿": "",
})


# Reddit selftext is markdown. A post containing `**the correct product was
# delivered.**` is quoted back by the model as the rendered text, without the
# asterisks -- that's the model reading what a human would read, not a
# paraphrase, and failing it loses real evidence on every bolded Reddit post.
# Emphasis markers are stripped from both sides before comparison. The source
# text itself is left untouched: what the UI shows is what the source says.
_EMPHASIS_RE = re.compile(r"[*_]+")


def normalize_for_match(s: str) -> str:
    folded = _EMPHASIS_RE.sub("", (s or "").translate(_PUNCT_FOLD))
    return re.sub(r"\s+", " ", folded).strip().lower()


def quote_is_verbatim(quote: str, source_text: str) -> bool:
    if not quote:
        return False
    return normalize_for_match(quote) in normalize_for_match(source_text)


def validate_result(result: dict, source_text: str) -> tuple[dict, list[str]]:
    """Returns (possibly-modified result, list of validation issue strings)."""
    issues: list[str] = []

    # journey_signals -- keep, but flag and halve confidence on a bad quote
    kept_signals = []
    for sig in result.get("journey_signals") or []:
        if quote_is_verbatim(sig.get("quote", ""), source_text):
            kept_signals.append(sig)
        else:
            issues.append(
                f"journey_signal '{sig.get('stage')}': quote not verbatim -- flagged, confidence halved"
            )
            sig = dict(sig)
            sig["confidence"] = sig.get("confidence", 0.5) * 0.5
            sig["quote"] = ""
            kept_signals.append(sig)
    result["journey_signals"] = kept_signals

    # event_timeline -- same treatment, quote blanked
    kept_events = []
    for ev in result.get("event_timeline") or []:
        if quote_is_verbatim(ev.get("quote", ""), source_text):
            kept_events.append(ev)
        else:
            issues.append(f"event_timeline '{ev.get('event')}': quote not verbatim -- flagged")
            ev = dict(ev)
            ev["quote"] = ""
            kept_events.append(ev)
    result["event_timeline"] = kept_events

    # future_purchase_relevance -- mandatory quote for direct/indirect
    fpr = result.get("future_purchase_relevance") or {}
    level = fpr.get("level")
    if level in ("direct", "indirect") and not quote_is_verbatim(fpr.get("quote", ""), source_text):
        issues.append(
            f"future_purchase_relevance level='{level}' had no verifiable quote -- downgraded to 'unclear'"
        )
        fpr = dict(fpr)
        fpr["level"] = "unclear"
        fpr["quote"] = ""
        fpr["confidence"] = min(fpr.get("confidence", 0.5), 0.5)
        result["future_purchase_relevance"] = fpr

    # theme_matches -- dropped outright on a bad quote or an invented theme id
    kept_themes = []
    for tm in result.get("theme_matches") or []:
        tid = tm.get("theme_id")
        if tid not in VALID_THEME_IDS:
            issues.append(f"theme_match '{tid}': not in the locked T1-T12 set -- dropped")
            continue
        if not quote_is_verbatim(tm.get("quote", ""), source_text):
            issues.append(f"theme_match '{tid}': quote not verbatim -- dropped (no weaker fallback)")
            continue
        kept_themes.append(tm)
    result["theme_matches"] = kept_themes

    return result, issues


def validate_batch_response(sent_ids: list[str], results: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """Returns (evidence_id -> result, id-level issues). Guards against the model
    dropping a record or inventing an id, both of which would otherwise show up
    as a silently short results table."""
    issues: list[str] = []
    by_id = {r["evidence_id"]: r for r in results if r.get("evidence_id")}

    sent_set = set(sent_ids)
    missing = sent_set - set(by_id)
    extra = set(by_id) - sent_set

    if missing:
        issues.append(f"{len(missing)} record(s) missing from the model response")
    if extra:
        issues.append(f"{len(extra)} unexpected id(s) in the response -- dropped, not sent by us")
        for eid in extra:
            del by_id[eid]

    return by_id, issues

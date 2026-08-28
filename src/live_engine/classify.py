"""
The classification call -- Gemini structured output, one batch for all 10
records.

Ported from phase2_analysis/src/myntra_analysis/gemini_client.py with two
changes:

  1. `theme_matches` added to the response schema (see prompt.py rule 14).
  2. The multi-provider registry (Gemini + Groq + OpenRouter, split by
     evidence_id hash across free-tier quotas) is gone. That existed to push
     16,917 records through free tiers without hitting a daily cap; ten
     records is one call, so there is no hash-splitting. Groq survives as a
     plain fallback -- not for throughput, but because this single call is the
     whole demo: a free-tier 429 on the grader's click would otherwise mean a
     red box and nothing else.

Batching is also gone for the same reason: Phase 2 packed records to a 6,000
character budget, and ten selected records fit inside a single call.
"""

from __future__ import annotations

import json
import time
from typing import Optional

from live_engine.config import gemini_key, groq_key
from live_engine.normalize import LiveRecord

# gemini-flash-lite is what Phase 2's full-corpus run used: the higher-tier
# flash model has a 20 request/day free tier, too low to be clickable.
MODEL = "gemini-flash-lite-latest"

# Fallback provider, only reached if Gemini fails twice. Same model Phase 2
# used as its second free-tier quota.
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_SENTIMENT_ENUM = ["positive", "negative", "neutral", "mixed"]

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "evidence_id": {"type": "STRING"},

                    "evidence_role": {
                        "type": "STRING",
                        "enum": [
                            "direct_purchase_decision", "indirect_future_purchase",
                            "post_purchase_learning", "general_feedback", "irrelevant",
                        ],
                    },
                    "evidence_role_confidence": {"type": "NUMBER"},

                    "sentiment": {"type": "STRING", "enum": _SENTIMENT_ENUM},
                    "sentiment_confidence": {"type": "NUMBER"},

                    "event_timeline": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "event": {"type": "STRING"},
                                "relative_time": {
                                    "type": "STRING",
                                    "enum": ["past", "ongoing", "anticipated", "unspecified"],
                                },
                                "quote": {"type": "STRING"},
                            },
                            "required": ["event", "relative_time", "quote"],
                        },
                    },

                    "journey_stage": {
                        "type": "STRING",
                        "enum": [
                            "discovery", "evaluation", "wishlist_save", "hesitation",
                            "purchase", "delivery", "trial_use", "return_exchange",
                            "post_purchase_reflection", "unclear",
                        ],
                    },
                    "journey_stage_confidence": {"type": "NUMBER"},

                    "journey_signals": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "stage": {
                                    "type": "STRING",
                                    "enum": [
                                        "wishlist_motivation", "purchase_barrier", "uncertainty",
                                        "purchase_postponement", "comparison", "external_information",
                                    ],
                                },
                                "confidence": {"type": "NUMBER"},
                                "quote": {"type": "STRING"},
                            },
                            "required": ["stage", "confidence", "quote"],
                        },
                    },

                    "factor_tags": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "factor": {"type": "STRING"},
                                "sentiment": {"type": "STRING", "enum": _SENTIMENT_ENUM},
                                "confidence": {"type": "NUMBER"},
                            },
                            "required": ["factor", "sentiment", "confidence"],
                        },
                    },

                    "wishlist_role": {
                        "type": "STRING",
                        "enum": [
                            "price_tracking", "style_inspiration", "purchase_queue",
                            "gift_planning", "comparison_shortlist", "unclear",
                        ],
                    },
                    "wishlist_role_confidence": {"type": "NUMBER"},

                    "purchase_intent": {
                        "type": "STRING",
                        "enum": ["genuine_intent", "consideration", "bookmarking", "inspiration", "unclear"],
                    },
                    "purchase_intent_confidence": {"type": "NUMBER"},

                    "purchase_outcome": {
                        "type": "STRING",
                        "enum": ["purchased", "delayed", "abandoned", "alternative_chosen", "unknown"],
                    },
                    "purchase_outcome_confidence": {"type": "NUMBER"},

                    "post_purchase": {
                        "type": "OBJECT",
                        "properties": {
                            "occurred": {"type": "BOOLEAN"},
                            "issues": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "type": {
                                            "type": "STRING",
                                            "enum": [
                                                "delivery_problem", "fit_quality_problem",
                                                "customer_service_problem", "wrong_item",
                                                "authenticity_problem", "other",
                                            ],
                                        },
                                        "confidence": {"type": "NUMBER"},
                                    },
                                    "required": ["type", "confidence"],
                                },
                            },
                            "trust_damage": {"type": "BOOLEAN"},
                            "trust_damage_confidence": {"type": "NUMBER"},
                        },
                        "required": ["occurred", "issues", "trust_damage", "trust_damage_confidence"],
                    },

                    "future_purchase_relevance": {
                        "type": "OBJECT",
                        "properties": {
                            "level": {"type": "STRING", "enum": ["direct", "indirect", "none", "unclear"]},
                            "confidence": {"type": "NUMBER"},
                            "quote": {"type": "STRING"},
                        },
                        "required": ["level", "confidence", "quote"],
                    },

                    "external_research": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "channel": {"type": "STRING"},
                                "confidence": {"type": "NUMBER"},
                            },
                            "required": ["channel", "confidence"],
                        },
                    },

                    # --- live-engine addition (prompt.py rule 14) ---
                    "theme_matches": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "theme_id": {
                                    "type": "STRING",
                                    "enum": [f"T{i}" for i in range(1, 13)],
                                },
                                "confidence": {"type": "NUMBER"},
                                "quote": {"type": "STRING"},
                            },
                            "required": ["theme_id", "confidence", "quote"],
                        },
                    },

                    "segment_hints": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "notes": {"type": "STRING"},
                },
                "required": [
                    "evidence_id", "evidence_role", "evidence_role_confidence",
                    "sentiment", "sentiment_confidence", "event_timeline",
                    "journey_stage", "journey_stage_confidence", "journey_signals",
                    "factor_tags", "wishlist_role", "wishlist_role_confidence",
                    "purchase_intent", "purchase_intent_confidence",
                    "purchase_outcome", "purchase_outcome_confidence",
                    "post_purchase", "future_purchase_relevance", "external_research",
                    "theme_matches", "segment_hints",
                ],
            },
        }
    },
    "required": ["results"],
}


class ClassificationError(RuntimeError):
    pass


def build_batch_payload(records: list[LiveRecord]) -> str:
    """Only evidence_id and text go to the model. Source, rating, URL and the
    search query that surfaced the record are deliberately withheld -- prompt
    rule 11 forbids using retrieval provenance as evidence, and the cleanest
    way to enforce that is not to send it."""
    return json.dumps(
        [{"evidence_id": r.evidence_id, "text": r.text} for r in records],
        ensure_ascii=False,
    )


def _classify_gemini(batch_json: str, system_prompt: str, key: str) -> list[dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120_000))
    response = client.models.generate_content(
        model=MODEL,
        contents=batch_json,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0,
        ),
    )
    return json.loads(response.text)["results"]


def _classify_groq(batch_json: str, system_prompt: str, key: str) -> list[dict]:
    """Fallback provider. Groq's API is OpenAI-compatible, and it only offers
    json_object mode rather than a strict schema -- so the schema is embedded in
    the instruction text and validate.py is what actually enforces correctness.
    That's fine here: validate.py was written to be defensive about any
    provider's output, not to trust Gemini's schema enforcement.

    Ported from phase2_analysis/src/myntra_analysis/grok_client.py, which used
    Groq for exactly this reason (a second independent free-tier quota).
    """
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=GROQ_BASE_URL, timeout=150.0)
    instruction = (
        f"{system_prompt}\n\nRespond with a single JSON object matching EXACTLY this JSON schema "
        "(every property listed as required MUST be present on every result, including every "
        "confidence field and every nested object's fields -- do not omit any, do not flatten "
        "nested objects into strings):\n\n" + json.dumps(RESPONSE_SCHEMA, separators=(",", ":"))
    )
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": instruction}, {"role": "user", "content": batch_json}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)["results"]


def _is_transient(e: Exception) -> bool:
    """Rate limits and upstream hiccups are worth one retry; a bad key or a
    malformed request is not."""
    msg = f"{e}".lower()
    return any(t in msg for t in ("429", "resource_exhausted", "rate limit", "503", "unavailable", "500", "timeout", "deadline"))


def classify(records: list[LiveRecord], system_prompt: str, api_key: Optional[str] = None) -> tuple[list[dict], str]:
    """One structured-output call for the whole batch. Returns
    (results, model_used) -- the caller reports which model actually ran, since
    a fallback means the Audit tab's provenance would otherwise be wrong.

    Gemini is tried twice (a free-tier 429 on the first click is the realistic
    failure mode and it usually clears), then Groq if a key is configured. The
    whole demo hangs off this one call, so a red box with no results is worth
    ~20 lines to avoid.
    """
    batch_json = build_batch_payload(records)
    gkey = api_key or gemini_key()
    attempts: list[str] = []

    if gkey:
        for attempt in range(2):
            try:
                return _classify_gemini(batch_json, system_prompt, gkey), MODEL
            except Exception as e:
                attempts.append(f"{MODEL} attempt {attempt + 1}: {type(e).__name__}: {e}")
                if attempt == 0 and _is_transient(e):
                    time.sleep(3.0)
                    continue
                break
    else:
        attempts.append("no Gemini API key configured")

    qkey = groq_key()
    if qkey:
        try:
            return _classify_groq(batch_json, system_prompt, qkey), f"{GROQ_MODEL} (fallback)"
        except Exception as e:
            attempts.append(f"{GROQ_MODEL} fallback: {type(e).__name__}: {e}")

    if not gkey and not qkey:
        raise ClassificationError(
            "No classifier API key configured. Set GEMINI_API_KEY (or GROQ_API_KEY) in "
            "Streamlit secrets, the environment, or a local .env file."
        )
    raise ClassificationError("Classification failed. " + " | ".join(attempts))

"""
System prompt for the live classification pass.

This is Phase 2's prompt (`phase2_analysis/src/myntra_analysis/prompt.py`,
prompt_version v1.1, codebook v1.1) reused verbatim -- rules 1-13 are
unchanged, because the whole point of the live engine is to show the *same*
classifier the static analysis ran on 16,917 records working on records
fetched seconds ago. Changing the rules here would make the live output
non-comparable with the corpus findings.

One rule is added: rule 14, theme mapping. Phase 2 derived themes T1-T12 by
clustering thousands of classified records; ten live records cannot re-derive
clusters, and pretending otherwise would be dishonest. Instead each live
record is mapped *onto* the locked T1-T12 -- so the live run demonstrates the
existing theme framework catching new evidence, rather than inventing a
fresh, statistically meaningless set of themes from n=10.

Metric-node (M1-M6) assignment is NOT done here: it is computed
deterministically from the extracted fields by metric_nodes.py, so the model
never gets to assert a metric connection the data doesn't support.
"""

from __future__ import annotations

import json

from live_engine.config import CODEBOOK_JSON, THEMES_JSON

PROMPT_VERSION = "v1.1-live"

# --- Rules 1-13: Phase 2's INSTRUCTIONS, unchanged. ---
INSTRUCTIONS = """You are analyzing user-generated text (app reviews, forum comments, video comments, web content) about Myntra/AJIO wishlist and purchase behavior, for a product research project on wishlist-to-purchase conversion.

For each record given, extract structured signals. Follow these rules strictly:

1. evidence_role: classify into exactly one of five roles -- do NOT use a simple relevant/irrelevant split.
   - direct_purchase_decision: about deciding whether/when/what to buy for a not-yet-purchased item, or a decision in progress.
   - indirect_future_purchase: mainly about something else (often post-purchase), but the text EXPLICITLY connects it to future purchase/shopping behavior or trust.
   - post_purchase_learning: a post-purchase account (delivery, fit, quality, return, exchange, customer service) with NO explicit statement about future purchase impact.
   - general_feedback: broad product/app/service commentary not tied to a specific decision or a clear post-purchase account.
   - irrelevant: not about Myntra/AJIO shopping at all.
   Do NOT force post-purchase complaints into "direct_purchase_decision" -- use post_purchase_learning or indirect_future_purchase instead, per the future_purchase_relevance rule below.

2. journey_stage is the PRIMARY chronological indicator of where this record sits in the shopping journey -- AT MOST ONE funnel-position label (discovery, evaluation, wishlist_save, hesitation, purchase, delivery, trial_use, return_exchange, post_purchase_reflection, unclear). Only set a specific stage when the text clearly supports it; otherwise "unclear". journey_stage does NOT include "comparison" -- comparison behavior belongs only in journey_signals (rule 3, which captures SECONDARY behaviors/signals alongside the primary stage), never here, so it is not double-counted.

3. journey_signals: zero or more RQ1-6 behavioral signals (wishlist_motivation, purchase_barrier, uncertainty, purchase_postponement, comparison, external_information), independent of journey_stage -- a record can have one stage and several signals, or a stage with no signals, or signals with an unclear stage. Each entry's "quote" MUST be an exact, verbatim substring copied from the record's text. If you cannot quote it verbatim, do not include the signal.

4. factor_tags: zero or more entries from the codebook's fit_size/styling/price/reviews/occasion/social_validation (RQ7) OR the emergent factors (quality, delivery, returns, trust, availability, customer_service, authenticity), each with its OWN sentiment (aspect-level) -- e.g. positive on styling and negative on price in the same record. This is separate from the record-level "sentiment", which is a coarse overall read and should be treated as secondary, not the main output. Do NOT tag a factor just because it sounds like something a search query would target -- only tag what the text itself actually discusses.

5. wishlist_role vs. purchase_intent -- these are related but NOT the same field:
   - wishlist_role: WHY something was saved (price_tracking, style_inspiration, purchase_queue, gift_planning, comparison_shortlist, unclear). Use "unclear" if the record doesn't concern wishlist-saving behavior at all.
   - purchase_intent: HOW STRONG the intent to buy is (genuine_intent, consideration, bookmarking, inspiration, unclear). Do not assume a "wishlist" mention alone means high purchase intent -- classify from the actual evidence.

6. purchase_outcome: the DECISION outcome only (purchased, delayed, abandoned, alternative_chosen, unknown). Do NOT fold in what happened after a purchase (returns, exchanges, service problems) -- a returned item is still "purchased" here. That detail goes in post_purchase (rule 7).

7. post_purchase: set occurred=true if a purchase happened per this record. issues: zero or more of delivery_problem, fit_quality_problem, customer_service_problem, wrong_item, authenticity_problem, other -- only what the text actually describes. trust_damage: true only if the text itself indicates damaged trust/confidence in the platform or seller (not inferred from a mildly negative tone).

8. future_purchase_relevance: this is critical -- do NOT assume every post-purchase complaint affects future purchasing, and do NOT assume every post-purchase account is irrelevant to it either. Follow the codebook's future_purchase_relevance.values[].worked_example entries below for exactly how to judge direct vs. indirect vs. none vs. unclear. A "quote" is REQUIRED (verbatim from the text) whenever level is "direct" or "indirect" -- if you cannot quote language supporting that level, use "unclear" instead. Never infer future behavior beyond what the text states.

9. event_timeline: zero or more distinct events the text narrates (e.g. "wishlisted", "ordered", "delivered", "returned"), each with its own relative_time (past/ongoing/anticipated/unspecified) and a verbatim quote. Keep this lightweight -- typically no more than 3-4 entries even for a record narrating a long history; do not try to reconstruct a full detailed timeline, just the distinct events actually stated. This is about the EVENTS DESCRIBED IN THE TEXT, not when the record was posted (the record's own post/publish date is tracked separately, outside this extraction, and is never something you estimate). Do not fabricate dates or events not in the text.

10. segment_hints: only self-disclosed context actually stated in the text (e.g. "as a student", "for my wedding"). Do NOT invent demographic guesses. Empty list if nothing is self-disclosed. Do not invent user segments -- only extract what's there.

11. Do not use the fact that a record was retrieved by a particular search query as evidence of anything -- classify purely from the record's own text.

12. Do not invent labels outside the codebook below. Every confidence is your own calibrated estimate in [0, 1], not a placeholder. Where evidence is genuinely insufficient, use "unclear"/"unknown" rather than guessing.

13. CONFIDENCE CALIBRATION -- this applies to every confidence field in the schema: confidence measures how strongly the TEXT SUPPORTS the label you chose, not how sure you are that your classification process was correct. This has a direct consequence: whenever you output a fallback value ("unclear", "unknown", or an empty/none-type value) because the text does not contain enough evidence to support a specific label, the confidence for that field MUST be LOW (roughly 0.2-0.5), reflecting that the evidence is genuinely weak or absent. Do NOT output high confidence (0.8+) on an "unclear"/"unknown" label -- being confident that something is unclear is not what this field measures. Reserve confidence 0.8+ for cases where you are choosing a SPECIFIC, non-fallback label and the text clearly supports it. This rule applies to wishlist_role_confidence, purchase_intent_confidence, journey_stage_confidence, purchase_outcome_confidence, evidence_role_confidence, and future_purchase_relevance.confidence alike.
"""

# --- Rule 14: added for the live engine only. ---
THEME_INSTRUCTION = """
14. theme_matches: map this record onto the LOCKED THEME SET (T1-T12) listed below. These twelve themes were derived by clustering a 16,917-record corpus; you are NOT re-deriving or editing them, only judging which existing themes this one record is evidence for.
   - Return zero or more matches. Zero is a perfectly valid and expected answer -- most individual records are evidence for one theme, many for none. Do NOT stretch a record to fit a theme.
   - Match on the theme's "mechanism", not its name. A record mentioning the word "return" is only T2 evidence if it describes the return/refund PROCESS being difficult, per T2's mechanism.
   - Each match needs a "quote": an exact, verbatim substring of the record's text that evidences the theme. No verbatim quote, no match.
   - "confidence" follows rule 13: high only when the mechanism clearly fires.

Return one result object per input record, keyed by the same evidence_id, in the same order given. Do not skip any record.
"""

# Keys present in codebook.json purely for human readers (changelog, lock
# status) carry no instructional value and are stripped before sending.
DOC_ONLY_KEYS = {"note", "status"}


def load_themes() -> list[dict]:
    with open(THEMES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def load_codebook() -> dict:
    with open(CODEBOOK_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt() -> tuple[str, str]:
    """Returns (system_prompt, codebook_version)."""
    codebook = load_codebook()
    codebook_version = codebook["codebook_version"]
    model_facing = {k: v for k, v in codebook.items() if k not in DOC_ONLY_KEYS}
    # Compact separators, not indent=2 -- whitespace is pure token cost here.
    codebook_text = json.dumps(model_facing, ensure_ascii=False, separators=(",", ":"))

    # Only id/name/mechanism go to the model. The corpus counts and metric
    # nodes in themes.json are for the UI; sending them would invite the model
    # to weight a theme by how common it was in the corpus rather than by what
    # this record actually says.
    themes_text = json.dumps(
        [{"theme_id": t["theme_id"], "name": t["name"], "mechanism": t["mechanism"]} for t in load_themes()],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    prompt = (
        f"{INSTRUCTIONS}{THEME_INSTRUCTION}\n\n"
        f"CODEBOOK (codebook_version={codebook_version}):\n{codebook_text}\n\n"
        f"LOCKED THEME SET (T1-T12, derived from the 16,917-record corpus -- do not modify):\n{themes_text}"
    )
    return prompt, codebook_version

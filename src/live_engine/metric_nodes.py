"""
Mechanical mapping from extracted fields to metric-decomposition nodes M1-M6
-- ported from phase2_analysis/src/myntra_analysis/metric_nodes.py.

Deliberately rule-based, not LLM-judged, and that is the point worth showing:
the connection between a live record and the Wishlist -> Purchase metric
decomposition is *computed* from the record's own extracted fields, not
asserted by a model. The LLM never gets asked "which metric node does this
affect?", so it can never invent a connection the data doesn't support.

Simplified vs. Phase 2: Phase 2 read rows out of a parquet dataframe, where
nested list fields come back as numpy arrays and `x or []` raises on them, so
it needed a defensive `_as_list`. Live records are plain dicts straight off
the JSON response, so that shim is gone.
"""

from __future__ import annotations

from collections import Counter

NODE_NAMES = {
    "M1": "Wishlist Add",
    "M2": "Post-Save Evaluation",
    "M3": "Purchase Decision",
    "M4": "Fulfillment Experience",
    "M5": "Post-Purchase Resolution",
    "M6": "Repeat-Purchase Propensity",
}

NODE_ORDER = ["M1", "M2", "M3", "M4", "M5", "M6"]


def record_nodes(row: dict) -> set[str]:
    """Which M-nodes this single classified record plausibly touches (can be >1)."""
    nodes: set[str] = set()

    stage = row.get("journey_stage")
    sig_stages = {s["stage"] for s in row.get("journey_signals") or []}
    factors = {f["factor"] for f in row.get("factor_tags") or []}
    pp = row.get("post_purchase") or {}
    pp_issues = {i["type"] for i in pp.get("issues") or []}
    fpr_level = (row.get("future_purchase_relevance") or {}).get("level")

    if (
        stage in ("discovery", "wishlist_save")
        or "wishlist_motivation" in sig_stages
        or row.get("wishlist_role") not in (None, "unclear")
    ):
        nodes.add("M1")

    if (
        stage in ("evaluation", "hesitation")
        or sig_stages & {"uncertainty", "comparison", "external_information"}
        or row.get("external_research")
    ):
        nodes.add("M2")

    if (
        stage == "purchase"
        or sig_stages & {"purchase_barrier", "purchase_postponement"}
        or row.get("purchase_intent") not in (None, "unclear")
        or row.get("purchase_outcome") not in (None, "unknown")
    ):
        nodes.add("M3")

    if stage in ("delivery", "trial_use") or pp_issues & {
        "delivery_problem", "fit_quality_problem", "wrong_item", "authenticity_problem"
    }:
        nodes.add("M4")

    if (
        stage in ("return_exchange", "post_purchase_reflection")
        or pp.get("trust_damage")
        or "customer_service_problem" in pp_issues
        or "trust" in factors
    ):
        nodes.add("M5")

    if fpr_level in ("direct", "indirect") or row.get("evidence_role") == "indirect_future_purchase":
        nodes.add("M6")

    return nodes


def node_distribution(records: list[dict]) -> Counter:
    """Node frequency across a set of records -- each record can contribute to
    multiple nodes, so this sums to more than len(records)."""
    counter: Counter = Counter()
    for r in records:
        counter.update(record_nodes(r))
    return counter

"""
Pipeline orchestration -- the four stages the demo button runs, plus the
aggregation the results panel reads.

    fetch  ->  normalize  ->  classify  ->  map to themes + metric nodes

Stages 1-2 happen inside collectors.py (each collector normalizes as it
emits, exactly as Phase 1 did -- there is no separate normalization pass to
run because there is no intermediate file). Stage 3 is one Gemini call.
Stage 4 is `metric_nodes.record_nodes` plus the validated `theme_matches`
from stage 3.

The stage callback exists so the UI can report progress: a silent 25-second
spinner reads as a broken page.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

from live_engine import classify as classify_mod
from live_engine import collectors, metric_nodes, relevance, validate
from live_engine.normalize import LiveRecord, utc_now_iso
from live_engine.prompt import PROMPT_VERSION, build_system_prompt, load_themes

# (stage_name, human detail, payload). The payload carries real data -- the
# SourceResult that just landed, or the normalized records about to be
# classified -- so the UI can show what was actually fetched during the ~25s
# wait instead of four abstract stage labels.
StageCallback = Callable[[str, str, object], None]


@dataclass
class RunResult:
    run_id: str
    started_at: str
    source_results: list[collectors.SourceResult]
    selection_stats: dict
    records: list[LiveRecord]
    classified: dict[str, dict]          # evidence_id -> validated result
    validation_issues: dict[str, list[str]]  # evidence_id -> issues
    batch_issues: list[str] = field(default_factory=list)
    codebook_version: str = ""
    prompt_version: str = PROMPT_VERSION
    model: str = classify_mod.MODEL
    timings: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.classified)

    def record_by_id(self, evidence_id: str) -> Optional[LiveRecord]:
        return next((r for r in self.records if r.evidence_id == evidence_id), None)


def run(
    n_records: int = 10,
    sources: Optional[list[str]] = None,
    on_stage: Optional[StageCallback] = None,
    fetch_deadline_s: float = 30.0,
) -> RunResult:
    def stage(name: str, detail: str = "", payload: object = None) -> None:
        if on_stage:
            on_stage(name, detail, payload)

    run_id = f"live_{int(time.time())}"
    started = utc_now_iso()
    timings: dict = {}

    # --- stage 1+2: fetch and normalize ---
    stage("fetch", "querying public sources in parallel")
    t0 = time.time()
    source_results = collectors.fetch_all(
        sources,
        deadline_s=fetch_deadline_s,
        # Emitted per source as it lands, not batched at the end -- Google Play
        # answers in ~0.6s and Reddit in ~9s, and showing the first while
        # waiting on the last is the difference between a live-looking page and
        # a stalled one.
        on_source=lambda sr: stage("source", sr.detail, sr),
    )
    timings["fetch_s"] = round(time.time() - t0, 1)

    ok_sources = [r for r in source_results if r.ok]
    if not ok_sources:
        return RunResult(
            run_id, started, source_results, {}, [], {}, {},
            timings=timings,
            error="Every source failed or timed out. This is a live-fetch failure, not a classification failure -- see the per-source detail above.",
        )

    t0 = time.time()
    records, selection_stats = collectors.select_top(source_results, n=n_records)
    timings["select_s"] = round(time.time() - t0, 1)

    if not records:
        return RunResult(
            run_id, started, source_results, selection_stats, [], {}, {},
            timings=timings,
            error=(
                "Sources responded, but nothing survived filtering: "
                f"{selection_stats.get('fetched', 0)} fetched → "
                f"{selection_stats.get('after_junk_filter', 0)} after the junk filter → "
                f"{selection_stats.get('after_brand_gate', 0)} mentioned Myntra. "
                "Try again — this is a thin-sample run, not a broken pipeline."
            ),
        )

    # The normalized records go to the UI here, before the ~15s classify call,
    # so the user reads real fetched text during the wait rather than a spinner.
    stage(
        "normalize",
        f"{selection_stats['fetched']} → {selection_stats['after_junk_filter']} → "
        f"{selection_stats['after_brand_gate']} → {len(records)} records",
        records,
    )

    # --- stage 3: classify ---
    stage("classify", f"one structured call, {len(records)} records, codebook v1.1")
    t0 = time.time()
    system_prompt, codebook_version = build_system_prompt()
    try:
        raw_results, model_used = classify_mod.classify(records, system_prompt)
    except classify_mod.ClassificationError as e:
        return RunResult(
            run_id, started, source_results, selection_stats, records, {}, {},
            codebook_version=codebook_version, timings=timings, error=str(e),
        )
    timings["classify_s"] = round(time.time() - t0, 1)
    # The classify call is one blocking request -- nothing to stream mid-call --
    # so this is the earliest point real results exist. Emitted before
    # validation (raw, not yet verbatim-checked) so the running UI can preview
    # which themes are surfacing the moment they exist, instead of the user
    # staring at "Classifying..." until the whole pipeline finishes.
    stage("classified", f"{len(raw_results)} records scored", raw_results)

    # --- stage 4: validate, then map to themes + metric nodes ---
    stage("validate", "checking every quote is verbatim")
    by_id, batch_issues = validate.validate_batch_response([r.evidence_id for r in records], raw_results)

    classified: dict[str, dict] = {}
    issues: dict[str, list[str]] = {}
    for rec in records:
        result = by_id.get(rec.evidence_id)
        if result is None:
            continue
        result, rec_issues = validate.validate_result(result, rec.text)
        result["metric_nodes"] = sorted(metric_nodes.record_nodes(result))
        classified[rec.evidence_id] = result
        if rec_issues:
            issues[rec.evidence_id] = rec_issues

    timings["total_s"] = round(sum(v for k, v in timings.items() if k.endswith("_s")), 1)
    stage("validated", f"{len(classified)} of {len(records)} verified", classified)

    return RunResult(
        run_id=run_id,
        started_at=started,
        source_results=source_results,
        selection_stats=selection_stats,
        records=records,
        classified=classified,
        validation_issues=issues,
        batch_issues=batch_issues,
        codebook_version=codebook_version,
        model=model_used,
        timings=timings,
    )


# --------------------------------------------------------------------------
# Aggregation for the results panel.
# --------------------------------------------------------------------------
@dataclass
class ThemeHit:
    theme_id: str
    name: str
    mechanism: str
    metric_nodes: list[str]
    corpus_share_pct: float
    corpus_evidence_count: int
    live_count: int
    evidence: list[dict]  # [{evidence_id, quote, confidence, source, url}]


def aggregate_themes(result: RunResult) -> list[ThemeHit]:
    """Which of the locked T1-T12 the live batch fired, with the quotes that
    fired them, ordered by live count then corpus share.

    Themes with zero live hits are omitted here -- the UI states the total so
    "3 of 12 themes fired" stays visible rather than implying all twelve did.
    """
    themes = {t["theme_id"]: t for t in load_themes()}
    hits: dict[str, list[dict]] = defaultdict(list)

    for evidence_id, res in result.classified.items():
        rec = result.record_by_id(evidence_id)
        for tm in res.get("theme_matches") or []:
            hits[tm["theme_id"]].append(
                {
                    "evidence_id": evidence_id,
                    "quote": tm.get("quote", ""),
                    "confidence": tm.get("confidence", 0.0),
                    "source": rec.source if rec else "?",
                    "url": rec.url if rec else None,
                }
            )

    out = []
    for theme_id, evidence in hits.items():
        t = themes.get(theme_id)
        if not t:
            continue
        # Order the evidence so the quote we SHOW first is on-subject. For every
        # theme except T5, a verbatim quote that names a competitor but not
        # Myntra is pushed below the on-subject ones regardless of its
        # confidence -- otherwise a high-confidence "Ajio is fraud" clause can
        # end up as the displayed card for a Myntra theme. T5 keeps a pure
        # confidence sort: naming a competitor is what its evidence is.
        if theme_id == "T5":
            ordered = sorted(evidence, key=lambda e: -e["confidence"])
        else:
            ordered = sorted(
                evidence,
                key=lambda e: (relevance.quote_is_off_subject(e["quote"]), -e["confidence"]),
            )
        out.append(
            ThemeHit(
                theme_id=theme_id,
                name=t["name"],
                mechanism=t["mechanism"],
                metric_nodes=t["metric_nodes"],
                corpus_share_pct=t["corpus_share_pct"],
                corpus_evidence_count=t["total_evidence_count"],
                live_count=len(evidence),
                evidence=ordered,
            )
        )
    return sorted(out, key=lambda h: (-h.live_count, -h.corpus_share_pct))


def aggregate_nodes(result: RunResult) -> list[tuple[str, str, int]]:
    """(node_id, node_name, live record count) for all six nodes, in funnel
    order. Zero-count nodes are kept: an empty node is itself a finding about
    what this batch happened to surface."""
    dist = metric_nodes.node_distribution(list(result.classified.values()))
    return [(n, metric_nodes.NODE_NAMES[n], dist.get(n, 0)) for n in metric_nodes.NODE_ORDER]


def aggregate_field(result: RunResult, field_name: str) -> Counter:
    """Distribution of a single scalar label field across the batch."""
    return Counter(res.get(field_name) for res in result.classified.values() if res.get(field_name))


def aggregate_signals(result: RunResult) -> Counter:
    c: Counter = Counter()
    for res in result.classified.values():
        c.update(s["stage"] for s in res.get("journey_signals") or [])
    return c


def aggregate_factors(result: RunResult) -> list[tuple[str, int, Counter]]:
    """(factor, total mentions, sentiment breakdown) -- aspect-level sentiment,
    which is the part the record-level sentiment field flattens away."""
    totals: Counter = Counter()
    sentiments: dict[str, Counter] = defaultdict(Counter)
    for res in result.classified.values():
        for ft in res.get("factor_tags") or []:
            totals[ft["factor"]] += 1
            sentiments[ft["factor"]][ft.get("sentiment", "neutral")] += 1
    return [(f, n, sentiments[f]) for f, n in totals.most_common()]

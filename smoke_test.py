"""
Headless end-to-end check: run the same pipeline the button runs, print what
came back. No Streamlit, no browser -- so a deploy problem can be told apart
from a UI problem.

    python smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from live_engine import pipeline
from live_engine.collectors import SOURCE_LABELS


def main() -> int:
    print("Running live pipeline...\n")
    result = pipeline.run(n_records=10, on_stage=lambda s, d, p=None: print(f"  [{s:9}] {d}"))

    print("\n--- sources ---")
    for sr in result.source_results:
        mark = "ok  " if sr.ok else "FAIL"
        print(f"  {mark} {SOURCE_LABELS.get(sr.source, sr.source):26} {sr.elapsed_s:5.1f}s  {sr.detail}")

    s = result.selection_stats
    print("\n--- selection funnel ---")
    print(f"  fetched            {s.get('fetched')}  {s.get('by_source_fetched')}")
    print(f"  after junk filter  {s.get('after_junk_filter')}")
    print(f"  after brand gate   {s.get('after_brand_gate')}   ({s.get('dropped_off_brand')} dropped as off-brand)")
    print(f"  selected           {s.get('selected')}   {s.get('by_source_selected')}")

    if result.error:
        print(f"\nERROR: {result.error}")
        return 1

    print(f"\n--- timings ---\n  {result.timings}")
    print(f"  model={result.model} prompt={result.prompt_version} codebook={result.codebook_version}")
    if "fallback" in result.model:
        print("  NOTE: Gemini failed twice; the Groq fallback ran this batch.")

    print(f"\n--- classified {len(result.classified)}/{len(result.records)} records ---")
    for rec in result.records:
        res = result.classified.get(rec.evidence_id)
        if not res:
            print(f"  MISSING {rec.evidence_id}")
            continue
        themes = ",".join(t["theme_id"] for t in res.get("theme_matches") or []) or "-"
        brand = "myntra" if "myntra" in rec.text.lower() else "NO-MYNTRA"
        print(
            f"  {rec.source:12} {brand:9} role={res['evidence_role']:24} stage={res['journey_stage']:24} "
            f"intent={res['purchase_intent']:14} M={','.join(res['metric_nodes']) or '-':17} T={themes}"
        )

    print("\n--- themes fired ---")
    for hit in pipeline.aggregate_themes(result):
        print(f"  {hit.theme_id:4} {hit.name:48} live={hit.live_count}  corpus={hit.corpus_share_pct}%")
        for e in hit.evidence[:2]:
            print(f"        \"{e['quote'][:90]}\" ({e['source']}, conf {e['confidence']})")

    print("\n--- metric nodes ---")
    for node, name, count in pipeline.aggregate_nodes(result):
        print(f"  {node} {name:26} {count}")

    print("\n--- factors ---")
    for factor, n, sent in pipeline.aggregate_factors(result):
        print(f"  {factor:20} {n:3}  {dict(sent)}")

    print("\n--- journey signals ---")
    print(f"  {dict(pipeline.aggregate_signals(result))}")

    issues = sum(len(v) for v in result.validation_issues.values())
    print(f"\n--- validation ---\n  {issues} quote/label issue(s) across {len(result.validation_issues)} record(s)")
    for eid, msgs in result.validation_issues.items():
        for m in msgs:
            print(f"    {eid[:8]}: {m}")
    for m in result.batch_issues:
        print(f"    batch: {m}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

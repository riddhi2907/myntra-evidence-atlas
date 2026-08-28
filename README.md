# Phase 3 — Live Discovery Engine

A one-button web demo of the discovery engine: it fetches publicly available
consumer feedback about Myntra **at the moment you click**, normalizes it,
classifies it against the locked research codebook, and maps each record onto
the twelve opportunity themes and the six metric-decomposition nodes produced
in Phase 2.

Nothing on the page is precomputed. Phases 1 and 2 were a static, batch
analysis of 16,917 records; this is the same pipeline, live, on ten.

```
Fetch                 Normalize            Classify             Map
Google Play    ──┐                                          ┌─ Themes T1–T12
Apple App Store ─┼─▶  one schema,   ──▶   one structured  ──▶│  (LLM, every match
YouTube        ──┤    whitespace          Gemini call,       │   quote-verified)
Reddit         ──┘    cleaned,            codebook v1.1      └─ Metric nodes M1–M6
   (parallel)         handles hashed                            (deterministic rules)
```

## Quick start

```bash
cd phase3_live_engine
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY (and optionally YOUTUBE_API_KEY)

streamlit run app.py          # the demo
python smoke_test.py          # same pipeline, headless, prints everything
```

`smoke_test.py` exists so a deployment problem can be told apart from a UI
problem: if it prints themes and metric nodes, the engine works and anything
wrong is in the page.

## Deploying to Streamlit Community Cloud

**Deploy a repo containing only this folder.** The parent project holds
`interviews/` — eight user-research transcripts of named real people — and
`Meha.docx`. The root `.gitignore` now excludes those and `phase2_analysis/data/`
(its rule used to say `analysis/data/`, the old folder name, and matched
nothing), but pushing this folder on its own removes the question entirely, and
nothing here imports from the other phases.

```bash
cd phase3_live_engine
git init && git add . && git commit -m "Live discovery engine"
# check `git status` shows no .env and no .streamlit/secrets.toml first
```

1. Push that repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create an app pointing
   at it with **main file path** `app.py`.
3. Open **Settings → Secrets** and paste the contents of
   `.streamlit/secrets.toml.example`, filled in:

   ```toml
   GEMINI_API_KEY = "..."
   YOUTUBE_API_KEY = "..."
   GROQ_API_KEY = "..."
   ```

4. **Click the button once and read the source panel.** `google-play-scraper`
   has only been verified from a residential IP; datacenter IPs are a common
   block point for it. If Google Play shows as unavailable there, the run
   degrades gracefully to three sources — but that is worth finding out before
   grading day, not during it.

`config.py` looks for credentials in Streamlit secrets first, then the
environment, then a local `.env` — so the same code runs in both places with
no branching. (Phase 2's clients read `.env` only, which works on a laptop and
fails silently on a host that has no `.env` file; that's the bug this avoids.)

Only `GEMINI_API_KEY` is required, and all three keys are free-tier. Without
`YOUTUBE_API_KEY` the app still runs — YouTube is reported as unavailable in
the source panel and the other three sources carry the batch. `GROQ_API_KEY`
is the classifier fallback, described below.

### The classifier is the single point of failure

Four independent sources make a total fetch failure unlikely, and any source
that fails is reported rather than hidden. The classification call has no such
redundancy: it is one call, and if it fails the page has nothing to show. So
`classify()` retries Gemini once after ~3s on a transient error (a free-tier
429 on the first click is the realistic failure and usually clears), then falls
back to Groq if a key is configured. The Audit tab always names the model that
actually ran, so a fallback never silently misreports provenance.

## Source reliability

Measured from this environment, and the reason the demo is built the way it is:

| Source | Auth | Typical | Behaviour |
|---|---|---|---|
| **Google Play** | none | ~0.6s | The most reliable source; the primary. No server-side keyword search, so it pages the newest reviews and relevance ranking picks from there. |
| **Apple App Store** | none | ~1–2s | Works, but the public RSS feed intermittently returns an empty page 1 with HTTP 200 and no error. `_app_store_page()` retries three times before believing it. The `l=en` query parameter is required for the India storefront — without it the feed silently returns zero entries (a Phase 1 finding, ported). |
| **YouTube** | API key | ~2.5s | Live video search, then comment threads. `search.list` costs 100 quota units against a free daily budget of 10,000 and `commentThreads.list` costs 1, so the run does three searches (~300 units) — genuine live discovery, and still ~30 clicks/day. |
| **Reddit** | none | ~9–12s | Via Arctic Shift, a public Reddit archive. It throttles hard, answering `422 "Timeout. Maybe slow down a bit"` rather than 429; a call typically needs 2–3 attempts. Subreddits are queried concurrently (sequential retries put this source alone at ~22s). **Never load-bearing** — it often returns only 1 of 3 subreddits. |

All four are fetched in parallel behind a 30-second wall-clock deadline that
is real, not advisory: `fetch_all` calls `shutdown(wait=False,
cancel_futures=True)` rather than using a `with` block, whose `__exit__` would
block on stragglers anyway. Reddit's own worst case is bounded to fit
(3 x 8s timeout + 2 x 2s spacing = 28s).

A source that fails or overruns is **shown in the UI as failed, with the
reason** — never silently dropped. Nothing is cached and no sample data is
bundled: if a source is down, the page says so.

## Why themes are mapped, not re-derived

Phase 2 derived T1–T12 by clustering thousands of classified records. Ten
records cannot produce clusters, and a demo that presented ad-hoc groupings of
ten records as "themes discovered live" would be inviting a fair objection.

So the twelve themes are **locked input**, sent to the model as a fixed set
(prompt rule 14), and each live record is judged against each theme's
*mechanism*. The live run therefore demonstrates the existing framework
catching new evidence — which is the honest and more interesting claim.

Metric nodes go further: **M1–M6 are never asked of the model at all.**
`metric_nodes.record_nodes()` computes them by rule from the record's own
extracted fields, so the model cannot assert a connection to the business
metric that the extraction doesn't support.

## Quote verification

Every quote the model produces is checked to be a verbatim substring of the
record it came from (`validate.py`). A model that paraphrases a quote may be
paraphrasing the finding too.

- `journey_signals` / `event_timeline` — a failed quote is flagged, its
  confidence halved, the quote blanked. Kept, but marked.
- `future_purchase_relevance` at `direct`/`indirect` — downgraded to
  `unclear` without a verifiable quote.
- `theme_matches` — **dropped outright.** There is no weaker version of "this
  record is evidence for T3".

The Audit tab shows every failure. A typical run has 0–4.

One deliberate loosening: curly quotes, en/em dashes and non-breaking spaces
are folded to their ASCII equivalents before matching. A curly apostrophe
copied back as a straight one is the same quote, not a paraphrase; the words
still have to match exactly, in order.

## Layout

```
app.py                      Streamlit UI -- the only file with any UI in it
smoke_test.py               headless end-to-end run, prints everything
requirements.txt            5 dependencies
.streamlit/config.toml      pinned light theme (charts are designed against one surface)
.streamlit/secrets.toml.example
data/
  codebook.json             copied from phase2_analysis, v1.1, unmodified
  themes.json               T1–T12 trimmed to what the demo needs
src/live_engine/
  config.py                 credentials: Streamlit secrets -> env -> .env
  normalize.py              text cleaning, date parsing, handle hashing, LiveRecord
  relevance.py              keyword scoring + junk filter -- picks which 10 to show
  collectors.py             the four sources, parallel fetch, selection
  prompt.py                 Phase 2's system prompt + rule 14 (theme mapping)
  classify.py               one Gemini structured-output call, Groq fallback
  validate.py               verbatim-quote enforcement
  metric_nodes.py           rule-based M1–M6 mapping
  pipeline.py               orchestration + aggregation for the results panel
  charts.py                 design tokens + HTML/CSS chart primitives
```

## What was cut from Phases 1 and 2

The brief for this phase was "the same pipeline, less complexity". Reused
unchanged: the codebook (v1.1), the system prompt (rules 1–13), the
verbatim-quote validation, the M1–M6 mapping, the normalization rules, and the
collector logic.

Dropped, with the reason each existed:

| Dropped | Why it existed | Why it isn't needed here |
|---|---|---|
| `pandas` + `pyarrow` | 16,917 records in a parquet dataframe | Ten records are a list of dicts. Dropping these is most of the deploy weight and cold-start time. |
| Multi-provider registry (Gemini + Groq + OpenRouter), hash-split | Splitting a huge job across free-tier daily quotas | Ten records is one call, so there is nothing to split. Groq survives as a plain fallback for a different reason — see above. |
| Char-budget batching (6,000 chars) | Packing thousands of records efficiently | Ten selected records fit in one call. |
| `SourceCollector` ABC, `RawWriter`, run metadata, YAML config | A multi-hour run that had to be resumable and auditable | One round-trip per source. Each collector is a plain function. |
| Clustering, opportunity synthesis, `opportunity_areas.json` | Deriving themes from the corpus | Themes are locked input here — see above. |
| Gold set, bias diagnostics, secondary-read check | Validating the static analysis' quality | Those validated the corpus that produced the locked codebook and themes this demo consumes. |
| `codebook_v0`, seed ingestion, LinkedIn discovery, `experiments/` | Phase 1/2 exploration | Not part of the pipeline either phase settled on. |

## Known limitations

- **Ten records are a demonstration, not a finding.** The themes and metric
  nodes that fire on any given run reflect what four public sources happened
  to surface in the last few minutes — heavily post-purchase, because that is
  what people write app reviews and Reddit posts about. The corpus percentages
  shown beside each theme come from the 16,917-record analysis and are the
  numbers to reason from.
- **Relevance ranking is a demo constraint, not a research one.** Phase 1
  deliberately kept low-relevance records so downstream analysis could decide.
  A page that can only show ten has to choose, so `relevance.py` ranks by
  keyword hits and the UI says so. The full fetched and filtered counts are
  always displayed.
- **Reddit skew.** Long Reddit posts structurally outscore two-line app
  reviews on keyword count, so `select_top` caps each source at 4 of 10;
  without the cap Reddit takes 8 slots.
- **Sub-40-character records are dropped** before ranking ("Good", "Link",
  emoji-only). They carry no extractable journey signal at any relevance score.
- **`r/MyntraSucks` is in the subreddit list**, which biases Reddit evidence
  negative by construction. It was the highest-yield subreddit in Phase 1 and
  is kept for that reason; the source panel names every subreddit queried.

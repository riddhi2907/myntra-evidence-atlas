"""Live Engine page -- fetch, classify, and map records right now.

Shares Findings' visual DNA (Inter + weight vocabulary, ink/teal palette,
tokens, nav pill, canvas wash, component language) but deliberately NOT its
page-level composition. Findings opens with an editorial cover (kicker pill
-> large gradient-accent cover-h1 -> subhead -> a CTA that closes an
argument) and repeats a section-id -> <h2> -> .note rhythm down the page.
Live Engine opens with an instrument masthead (mono eyebrow -> tighter
solid-ink headline, no gradient word -> one line) whose terminal element is
the control console: a bordered frame holding the run control, the gear,
and the four-step execution timeline. The timeline is visible from first
load (pending), during a run (live), and after (re-openable). The point is
that a viewer switching pages without reading the URL immediately knows one
is for reading results and the other for running the engine. See
DESIGN-SYSTEM.md Layout / ux.md.

An earlier version had five tabs (themes / metric decomposition / records /
signals & factors / audit) with nested expanders and multi-field record
dumps -- functionally complete but structurally inconsistent. It also hit a
real bug: bare `##`/`###` markdown headers get caught by the same global CSS
as Findings' large section headers, so they rendered oversized next to
compact utilitarian content.

Kept: run controls, the live status feed (the actual proof this is live,
not precomputed), sources queried, the selection funnel, and the theme-hit
output -- now shown the same way the findings page shows ranked themes
(charts.bar_chart) plus real evidence quotes styled like Consumer Voices.

Cut: metric-decomposition node routing (consistent with dropping M-node
framing on the findings page), the deep per-record multi-field dive,
signals/factors breakdowns, and the audit tab's stat trio + raw code dump --
collapsed to one quiet verification line and a download link.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from html import escape

import streamlit as st

from . import charts, chrome, pipeline
from .collectors import COLLECTORS, SOURCE_LABELS
from .config import gemini_key, youtube_key
from .prompt import load_themes


def _fmt_secs(v: float) -> str:
    """Sub-100ms stages read as broken showing '0.0s' -- floor the label."""
    return "<0.1s" if v < 0.1 else f"{v:.1f}s"


def render(findings_page, engine_page) -> None:
    chrome.inject_css()
    chrome.nav_shell(findings_page, engine_page, "engine")

    # Instrument masthead, NOT Findings' editorial cover. Shared DNA (Inter,
    # weights, ink/teal, tokens, nav, canvas) but a different composition
    # grammar on purpose: a mono instrument label + a tighter solid-ink
    # headline with no gradient accent-word, one line of copy, then the
    # control console as the hero's terminal element. Findings opens with
    # kicker-pill -> large cover-h1 (gradient phrase) -> subhead -> a CTA
    # that closes an argument; this page has to read as an instrument the
    # moment it loads, not as another article about the pipeline. See
    # DESIGN-SYSTEM.md Layout / ux.md.
    # Emitted as direct .block-container children -- NOT wrapped in a
    # `.scene` div, whose extra horizontal padding would inset the hero
    # ~110px past the left edge every other element on the page sits at.
    st.write("")
    st.write("")
    st.markdown(
        '<p class="engine-eyebrow"><b>Live</b> engine &nbsp;·&nbsp; Myntra Wishlist</p>'
        '<h1 class="engine-h1">Fetch, classify, and map, live.</h1>'
        '<p class="engine-lead">Press run. It fetches real public records now, classifies them '
        "against the same locked codebook as Findings, and maps them onto the same twelve themes. "
        "Nothing here is precomputed.</p>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # Run action + settings drawer. Settings used to live in Streamlit's
    # native left sidebar -- always-left, collapsed to a single easy-to-miss
    # arrow with no indication anything was behind it -- then in a second
    # right-hand st.columns() panel. That column fixed the discoverability
    # problem but created a new one: st.columns() sizes a row to its tallest
    # sibling, so opening it stretched the whole shared row and pushed every
    # section below (including the empty-state theme grid) further down the
    # page, even though the button column next to it had nothing to fill
    # that space with.
    #
    # This is now a fixed, right-anchored overlay drawer -- the same
    # position:fixed technique chrome.py already uses for the nav pill --
    # so opening or closing it never moves anything else on the page.
    # --------------------------------------------------------------------------
    if "cfg_sources" not in st.session_state:
        st.session_state.cfg_sources = list(COLLECTORS)
    if "cfg_n_records" not in st.session_state:
        st.session_state.cfg_n_records = 10
    if "engine_settings_open" not in st.session_state:
        st.session_state.engine_settings_open = False

    is_open = st.session_state.engine_settings_open
    selected_sources = st.session_state.cfg_sources
    n_records = st.session_state.cfg_n_records

    # Drawer/backdrop position comes from an inline style computed here in
    # Python, not a JS-toggled class -- injected <script> tags never execute
    # inside st.markdown() (see the note on spine() in chrome.py), so the
    # open/closed state has to be baked into the CSS on every rerun instead
    # of flipped client-side.
    drawer_style = (
        "transform:translateX(0);opacity:1;pointer-events:auto;"
        if is_open
        else "transform:translateX(calc(100% + 40px));opacity:0;pointer-events:none;"
    )
    backdrop_style = "opacity:1;" if is_open else "opacity:0;pointer-events:none;"
    # A real click-catcher, not just a decorative dimmer -- see the
    # st-key-drawerscrim button below. It only needs to intercept clicks
    # while the drawer is open; closed, it must let every click on the page
    # pass straight through, hence pointer-events flipping the same way the
    # drawer itself does.
    scrim_style = "pointer-events:auto;" if is_open else "pointer-events:none;"
    st.markdown(
        f"<style>.st-key-settingsdrawer {{ {drawer_style} }} "
        f".drawer-backdrop {{ {backdrop_style} }} "
        f".st-key-drawerscrim {{ {scrim_style} }}</style>"
        '<div class="drawer-backdrop"></div>',
        unsafe_allow_html=True,
    )
    # Click-outside-to-close. This has to be a real Streamlit button (not a
    # JS click handler on the decorative backdrop above) because injected
    # <script> tags never execute inside st.markdown() -- the only way to
    # react to a click at all here is a widget Streamlit itself wires up.
    # It's a full-viewport invisible button sitting between the backdrop
    # and the drawer in z-index, so it only ever catches clicks that land
    # outside the drawer's own bounds; the drawer sits above it and handles
    # its own clicks normally. There's still no Escape-to-close: that would
    # need a real keydown listener, which hits the same script-tag wall.
    with st.container(key="drawerscrim"):
        if st.button("Close settings panel", key="drawer_scrim_btn"):
            st.session_state.engine_settings_open = False
            st.rerun()

    # A viewer pressing a demo button doesn't need to know it's specifically
    # "Gemini classifier" vs "YouTube Data API" -- that's implementation detail
    # leaking into viewer-facing UI (confirmed against ux.md's audience: a
    # grader, not the developer). One readiness signal replaces the two named
    # credential rows that used to sit here; the provider-level break-out only
    # reappears inside the drawer, and only when something's actually missing.
    ready = bool(gemini_key())

    # The control console: a bordered instrument frame (st-key-console) that
    # holds the run control, the gear, the one-line readiness status, and the
    # four-step execution timeline. This is deliberately NOT Findings'
    # hero-CTA grammar (a primary button in a narrow column with an
    # explanatory line beside it, sitting as one more section). Here the
    # console IS the hero's terminal element and the page's defining
    # surface -- action -> live execution -> discovery reads off its
    # structure, not off section copy.
    #
    # Run stays dominant through its animated-gradient type="primary" fill
    # against the gear's plain glass fill -- not through column width. The
    # gear is a utility control: same RADIUS_SM as Run (set by the base
    # .stButton rule), a "Run settings" tooltip/label, opens the existing
    # drawer. See DESIGN-SYSTEM.md's Control Console + Gear entries.
    with st.container(key="console"):
        run_col, gear_col, meta_col = st.columns(
            [2.1, 0.5, 2.4], gap="small", vertical_alignment="center"
        )
        with run_col:
            # Label flips once a run has completed this session -- "Run again"
            # makes it unmistakable that the current run is finished and the
            # page below is its results, not a form still waiting to be filled.
            # Rendered into an st.empty() so the run handler below can swap it
            # for a disabled "Running discovery…" state for the duration of the
            # blocking pipeline.run() -- the script never leaves this execution
            # mid-run, so a plain st.button() would sit on its idle label the
            # whole time and keep inviting a click it can't service.
            has_run = bool(st.session_state.get("run_log"))
            run_slot = st.empty()
            run_clicked = run_slot.button(
                "Run again" if has_run else "Run live discovery",
                type="primary",
                use_container_width=True,
                disabled=not selected_sources or not ready,
                help="Usually 15 to 40 seconds end to end — Reddit's public archive is the slow leg.",
            )
        with gear_col:
            if st.button("⚙", key="open_settings", help="Run settings", use_container_width=True):
                st.session_state.engine_settings_open = True
                st.rerun()
        with meta_col:
            # An st.empty() so the run handler can overwrite it the moment the
            # run starts -- a plain st.markdown here can't be updated mid-script,
            # which is why it used to sit on "ready to run" for the whole run.
            meta_slot = st.empty()

        def render_meta(state: str) -> None:
            src_line = f"{len(selected_sources)} of {len(COLLECTORS)} sources · {n_records} records"
            if not ready:
                meta_slot.markdown(
                    charts.status_row(src_line, "bad", "add a Gemini key to run — open run settings"),
                    unsafe_allow_html=True,
                )
            elif state == "running":
                meta_slot.markdown(
                    charts.status_row("Running now", "ok", f"{src_line} · fetch → normalize → classify → validate"),
                    unsafe_allow_html=True,
                )
            elif state == "done":
                # The full run stats now live in the .run-complete cap at the
                # foot of the console; up here, next to the button, keep it to
                # the re-run affordance so the row stays one line.
                meta_slot.markdown(
                    charts.status_row("Complete", "ok", "run again for a fresh sample"),
                    unsafe_allow_html=True,
                )
            else:
                meta_slot.markdown(
                    charts.status_row(src_line, "ok", "ready to run — nothing here is precomputed"),
                    unsafe_allow_html=True,
                )

        render_meta("done" if st.session_state.get("run_log") else "idle")

        st.markdown('<p class="console-strip">Execution</p>', unsafe_allow_html=True)

        # --------------------------------------------------------------------
        # Execution timeline: four persistent step cards, not one status box
        # whose contents get overwritten at each stage. Each card only ever
        # changes its OWN state (pending -> running -> done); the other three
        # stay exactly where they are, so the page preserves run history top
        # to bottom instead of discarding it the moment the next stage
        # starts. Rendered inside the same console the button lives in --
        # not a separate widget appended below a now-idle button.
        #
        # Real st.expander widgets can't have their expanded/collapsed state
        # flipped mid-script (Streamlit fixes that at creation), and nothing
        # is clickable while the script is blocked inside pipeline.run()
        # anyway, so the live choreography below uses four st.empty()
        # placeholders rewritten with plain HTML instead. True click-to-
        # expand on a completed step only becomes meaningful once the script
        # is idle again -- see the persistent st.expander-based replay in the
        # `elif` branch below, reached via the st.rerun() at the end of this
        # block.
        # --------------------------------------------------------------------
        stage_order = ["fetch", "normalize", "classify", "validate"]
        stage_titles = {"fetch": "Fetch", "normalize": "Normalize", "classify": "Classify", "validate": "Validate"}
        # One line of "what this step does" -- shown on the idle/pending cards so
        # the resting console reads as the plan for a run, not four empty rows
        # waiting for data.
        stage_blurbs = {
            "fetch": "Query every public source in parallel",
            "normalize": "Junk filter, brand gate, rank by relevance",
            "classify": "One structured call against the locked codebook",
            "validate": "Confirm every quote is a verbatim substring",
        }

        if run_clicked:
            # Swap the control to a disabled running state that stays put for
            # the whole blocking run below; the st.rerun() at the end of this
            # block restores the normal "Run again" label. Same type/width as
            # the idle button so the console row doesn't reflow mid-run.
            run_slot.button(
                "Running discovery…",
                type="primary",
                use_container_width=True,
                disabled=True,
                key="run_active",
            )
            render_meta("running")
            step_slots = [st.empty() for _ in stage_order]
            details: dict[str, str] = {s: "" for s in stage_order}
            summaries: dict[str, str] = {}
            timings_live: dict[str, str] = {}
            started_at: dict[str, float] = {"fetch": time.perf_counter()}
            running_idx = 0

            def close_timing(key: str) -> None:
                if key in started_at and key not in timings_live:
                    timings_live[key] = _fmt_secs(time.perf_counter() - started_at[key])

            def render_step(i: int, state: str) -> None:
                key = stage_order[i]
                step_slots[i].markdown(
                    charts.exec_step(
                        i + 1, stage_titles[key], state,
                        detail_html=details[key], summary=summaries.get(key, ""),
                        blurb=stage_blurbs[key], timing=timings_live.get(key, ""),
                    ),
                    unsafe_allow_html=True,
                )

            for i in range(len(stage_order)):
                render_step(i, "running" if i == 0 else "pending")

            fetch_lines: list[str] = []
            fetch_ok = fetch_total = 0
            norm_records: list = []

            def on_stage(name: str, detail: str, payload: object = None) -> None:
                nonlocal running_idx, fetch_ok, fetch_total, norm_records

                if name == "source":
                    sr = payload
                    fetch_total += 1
                    fetch_ok += 1 if sr.ok else 0
                    fetch_lines.append(
                        charts.status_row(
                            f"{SOURCE_LABELS.get(sr.source, sr.source)}: {detail}",
                            "ok" if sr.ok else "warn",
                            f"{sr.elapsed_s:.1f}s",
                        )
                    )
                    details["fetch"] = "".join(fetch_lines)
                    render_step(0, "running")
                    return

                if name == "classified":
                    # Raw, not-yet-verbatim-checked theme hits -- the
                    # earliest point any real result exists, since classify
                    # is one blocking call with nothing to stream mid-
                    # request. Updates the Classify card's detail in place;
                    # it's still the running step, not a new one.
                    tally: Counter = Counter()
                    for r in payload or []:
                        for tm in r.get("theme_matches") or []:
                            tally[tm["theme_id"]] += 1
                    if tally:
                        chips = "".join(
                            f'<span class="chip" style="border-color:var(--teal);color:var(--teal);'
                            f'font-size:12px;padding:4px 10px;">{escape(tid)} · {n}</span>'
                            for tid, n in tally.most_common(5)
                        )
                        details["classify"] = (
                            '<p style="margin:0 0 6px;">Already surfacing, pending verification:</p>'
                            f"<div>{chips}</div>"
                        )
                        summaries["classify"] = f"{sum(tally.values())} theme matches across {len(payload or [])} records"
                        render_step(2, "running")
                    return

                if name == "validated":
                    # The last stage's own completion signal -- fires right
                    # before pipeline.run() returns, so Validate can go
                    # straight to "done" instead of waiting for the outer
                    # call to return and finalizing it from the outside.
                    summaries["validate"] = detail
                    close_timing("validate")
                    render_step(3, "done")
                    running_idx = 3
                    return

                if name not in stage_order:
                    return

                idx = stage_order.index(name)
                started_at[name] = time.perf_counter()
                if idx > 0:
                    prev_key = stage_order[idx - 1]
                    close_timing(prev_key)
                    if prev_key == "fetch":
                        summaries["fetch"] = f"{fetch_ok} of {fetch_total} sources responded"
                    # normalize's own summary is captured below, at its own
                    # stage-start event, using that event's detail string --
                    # not here, where `detail` belongs to whichever stage is
                    # starting now and would silently overwrite it with the
                    # wrong text.
                    render_step(idx - 1, "done")
                running_idx = idx
                render_step(idx, "running")

                if name == "normalize" and payload:
                    norm_records = list(payload)
                    sample = next((r for r in payload if len(r.text) > 60), None)
                    details["normalize"] = (
                        '<p style="margin:0 0 6px;">Ranked by keyword relevance, sent to the classifier.</p>'
                        + (
                            f'<div class="quote" style="font-size:12px;">{escape(sample.text[:200])}...</div>'
                            if sample
                            else ""
                        )
                    )
                    # This step's own completion summary is the *next*
                    # stage-start event's detail string (pipeline.py passes
                    # the fetched/filtered/selected counts as the "normalize"
                    # event's detail, which is the argument this closure
                    # already has -- captured here since idx==1 here, not at
                    # the point it's marked done one stage later).
                    summaries["normalize"] = detail
                    render_step(1, "running")

                if name == "classify":
                    # The one blocking stage with nothing to stream. Instead of
                    # a frozen "waiting…" line, show the real in-flight manifest
                    # staged from the normalize payload we already hold, plus a
                    # CSS-only sweep so the card reads as working, not stalled.
                    src_counts = Counter(r.source for r in norm_records)
                    src_line = " · ".join(
                        f"{SOURCE_LABELS.get(s, s)} {c}" for s, c in src_counts.most_common()
                    )
                    snippets = "".join(
                        f'<div class="quote" style="font-size:12px;">{escape(r.text[:120])}…</div>'
                        for r in norm_records[:3]
                    )
                    details["classify"] = (
                        f'<p style="margin:0 0 8px;">{len(norm_records)} records in flight against 12 locked '
                        f"themes · codebook v1.1.{f' {escape(src_line)}.' if src_line else ''}</p>"
                        '<div class="exec-shimmer"></div>'
                        f"{snippets}"
                    )
                    render_step(2, "running")

                if name == "validate":
                    details["validate"] = f'<p style="margin:0;">{escape(detail)}</p>'
                    render_step(3, "running")

            result = pipeline.run(n_records=n_records, sources=selected_sources, on_stage=on_stage)

            if result.error:
                summaries[stage_order[running_idx]] = "failed, see below"
                render_step(running_idx, "error")
            elif running_idx < 3:
                # Safety net: the "validated" event should have already
                # closed out step 4, but if a run somehow completes without
                # emitting it, don't leave a step visually stuck "running"
                # forever.
                render_step(running_idx, "done")

            close_timing(stage_order[running_idx])
            authoritative = {
                "fetch": result.timings.get("fetch_s"),
                "normalize": result.timings.get("select_s"),
                "classify": result.timings.get("classify_s"),
            }
            failed_stage = stage_order[running_idx] if result.error else None
            st.session_state["run_log"] = [
                {
                    "title": stage_titles[s],
                    "summary": summaries.get(s, ""),
                    "detail_html": details.get(s, ""),
                    "timing": _fmt_secs(authoritative[s]) if authoritative.get(s) is not None else timings_live.get(s, ""),
                    "state": "error" if s == failed_stage else "done",
                }
                for s in stage_order
            ]
            n_ok_run = sum(1 for sr in result.source_results if sr.ok)
            st.session_state["last_run_summary"] = (
                f"{n_ok_run} of {len(result.source_results)} sources · "
                f"{result.selection_stats.get('selected', len(result.records))} records"
            )
            st.session_state["last_run_total_s"] = result.timings.get("total_s")
            st.session_state["result"] = result
            # One rerun lands on the `elif` branch immediately: the live
            # cards just rendered can't be clicked (nothing's interactive
            # while blocked in pipeline.run()), so the rerun replaces them
            # with the compact done-strip + run-complete cap, and the full
            # per-step detail becomes the "Full execution trace" expander
            # near the foot of the page.
            st.rerun()

        elif st.session_state.get("run_log") and st.session_state.get("result") is not None:
            # Completed state: the run history is now SECONDARY to the results
            # payoff below (ux.md / STEP 5). The four steps stay visible as a
            # compact "it ran, here's how fast" strip -- accumulated ✓✓✓✓ with
            # connectors -- and the per-step detail folds into a single
            # disclosure instead of four full-width expanders competing with
            # "N of 12 themes fired" further down the page.
            log = st.session_state["run_log"]
            st.markdown(
                "".join(
                    charts.exec_step(
                        i + 1, e["title"], e.get("state", "done"),
                        summary=e["summary"], timing=e.get("timing", ""),
                    )
                    for i, e in enumerate(log)
                ),
                unsafe_allow_html=True,
            )
            total_s = st.session_state.get("last_run_total_s")
            failed = any(e.get("state") == "error" for e in log)
            # The console's terminal element: a run-complete cap that closes
            # the execution chapter, so the four ✓ steps read as a finished
            # PROCESS and the eye is handed on to the discovery below rather
            # than stopping here thinking this panel is the output.
            if not failed:
                rc_summary = st.session_state.get("last_run_summary", "")
                st.markdown(
                    '<div class="run-complete"><span class="rc-check">✓</span>'
                    '<span class="rc-label">Run complete</span>'
                    f'<span class="rc-meta">{escape(rc_summary)}'
                    f'{f" · {total_s}s end to end" if total_s else ""}</span></div>',
                    unsafe_allow_html=True,
                )
            # The full per-step execution trace is deliberately NOT here -- it
            # renders as a collapsed disclosure below the discovery results
            # (optional process transparency, not primary output). Keeping it
            # in the console pushed the payoff a whole viewport further down.
        else:
            # Idle: the machine at rest. The four stages are visible from the
            # first load as quiet `pending` cards, so the first viewport is
            # headline + control + visible mechanism -- not headline + button
            # + prose, which is what made this page read as an article about
            # the pipeline rather than the instrument that runs it. `pending`
            # (opacity .58, "waiting") stays clearly distinct from `running`
            # (teal ring + LIVE) and `done` (check + summary), so the idle
            # state can't be mistaken for a completed or null run -- it's the
            # plan, per ux.md's States section.
            st.markdown(
                "".join(
                    charts.exec_step(i + 1, stage_titles[s], "pending", blurb=stage_blurbs[s])
                    for i, s in enumerate(stage_order)
                ),
                unsafe_allow_html=True,
            )

    with st.container(key="settingsdrawer"):
        head_col, close_col = st.columns([3, 1], vertical_alignment="center")
        with head_col:
            st.markdown('<p class="section-id" style="margin:0;">Run settings</p>', unsafe_allow_html=True)
        with close_col:
            if st.button("✕", key="close_settings", use_container_width=True):
                st.session_state.engine_settings_open = False
                st.rerun()
        # Opening the drawer should feel like zooming into the summary chip
        # on the main page, not switching to an unrelated screen -- it
        # restates the same sentence before handing over the controls that
        # edit it.
        st.markdown(
            f'<p class="note" style="margin:4px 0 16px;">Currently: {len(selected_sources)} of '
            f"{len(COLLECTORS)} sources, {n_records} records per run.</p>",
            unsafe_allow_html=True,
        )
        st.markdown('<p class="meta" style="margin:0 0 2px;">What to run</p>', unsafe_allow_html=True)
        st.multiselect(
            "Sources to query",
            options=list(COLLECTORS),
            format_func=lambda s: SOURCE_LABELS.get(s, s),
            help="All four are queried in parallel. Any that fails is reported, never hidden.",
            key="cfg_sources",
        )
        st.slider(
            "Records to classify",
            5,
            20,
            help="Selected from the full fetched pool by keyword relevance.",
            key="cfg_n_records",
        )
        st.write("")
        st.markdown('<p class="meta" style="margin:0 0 2px;">Readiness</p>', unsafe_allow_html=True)
        if ready:
            # Gemini is the only hard requirement (YouTube is optional --
            # missing it degrades to three sources, it doesn't block a run),
            # so "ready" collapses to one line instead of a per-provider list.
            # No panel box for the ready case -- a bordered card for one
            # confirmed-fine line was heavier than the line itself. The
            # panel stays for the not-ready branch below, where it's
            # grouping a real status row with the error message under it.
            st.markdown(
                charts.status_row(
                    "Ready to run",
                    "ok",
                    "Gemini + YouTube configured" if youtube_key() else "Gemini configured, YouTube optional and unset",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="panel" style="padding:12px 14px;">'
                + charts.status_row("Gemini classifier", "bad", "missing, required to classify")
                + charts.status_row(
                    "YouTube Data API",
                    "ok" if youtube_key() else "warn",
                    "configured" if youtube_key() else "missing, YouTube will be skipped",
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            st.error("Set `GEMINI_API_KEY` in Streamlit secrets or a local `.env` file.")

    result: pipeline.RunResult | None = st.session_state.get("result")

    # --------------------------------------------------------------------------
    # Empty state
    # --------------------------------------------------------------------------
    if result is None:
        # Compact methodology -- deliberately NOT the section-id -> <h2> ->
        # .note rhythm Findings gives its own methodology section. On this
        # page the themes are supporting context ("what the engine measures
        # against"), subordinate to the run action, the timeline, and the
        # results. A single label + the chip strip + one disclosure, no
        # editorial heading competing with the console above it.
        st.write("")
        st.write("")
        st.markdown(
            '<div class="engine-measure"><span class="k">Measured against</span>'
            '<span class="v">The same twelve locked themes as Findings. Live records map onto the '
            "Phase 2 set — ten records can't cluster themselves — which is what keeps live discovery "
            "and Findings measuring the same thing.</span></div>",
            unsafe_allow_html=True,
        )
        theme_chips = "".join(
            f'<span class="chip" title="{escape(t["mechanism"])}">{escape(t["theme_id"])} · {escape(t["name"])}</span>'
            for t in load_themes()
        )
        st.markdown(f"<div>{theme_chips}</div>", unsafe_allow_html=True)
        st.write("")
        with st.expander("Theme mechanisms"):
            theme_cards = "".join(
                f'<article class="layer glass reveal-in" style="animation-delay:{i * 0.04:.2f}s">'
                f'<span class="layer-num">{t["theme_id"]}</span>'
                f'<h3>{escape(t["name"])}</h3>'
                f'<p>{escape(t["mechanism"])}</p>'
                f'<div class="source-tags"><span>{t["corpus_share_pct"]}% of corpus</span>'
                f'<span>{t["total_evidence_count"]:,} records</span></div></article>'
                for i, t in enumerate(load_themes())
            )
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));'
                f'gap:14px;">{theme_cards}</div>',
                unsafe_allow_html=True,
            )
        st.stop()

    # --------------------------------------------------------------------------
    # Process -- selection funnel only. The persistent run_log timeline above
    # (Fetch/Normalize/Classify/Validate) already carries the per-source rows
    # and the fetch->normalize counts in its own expandable steps; this
    # section used to restate both (a "sources responded" summary line, then
    # a full "sources queried" list identical to the Fetch step's own detail)
    # a second and third time before the payoff -- three views of the same
    # fetch/normalize data stacked between the timeline and the discovery.
    # The funnel's percentage bars are the one thing not already shown
    # elsewhere, so that stays -- but as a P1 disclosure BELOW the themes and
    # quotes, not between the run and the payoff (see the move further down).
    # --------------------------------------------------------------------------
    # Funnel/records context is shown whenever selection_stats actually has
    # data -- not just when the run fully succeeded. pipeline.run() populates
    # selection_stats as soon as fetch+normalize complete, even if classify
    # fails afterward, so a classify-stage failure still has a real funnel to
    # show. Only the two early-return paths (every source failed, or nothing
    # survived filtering) leave it empty -- that's what this checks, not
    # result.error directly.
    have_stats = bool(result.selection_stats.get("fetched"))
    n_ok = sum(1 for sr in result.source_results if sr.ok)
    summary_line = f"{n_ok} of {len(result.source_results)} sources responded"
    if have_stats:
        summary_line += f" · {result.selection_stats['selected']} records sent to the classifier"

    funnel_html = ""
    if have_stats:
        stats = result.selection_stats
        funnel_html = (
            '<div class="panel" style="padding:14px 18px;">'
            + charts.funnel(
                [
                    ("fetched", stats["fetched"], "across all sources"),
                    ("passed the junk filter", stats["after_junk_filter"], "under 40 characters, link-only, emoji-only"),
                    ("passed the brand gate", stats["after_brand_gate"], f"{stats['dropped_off_brand']} dropped as off-brand"),
                    ("sent to the classifier", stats["selected"], "top-ranked by keyword relevance"),
                ],
                total=stats["fetched"] or 1,
            )
            + '<p class="note" style="margin-top:8px;font-size:12px;">The brand gate drops Ajio, '
            "Meesho and Amazon-only comments (App Store and Play Store reviews are exempt, being "
            "reviews of the Myntra app itself).</p></div>"
        )

    if result.error:
        # A styled panel in the app's own voice, not a bare st.error() red
        # box -- per ux.md's error-state spec, failure should look like the
        # rest of the page, not a foreign component dropped into it. Reserved
        # for the "truly nothing to show" case (ux.md), which is exactly what
        # result.error signals. The failed step itself is already visible,
        # coral-marked, in the run_log timeline above -- no need to restate
        # its source list here too.
        if funnel_html:
            st.markdown(funnel_html, unsafe_allow_html=True)
            st.write("")
        st.markdown(
            '<div class="panel" style="padding:18px 20px;border-left:2px solid var(--coral);">'
            '<p class="meta" style="margin:0 0 6px;color:var(--coral);">Run failed</p>'
            f'<p class="note" style="margin:0;">{escape(result.error)}</p></div>',
            unsafe_allow_html=True,
        )
        st.stop()

    # --------------------------------------------------------------------------
    # Results -- the actual output. One ranked bar chart, exactly the same
    # pattern as "Twelve themes, ranked by volume" on the findings page, plus
    # real evidence quotes from the top themes that fired, styled like
    # Consumer Voices. This replaces five tabs' worth of analyst detail with
    # the one thing a reviewer actually came here to see: does the live
    # pipeline produce output comparable to the static analysis.
    # --------------------------------------------------------------------------
    theme_hits = pipeline.aggregate_themes(result)
    n_classified = len(result.classified)

    # This is the payoff -- the one thing a reader came here to see. The
    # run-complete cap closed the execution chapter inside the console; this
    # connector + chevron (same left axis as the step connectors) flows the
    # eye down out of it into the full-size Discovery heading, so the
    # completed console reads as a process summary the page continues past --
    # composition carrying the EXECUTION -> RUN COMPLETE -> DISCOVERY
    # narrative, not a "scroll down" line.
    st.markdown('<div class="result-flow" aria-hidden="true"></div>', unsafe_allow_html=True)
    # Ties the payoff back to the config that produced it -- the settings
    # drawer is closed and gone by the time this renders, so without this the
    # result has no visible thread back to what was actually run.
    run_from = st.session_state.get("last_run_summary", summary_line)
    st.markdown('<p class="section-id">Discovery</p>', unsafe_allow_html=True)
    # Headline dominates; the methodology it used to carry is stated on the
    # idle screen ("Measured against") and the verbatim-quote guarantee in the
    # trust line below, so here it's one quiet provenance line, not a
    # paragraph competing with the payoff.
    st.markdown(
        f"<h2>{len(theme_hits)} of 12 locked themes fired on {n_classified} live records.</h2>"
        f'<p class="meta" style="margin:10px 0 0;">From {escape(run_from)} · mapped onto the twelve '
        "locked themes, not re-derived.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    if not theme_hits:
        st.markdown(
            '<div class="panel"><p class="note" style="margin:0;">No theme matched. A real '
            "result, not an error: this batch surfaced generic app feedback rather than "
            "decision-journey evidence. Run again for a fresh sample.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        ranked = sorted(theme_hits, key=lambda h: -h.live_count)
        st.markdown(
            f'<div class="panel" style="padding:28px 26px;">'
            + charts.bar_chart(
                [(f"{h.theme_id} · {h.name}", h.live_count, f"of {n_classified}") for h in ranked],
                max_value=n_classified,
                label_width="280px",
            )
            + "</div>",
            unsafe_allow_html=True,
        )

        with_evidence = [h for h in ranked if h.evidence][:3]
        if with_evidence:
            st.write("")
            st.write("")
            q_cols = st.columns(len(with_evidence))
            for i, (col, h) in enumerate(zip(q_cols, with_evidence)):
                e = h.evidence[0]
                with col:
                    link = (
                        f' · <a href="{escape(e["url"], quote=True)}" target="_blank" '
                        'rel="noopener nofollow">source</a>'
                        if e["url"]
                        else ""
                    )
                    # The top-ranked theme's card gets the same "primary"
                    # tinted treatment Consumer Voices gives its lead quote on
                    # the findings page -- one visually anchored card, not
                    # three identical ones, since they aren't equally
                    # important (this is the most-fired theme in the batch).
                    card_class = "quote-card primary glass reveal-in" if i == 0 else "quote-card glass reveal-in"
                    # Trim only the DISPLAYED quote so one long record doesn't
                    # blow the trio's column heights out (same ellipsis pattern
                    # as bar_chart's long labels); full text stays in `title`.
                    # ~120 chars keeps the three cards within roughly one line
                    # of each other -- blockquote runs at clamp(1.1rem,1.8vw,
                    # 1.6rem) in a ~220px column, so a longer quote blows the
                    # trio's heights apart. Full text stays in `title`.
                    q_full = e["quote"]
                    q_disp = q_full if len(q_full) <= 120 else q_full[:118].rstrip() + "…"
                    st.markdown(
                        f'<figure class="{card_class}" style="animation-delay:{i * 0.08:.2f}s;height:100%;">'
                        f'<span class="quote-mark">"</span>'
                        f'<blockquote title="{escape(q_full, quote=True)}">{escape(q_disp)}</blockquote>'
                        f'<figcaption><b>{escape(h.theme_id)}</b> &nbsp; {escape(h.name)}'
                        f'<span class="meta" style="display:block;margin-top:4px;">'
                        f"{SOURCE_LABELS.get(e['source'], e['source'])}{link}</span>"
                        f"</figcaption></figure>",
                        unsafe_allow_html=True,
                    )

    # --------------------------------------------------------------------------
    # P1 detail, deliberately BELOW the payoff: the selection funnel (how the
    # fetched pool narrowed to the classified records) sat between the run and
    # the discovery before, reading as another terminal panel a viewer could
    # stop at. It's real context, not the finding, so it lives here as a quiet
    # disclosure alongside the trust + export line.
    # --------------------------------------------------------------------------
    if funnel_html:
        st.write("")
        with st.expander("How the sample was selected"):
            st.markdown(funnel_html, unsafe_allow_html=True)

    # Optional process transparency: the full per-step trace (source responses,
    # timings, the normalized sample, the classify manifest, the verification
    # detail). Lives here, collapsed, so it never sits between the run and the
    # discovery -- but every step's detail stays one click away.
    run_log = st.session_state.get("run_log")
    if run_log:
        total_s = st.session_state.get("last_run_total_s")
        with st.expander(
            f"Full execution trace{f' · {total_s}s end to end' if total_s else ''}"
        ):
            for i, entry in enumerate(run_log):
                head = f'{i + 1} · {escape(entry["title"])}'
                if entry["summary"]:
                    head += f' — {escape(entry["summary"])}'
                if entry.get("timing"):
                    head += f' · {escape(entry["timing"])}'
                body = entry["detail_html"] or '<span class="note">No detail recorded for this step.</span>'
                st.markdown(
                    f'<p class="meta" style="margin:12px 0 2px;color:var(--teal);">{head}</p>'
                    f'<div class="exec-trace-detail">{body}</div>',
                    unsafe_allow_html=True,
                )

    # --------------------------------------------------------------------------
    # Trust + export -- one line, not a tab. The full detail (every record,
    # every field, run provenance) is still there for anyone who wants it,
    # one click away in the download, rather than filling the page by default.
    # --------------------------------------------------------------------------
    n_issues = sum(len(v) for v in result.validation_issues.values())
    st.write("")
    trust_col, dl_col = st.columns([3, 1], vertical_alignment="center")
    with trust_col:
        if n_issues:
            st.markdown(
                f'<p class="note" style="margin:0;">⚠ {n_issues} quote or label check(s) failed '
                f"verbatim verification across {len(result.validation_issues)} record(s) and were "
                "flagged or dropped. See the downloaded run for detail.</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="note" style="margin:0;">✓ Every quote in this run verified verbatim '
                f"against its source record · {result.timings.get('total_s', '?')}s end to end.</p>",
                unsafe_allow_html=True,
            )
    with dl_col:
        theme_hits_export = theme_hits
        node_rows = pipeline.aggregate_nodes(result)
        export = {
            "run_id": result.run_id,
            "started_at": result.started_at,
            "model": result.model,
            "prompt_version": result.prompt_version,
            "codebook_version": result.codebook_version,
            "timings": result.timings,
            "selection_stats": result.selection_stats,
            "sources": [
                {
                    "source": s.source,
                    "ok": s.ok,
                    "detail": s.detail,
                    "elapsed_s": round(s.elapsed_s, 2),
                    "fetched": len(s.records),
                }
                for s in result.source_results
            ],
            "records": [
                {
                    **rec.to_dict(),
                    "analysis": result.classified.get(rec.evidence_id),
                    "validation_issues": result.validation_issues.get(rec.evidence_id, []),
                }
                for rec in result.records
            ],
            "themes_fired": [
                {
                    "theme_id": h.theme_id,
                    "name": h.name,
                    "live_count": h.live_count,
                    "corpus_share_pct": h.corpus_share_pct,
                    "evidence": h.evidence,
                }
                for h in theme_hits_export
            ],
            "metric_nodes": {n: c for n, _, c in node_rows},
        }
        st.download_button(
            "Download run (JSON)",
            data=json.dumps(export, indent=2, ensure_ascii=False),
            file_name=f"{result.run_id}.json",
            mime="application/json",
            use_container_width=True,
        )

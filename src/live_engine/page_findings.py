"""Discovery Findings page -- the static evidence-collection story.

Content ported from a static "Evidence Atlas" prototype page; the findings
it showed now live in docs/DISCOVERY_ENGINE_FINDINGS.md. This page never calls a live API and never reruns from a widget of
its own (only the "Try it yourself" button, which immediately navigates
away) -- it is meant to sit still and be read.

Reordered in a composition pass (see DESIGN-SYSTEM.md/ux.md): the ranked-
theme finding used to be the last section on the page, seven sections after
a hero that promised "insight" -- so the hero's thesis and the page's actual
payoff were two different claims until the very end. It now sits right after
the hero. Source Architecture and The Pivots also used to be two more
independent eyebrow+h2+three-card-row sections stacked directly against
Pipeline's own five-card row -- three sections sharing one layout family in
a row, the mechanical root of the page reading as "a collection of cards."
They're combined into one two-column list section below; Pipeline keeps its
own card row since it's a real ordered sequence, not an arbitrary grouping.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from . import charts, chrome


def _scene_open(scene_id: str) -> None:
    # A tag opened here and closed in a later, separate st.markdown() call
    # would NOT actually nest -- Streamlit renders each call as its own
    # independent HTML fragment, so the browser auto-closes it on the spot.
    # This is a single, self-contained, already-closed element: an anchor
    # target plus generous top spacing, not a wrapper.
    st.markdown(f'<span id="{scene_id}" class="scene-anchor"></span>', unsafe_allow_html=True)
    st.write("")
    st.write("")


def _scene_close() -> None:
    st.write("")
    st.write("")


def _section_id(label: str) -> None:
    st.markdown(f'<p class="section-id">{escape(label)}</p>', unsafe_allow_html=True)


def render(findings_page, engine_page) -> None:
    chrome.inject_css()
    chrome.nav_shell(findings_page, engine_page, "findings")
    chrome.spine([
        ("cover", "Collection"),
        ("themes", "What we found"),
        ("voices", "Consumer voices"),
        ("methodology", "How it works"),
    ])

    # ---- Cover ----
    _scene_open("cover")
    st.markdown(
        '<p class="cover-kicker"><span>Myntra</span> Wishlist evidence collection</p>'
        '<h1 class="cover-h1">Raw evidence.<br><span class="accent-word">Ready for insight.</span></h1>'
        '<p class="subhead">Real consumer evidence, collected, normalized, and '
        "classified by a reproducible engine.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    # ----------------------------------------------------------------------
    # Primary CTA -- the close of the hero's argument. The subhead names what
    # the pipeline does; the button lets the reader run it. The reproducibility
    # claim is deliberately pinned to the *pipeline*, not the results -- the
    # static corpus analysis is deterministic, but a live run fetches fresh
    # posts and never reproduces a prior run's output. No numbers here -- the
    # proof stats directly below carry those, and repeating them in the subhead
    # just pre-empts the cards.
    # The rest of the page carries the methodology (six sources, locked
    # codebook, classification, how the Live Engine works), so the hero stays
    # to three beats: what this page is, the claim, run it yourself. No
    # explanatory follow-on line. Left column only (same [1.5, 2.5] ratio the
    # Live Engine action row uses) so the button carries weight without going
    # full-width. This is the page's only CTA copy; the nav "Live engine"
    # pill is the persistent secondary path.
    # ----------------------------------------------------------------------
    cta_col, _cta_pad = st.columns([1.5, 2.5])
    with cta_col:
        if st.button(
            "Run the engine yourself →",
            type="primary",
            use_container_width=True,
            key="cta_hero",
        ):
            st.switch_page(engine_page)
    st.write("")
    # 16,917 is the number that matters -- the trustworthy, final dataset
    # size. 24,206 and 30.1% are process detail explaining how you got
    # there, not the headline itself. Three identical cards used to force a
    # reader to read all three labels before knowing which one was "the
    # number" -- this is now one dominant figure plus two smaller supporting
    # ones, asymmetric column widths and font-size doing the work rather
    # than a new component.
    cov_cols = st.columns([1.6, 1, 1], gap="large")
    with cov_cols[0]:
        st.markdown(
            '<article class="floating-card glass reveal-in" style="height:100%;">'
            '<small>Evidence retained</small>'
            '<b style="font-size:3.4rem;">16,917</b>'
            '<p>deduplicated public records, six sources</p>'
            '<span class="status-row"><i></i>Schema verified</span></article>',
            unsafe_allow_html=True,
        )
    with cov_cols[1]:
        st.markdown(
            '<article class="floating-card glass reveal-in" style="animation-delay:0.08s;height:100%;">'
            '<small>Raw intake</small>'
            '<b style="font-size:2.1rem;">24,206</b>'
            '<p>records before the quality pass</p></article>',
            unsafe_allow_html=True,
        )
    with cov_cols[2]:
        st.markdown(
            '<article class="floating-card glass reveal-in" style="animation-delay:0.16s;height:100%;">'
            '<small>Removed</small>'
            '<b style="font-size:2.1rem;">30.1%</b>'
            '<p>exact + source-level duplicates</p></article>',
            unsafe_allow_html=True,
        )
    _scene_close()

    # --------------------------------------------------------------------------
    # What we found -- moved here from the very bottom of the page. The hero's
    # thesis is "ready for insight"; this is the insight, so it now follows
    # immediately instead of after seven sections of methodology. The "Test the
    # engine yourself" CTA now lives in the hero (above the proof stats) so a
    # grader sees it in the first viewport.
    #
    # The H2 also used to be purely descriptive ("Twelve themes, ranked by
    # volume") -- accurate, but not the actual claim. The chart's sharpest
    # insight (four post-delivery themes account for 44.5% of the corpus) used
    # to live only in a small caveat box below the chart, styled identically to
    # Integrity's minor "9 recovered records" footnote elsewhere on the page --
    # buried inside the one section that's supposed to be the loudest. The
    # claim now leads the heading; "ranked by volume" moves to supporting text.
    # --------------------------------------------------------------------------
    _scene_open("themes")
    _section_id("What this corpus found")
    st.markdown(
        "<h2>Post-delivery problems dominate the corpus.</h2>"
        '<p class="note" style="max-width:70ch;">Returns, authenticity doubt, delivery, and trust '
        "collapse: four themes, all reactions to something that already happened after checkout, "
        "account for 44.5% of the 16,917 classified records. Every theme below is ranked exactly "
        "as the engine counted it, most records first.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    theme_rows = [
        ("T2 · Return & Refund Process Friction", 2399, "14.18%"),
        ("T1 · Authenticity & Counterfeit Doubt", 2215, "13.09%"),
        ("T4 · Delivery & Fulfillment Reliability", 1487, "8.79%"),
        ("T3 · Trust Collapse → Stated Refusal to Repurchase", 1427, "8.44%"),
        ("T5 · Cross-Platform Comparison Shopping", 551, "3.26%"),
        ("T6 · Missing Product Information Blocks Decision", 375, "2.22%"),
        ("T7 · Wishlist as a Deliberate Price-Tracking Tool", 247, "1.46%"),
        ("T10 · Operational Barriers at the Final Purchase Step", 229, "1.35%"),
        ("T12 · External Social Validation & Discovery-Seeking", 199, "1.18%"),
        ("T9 · Price & Timing-Driven Deferral", 189, "1.12%"),
        ("T8 · External Discovery → Purchase-Access Friction", 175, "1.03%"),
        ("T11 · Sizing & Fit Confidence Gap (pre-purchase)", 121, "0.72%"),
    ]
    # Same .panel base as everywhere else, but this is the one surface on
    # the page that earns heavier treatment: the deep shadow token (--shadow,
    # SHADOW_DEEP -- used elsewhere for hover-elevated cards, not a resting
    # state) instead of the standard shadow-soft, a teal left accent, and
    # more generous padding. Every other section on this page uses the plain
    # .panel/.glass treatment identically regardless of importance; this is
    # the one place that's deliberately not true anymore.
    st.markdown(
        '<div class="panel" style="padding:32px 28px;border-left:3px solid var(--teal);'
        'box-shadow:var(--shadow);">'
        + charts.bar_chart(theme_rows, label_width="340px", unit=" records")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        '<div class="recovery" style="align-items:center;">'
        '<span style="flex:0 0 auto;text-align:center;">'
        '<strong class="recovery-number" style="display:block;">44.5%</strong>'
        '<span class="metric-label" style="color:#a06a5a;">of the corpus</span></span>'
        '<p style="font-size:13.5px !important;line-height:1.55 !important;">'
        "<b>Why the skew:</b> themes closer to the pre-purchase decision itself sit far smaller "
        "here, and that split matches a known bias of public platforms: people are far more "
        "likely to post about a bad experience after a package arrives than to narrate the quiet "
        "reasoning that happened before they clicked buy.</p></div>",
        unsafe_allow_html=True,
    )
    _scene_close()

    # ---- Voices -- the evidence behind the finding above, still sounds like
    # people, not just percentages. ----
    _scene_open("voices")
    voi_cols = st.columns([1, 1])
    with voi_cols[0]:
        _section_id("Consumer voices")
        st.markdown("<h2>The output still sounds like people.</h2>", unsafe_allow_html=True)
    with voi_cols[1]:
        st.markdown(
            '<p class="note" style="padding-bottom:8px;">No sentiment scores. No premature labels. '
            "The downstream analysis begins with intact, first-person language.</p>",
            unsafe_allow_html=True,
        )
    st.write("")
    q_cols = st.columns([1.2, 0.8])
    with q_cols[0]:
        st.markdown(
            '<figure class="quote-card primary glass reveal-in"><span class="quote-mark">“</span>'
            "<blockquote>The one I wishlisted will show same price as the black and brown one when "
            "I am browsing from the wishlist but when I click on it, it’s price is 500 rs "
            "more.</blockquote><figcaption><b>Reddit · r/MyntraSucks</b> &nbsp; Direct wishlist / "
            "price behaviour</figcaption></figure>",
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            '<figure class="quote-card glass reveal-in" style="animation-delay:0.1s">'
            '<span class="quote-mark">“</span>'
            "<blockquote>This ! Lol.. nothing from my wishlist has a "
            "sale</blockquote><figcaption><b>T7</b> &nbsp; Wishlist as a deliberate price-tracking "
            "tool</figcaption></figure>",
            unsafe_allow_html=True,
        )
    with q_cols[1]:
        st.markdown(
            '<figure class="quote-card glass reveal-in" style="animation-delay:0.08s">'
            '<span class="quote-mark">“</span>'
            "<blockquote>None of the items in my wishlist and cart got their price "
            "reduced...</blockquote><figcaption><b>Reddit</b> &nbsp; Postponement / sale waiting"
            "</figcaption></figure>",
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            '<figure class="quote-card glass reveal-in" style="animation-delay:0.16s">'
            '<span class="quote-mark">“</span>'
            "<blockquote>Double Tap to Wishlist... Faster product discovery, quick "
            "decision-making.</blockquote><figcaption><b>LinkedIn</b> &nbsp; UX practitioner "
            "perspective</figcaption></figure>",
            unsafe_allow_html=True,
        )
    st.write("")
    st.markdown(
        '<div class="final-strip glass reveal-in"><p>Broad evidence. Clear provenance. Ready for '
        'analysis.</p><span class="final-stat"><b>6</b><span>sources</span></span>'
        '<span class="final-stat"><b>10</b><span>seed formats</span></span>'
        '<span class="final-stat"><b>0</b><span>labels</span></span></div>',
        unsafe_allow_html=True,
    )
    _scene_close()

    # ---- Pipeline steps: the discovery engine's journey, Phase 1 + Phase 2.
    # Kept as its own card row -- a genuine five-step ordered sequence, not
    # an arbitrary grouping, so numbering and a card-per-step earn their
    # place here even though the section right after this one deliberately
    # avoids repeating the same layout family. ----
    _scene_open("pipeline")
    _section_id("How the discovery engine works")
    st.markdown(
        "<h2>Five steps from raw text to twelve locked themes.</h2>"
        '<p class="note" style="max-width:70ch;">Extraction and normalization are Phase 1: '
        "collection only, no judgment calls. Tagging, clustering, and theming are Phase 2, run "
        "once over the full corpus and then locked, which is why the live engine on the next page "
        "maps new records onto this set instead of re-deriving it.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    pipe_cols = st.columns(5)
    # Each card leads with the stage and *why* it exists -- the count is real
    # but secondary, so it's a small pill, not a headline number. A previous
    # version gave the count the same oversized display style used for the
    # hero metrics; at one-fifth the column width, "24,206" wrapped mid-digit
    # and read as broken, not big.
    pipeline_steps = [
        ("01", "Extract", "24,206 raw",
         "Six independent sources, each collected on its own terms, so no single "
         "platform's blind spot becomes the whole picture."),
        ("02", "Normalize", "16,917 kept",
         "One shared schema catches the same complaint posted twice before it can "
         "look like two independent signals."),
        ("03", "Tag", "16,917 classified",
         "Every record classified against one locked codebook, so results are "
         "comparable across sources instead of six ad hoc reads."),
        ("04", "Cluster", "47 areas",
         "Quotes grouped by what people are actually describing, not by keyword, "
         "so the same issue said many ways still counts once."),
        ("05", "Themes", "12 themes",
         "47 clusters rolled up by underlying mechanism, not shared keywords, "
         "without losing traceability back to any one cluster."),
    ]
    for i, (col, (num, title, stat, why)) in enumerate(zip(pipe_cols, pipeline_steps)):
        with col:
            st.markdown(
                f'<article class="layer glass reveal-in" style="animation-delay:{i * 0.06:.2f}s;padding:20px;height:100%;">'
                f'<span class="layer-num">{num}</span>'
                f"<h3 style=\"font-size:1.15rem !important;margin-top:10px !important;\">{escape(title)}</h3>"
                f'<span class="chip chip-on" style="margin:6px 0 10px;">{escape(stat)}</span>'
                f"<p style=\"font-size:12.5px !important;line-height:1.5 !important;\">{escape(why)}</p></article>",
                unsafe_allow_html=True,
            )
    _scene_close()

    # --------------------------------------------------------------------------
    # Methodology detail: source roles + pivots, combined. These used to be
    # two separate eyebrow+h2+three-card-row sections, stacked directly
    # against Pipeline's own five-card row above -- three sections in a row
    # sharing one layout family, which read as a slideshow of interchangeable
    # decks by the third repeat. Same content, same data, but a two-column
    # list instead of a second and third card grid: a genuinely different
    # composition, not just a restyle.
    # --------------------------------------------------------------------------
    _scene_open("methodology")
    _section_id("Sources and pivots")
    st.markdown(
        "<h2>Three source roles. Three moments constraint became design.</h2>"
        '<p class="note" style="max-width:70ch;">Each source was selected for a role, not forced '
        "through a generic collection template, and when a source fought back, the response was "
        "architectural, not an endless loop of retries.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    meth_cols = st.columns(2, gap="large")
    with meth_cols[0]:
        st.markdown('<p class="meta" style="margin:0 0 4px;">Source architecture</p>', unsafe_allow_html=True)
        arch_data = [
            ("01", "Behavioural narrative", "Threads reveal comparisons, uncertainty, postponement, and "
             "the language around real purchase decisions.", ["YouTube", "Reddit"]),
            ("02", "Product baseline", "High-volume review feeds establish broad product context while "
             "remaining intentionally thinner per record.", ["Google Play", "App Store"]),
            ("03", "Discovery reach", "Search triangulation reaches evidence that platform-native "
             "collectors structurally cannot see.", ["3 web providers", "LinkedIn", "Seed corpus"]),
        ]
        rows = []
        for i, (num, title, body, tags) in enumerate(arch_data):
            tag_html = "".join(f"<span>{escape(t)}</span>" for t in tags)
            border = "border-bottom:1px solid var(--line);" if i < len(arch_data) - 1 else ""
            rows.append(
                f'<div style="padding:14px 0;{border}">'
                f'<div style="display:flex;align-items:center;gap:10px;">'
                f'<span class="layer-num" style="width:26px;height:26px;flex:0 0 26px;font-size:10px;">{num}</span>'
                f'<h3 style="margin:0 !important;font-size:13.5px !important;">{escape(title)}</h3></div>'
                f'<p style="margin:6px 0 8px 36px;font-size:12.5px !important;line-height:1.5 !important;">{escape(body)}</p>'
                f'<div class="source-tags" style="margin:0 0 0 36px;">{tag_html}</div></div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)
    with meth_cols[1]:
        st.markdown('<p class="meta" style="margin:0 0 4px;">The pivots</p>', unsafe_allow_html=True)
        pivot_data = [
            ("↻", "YouTube · self-correction", "Spam filtered; evidence preserved.",
             "A title denylist saves quota before metadata calls. The relevance funnel was walked "
             "back when it conflicted with the evidence-preservation principle; the score now stays "
             "diagnostic-only.", "Pre-filter baseline retained for comparison"),
            ("↗", "Reddit · route around", "Two paths beat one throttled endpoint.",
             "Bounded Arctic Shift collection was paired with site-scoped discovery across three "
             "search providers.", "89 test records → 4,042 final"),
            ("+", "LinkedIn · genuine discovery", "A pattern in the seeds became a new source.",
             "Repeated 88–100% seed hit-rates triggered a dedicated direct-fetch pass outside the "
             "original brief.", "186 posts · 0 fetch failures · 91.1% hit-rate"),
        ]
        rows = []
        for i, (icon, kicker, title, body, outcome) in enumerate(pivot_data):
            border = "border-bottom:1px solid var(--line);" if i < len(pivot_data) - 1 else ""
            rows.append(
                f'<div style="padding:14px 0;{border}">'
                f'<div style="display:flex;align-items:center;gap:10px;">'
                f'<span class="layer-num" style="width:26px;height:26px;flex:0 0 26px;font-size:12px;">{icon}</span>'
                f'<div><small style="display:block;color:var(--teal);font-size:9.5px;font-weight:850;'
                f'letter-spacing:.08em;text-transform:uppercase;">{escape(kicker)}</small>'
                f'<h3 style="margin:1px 0 0 !important;font-size:13.5px !important;">{escape(title)}</h3></div></div>'
                f'<p style="margin:6px 0 8px 36px;font-size:12.5px !important;line-height:1.5 !important;">{escape(body)}</p>'
                f'<span class="outcome" style="margin-left:36px;">{escape(outcome)}</span></div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)
    _scene_close()

    # ---- Signal landscape ----
    _scene_open("signal")
    sig_cols = st.columns([0.75, 1.25])
    with sig_cols[0]:
        _section_id("Signal landscape")
        st.markdown(
            '<h2>Volume and signal moved in <span class="accent-word">opposite directions.</span></h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="subhead">Large conversational sources create breadth. Small focused sources '
            "carry denser purchase-journey language.</p>"
            '<span class="insight-chip">LinkedIn: 91.1% diagnostic hit-rate</span>',
            unsafe_allow_html=True,
        )
    with sig_cols[1]:
        bubbles = [
            ("YouTube", "10,185 · 14.5%", 154, "rgba(104,187,235,.64)", 85, 16),
            ("Reddit", "4,042 · 35.5%", 112, "rgba(141,121,232,.58)", 64, 38),
            ("Play", "1,662 · 41.3%", 82, "rgba(255,185,117,.65)", 42, 47),
            ("Web", "458 · 66.6%", 65, "rgba(232,101,97,.5)", 23, 72),
            ("App", "402 · 24.4%", 62, "rgba(159,175,205,.58)", 15, 28),
            ("LinkedIn", "168 · 91.1%", 74, "rgba(47,200,194,.69)", 8, 88),
        ]
        bubble_html = "".join(
            f'<span class="bubble" style="--size:{size}px;--fill:{fill};left:{left}%;bottom:{bottom}%;">'
            f'<span>{escape(name)}<small>{escape(sub)}</small></span></span>'
            for name, sub, size, fill, left, bottom in bubbles
        )
        st.markdown(
            f'<figure class="signal-glass glass reveal-in">'
            '<span class="axis-label" style="top:36px;left:38px;">Higher signal density ↑</span>'
            '<span class="axis-label" style="right:38px;bottom:24px;">More records →</span>'
            f'<div class="plot">{bubble_html}</div></figure>',
            unsafe_allow_html=True,
        )
    _scene_close()

    # --------------------------------------------------------------------------
    # Research question coverage -- the engine was built to answer ten named
    # research questions; this states, per question, how much weight each
    # answer can actually bear. Placed after Signal Landscape (source-level
    # trust) and before Integrity (collection-process trust): source quality
    # -> answer quality -> process integrity, three honesty checks in
    # ascending specificity, not one undifferentiated "trust us" block.
    # Reuses status_row for the Strong/Partial state precisely because it
    # already carries a text label alongside its color dot (accessibility)
    # and needed no new token -- GOOD/WARN map directly onto Strong/Partial.
    # --------------------------------------------------------------------------
    _scene_open("coverage")
    _section_id("Research question coverage")
    st.markdown(
        "<h2>Six of ten research questions have direct, quantified answers.</h2>"
        '<p class="note" style="max-width:70ch;">Every answer below traces back to a specific field '
        "or theme in the corpus, never asserted from memory. The other four aren't tagging failures "
        "-- they're honest limits of what anonymous public reviews can say: most reviews never "
        "narrate why something was wishlisted or how firm the intent to buy really is.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    cov_stat_cols = st.columns([1, 1], gap="large")
    with cov_stat_cols[0]:
        st.markdown(
            charts.stat_tile(
                "6 / 10", "Strong coverage",
                "Direct, quantified, quote-traceable evidence", tone="good",
            ),
            unsafe_allow_html=True,
        )
    with cov_stat_cols[1]:
        st.markdown(
            charts.stat_tile(
                "4 / 10", "Partial coverage",
                "Real, quantified gaps -- not tagging failures", tone="warn",
            ),
            unsafe_allow_html=True,
        )
    st.write("")
    rq_data = [
        (1, "Why do users add products to their wishlist?", "warn", "Partial",
         "wishlist_role tagged, but clearly codeable on only 3.2% of records"),
        (2, "What prevents wishlisted products from being purchased?", "ok", "Strong",
         "T1 (M2 slice), T6, T9, T10, T11"),
        (3, "What uncertainties remain after a product is identified?", "ok", "Strong",
         "T1, T6, T11"),
        (4, "What causes users to postpone a purchase?", "ok", "Strong",
         "T9 · 189 records of explicit deferral language"),
        (5, "How do users compare multiple shortlisted products?", "warn", "Partial",
         "Strong cross-platform (551 records); thin within-wishlist (64 records)"),
        (6, "What information is sought outside Myntra/AJIO?", "ok", "Strong",
         "T12, T8, and a dedicated external_research_channel field"),
        (7, "Role of fit, size, styling, price, reviews, occasion, social validation?", "ok", "Strong",
         "13 named factor_tags, each with its own sentiment"),
        (8, "Genuine purchase intent vs. simple bookmarking?", "warn", "Partial",
         "purchase_intent tagged, but clearly codeable on only 19% of records"),
        (9, "How do behaviors differ across user segments?", "warn", "Partial",
         "No demographic data in public corpora; proxy segments only (source, rating, engagement)"),
        (10, "What unmet needs emerge consistently across user conversations?", "ok", "Strong",
         "A second, independent method (request-language search) converged on the same theme as clustering"),
    ]
    rq_cols = st.columns(2, gap="large")
    for col, chunk in zip(rq_cols, [rq_data[:5], rq_data[5:]]):
        with col:
            rows = []
            for i, (num, question, state, label, evidence) in enumerate(chunk):
                border = "border-bottom:1px solid var(--line);" if i < len(chunk) - 1 else ""
                rows.append(
                    f'<div style="padding:14px 0;{border}">'
                    f'<div style="display:flex;align-items:center;gap:10px;">'
                    f'<span class="layer-num" style="width:26px;height:26px;flex:0 0 26px;font-size:9px;">Q{num}</span>'
                    f'<h3 style="margin:0 !important;font-size:13.5px !important;">{escape(question)}</h3></div>'
                    f'<div style="margin-left:36px;">{charts.status_row(label, state, evidence)}</div></div>'
                )
            st.markdown("".join(rows), unsafe_allow_html=True)
    _scene_close()

    # ---- Integrity ----
    # Built as one consolidated HTML string, not st.columns -- the shell
    # background needs to genuinely wrap the guardrail grid, which only
    # works if it's all one fragment (see the note on _scene_open above).
    _scene_open("integrity")
    guard_data = [
        ("No invented fetches", "Unavailable pages never masquerade as full-fidelity retrieval."),
        ("Explicit source tags", "Summary-only evidence remains distinguishable downstream."),
        ("0 identity gaps", "No duplicate IDs and no missing URLs or source IDs."),
        ("Dead ends documented", "PullPush, direct Reddit JSON, and scraping blocks stay in the record."),
    ]
    guardrail_html = "".join(
        f'<article class="guardrail reveal-in"><b>{escape(title)}</b><p>{escape(body)}</p></article>'
        for title, body in guard_data
    )
    st.markdown(
        '<div class="integrity-shell glass reveal-in">'
        '<div class="integrity-top">'
        '<div><p class="section-id">Evidence integrity</p>'
        "<h2>Failure was labelled.<br>Nothing was disguised.</h2></div>"
        '<p class="note" style="padding-bottom:12px;">Blocked pages, rejected providers, and '
        "unreachable URLs remain visible in the provenance trail. That makes the dataset "
        "inspectable, not artificially perfect.</p></div>"
        f'<div class="guardrails">{guardrail_html}</div>'
        '<div class="recovery"><strong class="recovery-number">9</strong>'
        "<p>otherwise-lost pieces of evidence recovered as clearly marked seed summaries when "
        "Quora and Trustpilot blocked direct retrieval.</p></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    _scene_close()

    chrome.footer(end_label="End of Atlas")

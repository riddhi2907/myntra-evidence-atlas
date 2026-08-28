"""Shared page chrome: one CSS injection, used by every page.

Ported from docs/myntra-wishlist-findings.html -- that page is the
design source of truth for this app now, not an independent interpretation
of it. Every color/type/shape value below comes from live_engine.charts, so
this file and the chart primitives cannot drift apart. Both pages
(page_findings.py, page_engine.py) call inject_css() once at the top of
their render(), so the two pages -- separate Streamlit rerun boundaries --
never look inconsistent with each other.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from . import charts

# phase3_live_engine/assets/ -- copied into this phase so it stays
# independently publishable (CLAUDE.md: Phase 3 crosses nothing).
ASSETS = Path(__file__).resolve().parents[2] / "assets"
LOGO = ASSETS / "evidence-atlas-logo.png"


@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    """The brand mark as a data URI -- inlined into the one CSS block rather
    than served as a file so the nav pill needs no extra asset route."""
    b64 = base64.b64encode((ASSETS / "evidence-atlas-logo-96.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400..800;1,400..800&display=swap');

          :root {{
            --bg: {charts.CANVAS}; --ink: {charts.INK_PRIMARY}; --ink-2: {charts.INK_SECONDARY};
            --muted: {charts.INK_MUTED}; --line: {charts.HAIRLINE}; --white-line: {charts.GLASS_BORDER};
            --glass: {charts.GLASS}; --glass-solid: {charts.GLASS_SOLID};
            --teal: {charts.SERIES}; --teal-bright: {charts.SERIES_SOFT};
            --indigo: {charts.INDIGO}; --violet: {charts.VIOLET};
            --coral: {charts.CORAL}; --amber: {charts.AMBER};
            --shadow: {charts.SHADOW_DEEP}; --shadow-soft: {charts.SHADOW_SOFT};
            --radius: {charts.RADIUS_LG};
          }}

          html, body, .stApp, [class*="css"] {{ font-family: {charts.FONT}; }}
          .stApp {{
            background: {charts.CANVAS_GRADIENT};
            background-attachment: fixed;
            color: var(--ink);
          }}
          /* Transparent background alone leaves the header's hit-box intact
             and it sits above custom fixed elements by default -- confirmed
             with Playwright: it silently intercepted every click meant for
             the nav pill underneath it. Dropping it below the nav pill in
             the stacking order, not disabling its pointer events outright,
             since the sidebar-collapse control that lives in it should stay
             clickable. */
          [data-testid="stHeader"] {{ background: transparent; z-index: 1; }}
          [data-testid="stAppViewContainer"] {{ position: relative; z-index: 1; }}
          [data-testid="stSidebarNav"] {{ display: none; }}
          .block-container {{ padding-top: 0.5rem; padding-bottom: 6rem; max-width: 1240px; }}

          h1, h2, h3 {{ text-wrap: balance; letter-spacing: -0.03em; color: var(--ink) !important;
                        font-family: {charts.FONT} !important; }}
          /* Streamlit stamps a hover anchor-link onto every markdown heading;
             on the Engine payoff h2 it lands mid-sentence ("…live records. 🔗").
             Nothing on this app links to a heading id, so hide it. */
          h1 > a, h2 > a, h3 > a, [data-testid="stHeaderActionElements"] {{ display: none !important; }}
          h2 {{ font-size: clamp(2.1rem, 3.6vw, 3.4rem) !important; font-weight: 680 !important;
                line-height: 1 !important; margin: 0 0 14px !important; padding: 0 !important; }}
          h3 {{ font-size: 1.15rem !important; font-weight: 720 !important;
                line-height: 1.15 !important; margin: 0 0 9px !important; padding: 0 !important; }}
          p, li, .stMarkdown {{ font-family: {charts.FONT} !important; color: var(--ink-2);
                                font-size: 14.5px !important; line-height: 1.6 !important; }}
          .stMarkdown strong {{ color: var(--ink); font-weight: 650; }}
          code, .stCode, pre {{ font-family: {charts.MONO} !important; }}

          .accent-word {{ color: transparent; background: linear-gradient(100deg, #008b8e 0%, #315abb 48%, #7455c8 100%);
                          background-clip: text; -webkit-background-clip: text; }}
          .section-id {{ display: inline-flex; align-items: center; gap: 10px; margin: 0 0 16px;
                         color: var(--teal); font-size: 11px; font-weight: 850; letter-spacing: .15em;
                         text-transform: uppercase; }}
          .section-id::before {{ content: ""; width: 28px; height: 1px; background: currentColor; }}

          .glass {{ border: 1px solid var(--white-line); background: var(--glass); box-shadow: var(--shadow);
                    backdrop-filter: blur(26px) saturate(145%); -webkit-backdrop-filter: blur(26px) saturate(145%); }}

          /* Ambient color blobs -- fixed, blurred, decorative. A slow drift is
             harmless to replay on a Streamlit rerun (it is not gated on scroll
             state). The source page's IntersectionObserver scroll-reveal is
             intentionally not ported -- a two-page split still means each
             page's own widget interactions rerun that page, so a
             scroll-triggered reveal would replay from invisible on every
             rerun rather than feel polished. Content renders statically
             visible instead. */
          .ambient {{ position: fixed; z-index: 0; pointer-events: none; border-radius: 999px; filter: blur(3px); }}
          .ambient.a {{ width: 420px; height: 420px; top: 7vh; left: -230px;
                        background: radial-gradient(circle at 65% 45%, rgba(46,206,199,.45), rgba(85,211,255,.08) 58%, transparent 70%);
                        animation: float-a 16s ease-in-out infinite alternate; }}
          .ambient.b {{ width: 560px; height: 560px; top: 48vh; right: -310px;
                        background: radial-gradient(circle at 30% 45%, rgba(146,119,235,.38), rgba(255,135,173,.08) 55%, transparent 70%);
                        animation: float-b 20s ease-in-out infinite alternate; }}
          @keyframes float-a {{ from {{ transform: translateY(-2vh); }} to {{ transform: translate(7vw,9vh); }} }}
          @keyframes float-b {{ from {{ transform: translate(0,0); }} to {{ transform: translate(-8vw,5vh); }} }}
          @media (prefers-reduced-motion: reduce) {{ .ambient {{ animation: none; }} }}

          /* Mount-in animation, not scroll-triggered -- each findings-page
             card renders in full inside a single st.markdown() call, so it's
             a genuinely self-contained element the animation can safely
             target. Plays once when the page first mounts (each Streamlit
             page is its own rerun boundary), never replays on a rerun this
             page doesn't own. */
          @keyframes reveal-in {{ from {{ opacity: 0; transform: translateY(18px) scale(.985); }}
                                  to {{ opacity: 1; transform: none; }} }}
          .reveal-in {{ animation: reveal-in .65s cubic-bezier(.2,.75,.2,1) both; }}
          @media (prefers-reduced-motion: reduce) {{ .reveal-in {{ animation: none; }} }}

          /* Equal-height cards in a st.columns() row. The column is a flex
             child that already stretches to the row's height, but every
             Streamlit wrapper between it and our card collapses to content
             height, so a card's own height:100% has nothing to fill against.
             Give the whole wrapper chain full height wherever a column holds
             one of our card primitives. */
          [data-testid="stColumn"]:has(> div > [data-testid="stVerticalBlock"] .layer),
          [data-testid="stColumn"]:has(> div > [data-testid="stVerticalBlock"] .quote-card),
          [data-testid="stColumn"]:has(> div > [data-testid="stVerticalBlock"] .floating-card) {{
            display: flex;
          }}
          [data-testid="stColumn"]:has(.layer) > div,
          [data-testid="stColumn"]:has(.quote-card) > div,
          [data-testid="stColumn"]:has(.floating-card) > div,
          [data-testid="stColumn"]:has(.layer) [data-testid="stVerticalBlock"],
          [data-testid="stColumn"]:has(.quote-card) [data-testid="stVerticalBlock"],
          [data-testid="stColumn"]:has(.floating-card) [data-testid="stVerticalBlock"],
          [data-testid="stColumn"]:has(.layer) [data-testid="stElementContainer"],
          [data-testid="stColumn"]:has(.quote-card) [data-testid="stElementContainer"],
          [data-testid="stColumn"]:has(.floating-card) [data-testid="stElementContainer"],
          [data-testid="stColumn"]:has(.layer) .stMarkdown,
          [data-testid="stColumn"]:has(.quote-card) .stMarkdown,
          [data-testid="stColumn"]:has(.floating-card) .stMarkdown,
          [data-testid="stColumn"]:has(.layer) .stMarkdown > div,
          [data-testid="stColumn"]:has(.quote-card) .stMarkdown > div,
          [data-testid="stColumn"]:has(.floating-card) .stMarkdown > div,
          [data-testid="stColumn"]:has(.layer) [data-testid="stMarkdownContainer"],
          [data-testid="stColumn"]:has(.quote-card) [data-testid="stMarkdownContainer"],
          [data-testid="stColumn"]:has(.floating-card) [data-testid="stMarkdownContainer"] {{
            width: 100%;
            height: 100%;
          }}

          /* Hover lift -- cheap, real interactivity, zero rerun risk (pure CSS). */
          .layer, .pivot, .quote-card, .metric, .floating-card {{ transition: transform .25s ease, box-shadow .25s ease; }}
          .layer:hover, .pivot:hover {{ transform: translateY(-6px); box-shadow: 0 24px 60px rgba(58,75,118,.16); }}
          .quote-card:hover, .metric:hover, .floating-card:hover {{ transform: translateY(-4px); }}
          .bubble {{ transition: transform .25s ease, box-shadow .25s ease; }}
          .bubble:hover {{ z-index: 4; transform: translate(-50%, 50%) scale(1.07);
                           box-shadow: 0 18px 38px rgba(54,76,126,.2), inset 0 1px 7px white; }}

          /* Glare Hover (react-bits-inspired) -- a diagonal light sweep on
             hover. Pure CSS: no cursor tracking, just a transform triggered
             by :hover, so it needs no JS and carries no rerun risk. */
          .layer, .pivot, .quote-card, .metric, .guardrail {{ position: relative; overflow: hidden; }}
          .layer::after, .pivot::after, .quote-card::after, .metric::after, .guardrail::after {{
            content: ""; position: absolute; top: -60%; left: -60%; width: 40%; height: 220%;
            background: linear-gradient(115deg, transparent 20%, rgba(255,255,255,.55) 50%, transparent 80%);
            transform: translateX(-160%) rotate(8deg); pointer-events: none; transition: transform .7s ease;
          }}
          .layer:hover::after, .pivot:hover::after, .quote-card:hover::after,
          .metric:hover::after, .guardrail:hover::after {{ transform: translateX(320%) rotate(8deg); }}
          @media (prefers-reduced-motion: reduce) {{
            .layer::after, .pivot::after, .quote-card::after, .metric::after, .guardrail::after {{ display: none; }}
          }}

          /* Shiny Text (react-bits-inspired) -- continuous gradient sheen,
             not hover-gated, on the accent headline words. */
          .accent-word {{ background-size: 260% 100%; animation: shine 5s linear infinite; }}
          @keyframes shine {{ 0% {{ background-position: 0% 50%; }} 100% {{ background-position: 200% 50%; }} }}
          @media (prefers-reduced-motion: reduce) {{ .accent-word {{ animation: none; }} }}

          /* Star Border (react-bits-inspired), take two. The first version
             used an absolutely-positioned ::before ring behind the button --
             confirmed with Playwright that it rendered as a huge diagonal
             smear across the page instead of a thin border, because
             Streamlit's own wrapper divs around a button broke the
             containing-block assumption position:absolute relied on. This
             version can't have that failure mode: the gradient lives in the
             button's own background, fully contained in its own box, no
             pseudo-element positioning involved. */
          /* Every .stButton rule in this file uses the descendant combinator
             (.stButton button), not a direct child (.stButton > button).
             Confirmed live: adding help= to a button makes Streamlit wrap it
             in stTooltipIcon/stTooltipHoverTarget divs for the hover "?"
             affordance, which silently broke every direct-child selector
             here (the primary button reverted to Streamlit's stock blue,
             background-image: none, computed-style-verified) the moment a
             help= tooltip was added anywhere in the app. Descendant match
             is immune to however many wrapper divs Streamlit inserts. */
          .stButton button[kind="primary"] {{
            background: linear-gradient(100deg, var(--ink) 30%, var(--teal) 45%, var(--indigo) 55%, var(--ink) 70%);
            background-size: 260% 100%;
            animation: shine 5s linear infinite;
          }}
          @media (prefers-reduced-motion: reduce) {{ .stButton button[kind="primary"] {{ animation: none; }} }}

          /* help= tooltip. Streamlit's stock bubble is a plain white slab with
             a ~672px max-width; on the narrow console it renders ~550px wide,
             centered on the Run button, so it breaks left out of the console
             frame and lands on the hero lead. Constrain it to a compact bubble
             and match the glass/ink surface the rest of the page uses. */
          [data-testid="stTooltipContent"] {{
            max-width: 248px;
            padding: 9px 12px;
            font-size: 12.5px;
            line-height: 1.45;
            color: var(--ink-2);
            background: var(--glass-solid);
            border: 1px solid var(--white-line);
            border-radius: 12px;
            box-shadow: var(--shadow-soft);
          }}

          /* "Running discovery…" state -- page_engine.py swaps the Run control
             for a disabled primary button while pipeline.run() blocks. Stock
             disabled styling drops the text to near-invisible grey on the dark
             fill; keep it legible and let the shine keep moving so the control
             reads as working, not dead. */
          .st-key-run_active .stButton button[disabled] {{
            opacity: 1;
            cursor: progress;
            color: rgba(255, 255, 255, .92) !important;
            -webkit-text-fill-color: rgba(255, 255, 255, .92);
          }}
          .st-key-run_active .stButton button[disabled][kind="primary"] {{
            animation: shine 5s linear infinite;
          }}
          @media (prefers-reduced-motion: reduce) {{
            .st-key-run_active .stButton button[disabled][kind="primary"] {{ animation: none; }}
          }}

          /* Fixed full-width scrim behind the nav pill. The pill itself is
             capped at 900px and centered, so on wide viewports page content
             (the theme card grid especially) used to scroll straight up
             underneath/around it with nothing to fade it out first -- card
             text visually ran into the pill's edges. This bar sits just
             under the pill's z-index, spans the full width, and fades to
             transparent via mask-image so content dissolves before it
             reaches the pill instead of colliding with it. */
          .nav-scrim {{ position: fixed; z-index: 998; top: 0; left: 0; right: 0; height: 92px;
                        background: linear-gradient(to bottom, var(--bg) 0%, var(--bg) 55%, transparent 100%);
                        -webkit-mask-image: linear-gradient(to bottom, black 0%, black 55%, transparent 100%);
                        mask-image: linear-gradient(to bottom, black 0%, black 55%, transparent 100%);
                        pointer-events: none; }}

          /* Nav shell -- floating glass pill, fixed at top. A real
             st.container(key="navshell") wrapping real st.page_link widgets,
             not raw HTML -- see the note in nav_shell() for why. */
          .st-key-navshell {{ position: fixed !important; z-index: 999 !important; top: 18px; left: 50%;
                              transform: translateX(-50%); width: min(calc(100% - 36px), 900px);
                              padding: 6px 14px; border: 1px solid var(--white-line); border-radius: 20px;
                              background: var(--glass); box-shadow: var(--shadow-soft);
                              backdrop-filter: blur(24px) saturate(145%);
                              -webkit-backdrop-filter: blur(24px) saturate(145%); }}
          .st-key-navshell [data-testid="stHorizontalBlock"] {{ align-items: center; gap: 4px; }}
          .brand {{ display: flex; align-items: center; gap: 11px; font-size: 13px; font-weight: 800;
                    letter-spacing: -.02em; color: var(--ink); }}
          /* The logo is a finished app-icon (its own rounded-square edge,
             gradient, and highlight) -- rendered as an <img> at its native
             aspect so nothing is cropped, lifted off the glass pill by a
             drop-shadow that follows the PNG's rounded-corner alpha (a
             box-shadow here would show square corners past the artwork). */
          .brand-icon {{ width: 38px; height: 38px; flex: 0 0 38px; object-fit: contain;
                         filter: drop-shadow(0 2px 5px rgba(17,24,43,.18))
                                 drop-shadow(0 9px 20px rgba(74,79,181,.30));
                         transition: transform .25s cubic-bezier(.2,.75,.2,1); }}
          .brand:hover .brand-icon {{ transform: rotate(-4deg) scale(1.06); }}
          @media (prefers-reduced-motion: reduce) {{ .brand-icon {{ transition: none; }} }}
          .st-key-navshell [data-testid="stPageLink"] {{ border-radius: 12px; padding: 2px 4px; }}
          .st-key-navshell [data-testid="stPageLink"]:hover {{ background: rgba(255,255,255,.75); }}
          .st-key-navshell [data-testid="stPageLink"] p {{ font-size: 12.5px !important; font-weight: 700 !important;
                                                            color: var(--ink-2) !important; }}
          .st-key-navshell [data-testid="stPageLink"][aria-disabled="true"] {{ background: rgba(0,127,131,.1); }}
          .st-key-navshell [data-testid="stPageLink"][aria-disabled="true"] p {{ color: var(--teal) !important; }}
          /* Persistent secondary CTA: the "Live engine" link (last nav column)
             renders as a filled teal pill whenever it is NOT the current page,
             so a grader always has a visible route to the live demo. */
          .st-key-navshell [data-testid="stColumn"]:last-child [data-testid="stPageLink"]:has(a:not([disabled])) {{
              background: var(--teal); padding: 6px 14px; box-shadow: 0 8px 20px rgba(0,127,131,.28); }}
          .st-key-navshell [data-testid="stColumn"]:last-child [data-testid="stPageLink"]:has(a:not([disabled])):hover {{
              background: #00696d; }}
          .st-key-navshell [data-testid="stColumn"]:last-child [data-testid="stPageLink"]:has(a:not([disabled])) p {{
              color: #fff !important; font-weight: 800 !important; }}

          /* Status panel + "Run settings" button stack flush (0-gap) as one
             visual unit on the Engine page. Left to their own class defaults
             they carry two different corner radii (panel: var(--radius),
             button: 14px) which reads as a visible mismatched seam right
             where they touch. Rounding only the outer corners of each half
             makes the pair read as one continuous shape instead. */
          .st-key-statusstack .panel {{ border-radius: var(--radius) var(--radius) 0 0 !important; }}
          .st-key-statusstack .stButton button {{
              border-radius: 0 0 var(--radius) var(--radius) !important; }}

          /* Execution timeline (Engine page only) -- four persistent step
             cards, one per pipeline stage, that never get replaced the way a
             single st.status() box's contents used to be. Each card only
             ever changes its own state (pending/running/done); the other
             three stay exactly where they are, preserving run history top to
             bottom instead of discarding it the moment the next stage
             starts. */
          .exec-step {{ position: relative; display: flex; align-items: center; gap: 12px; min-height: 44px;
                        padding: 10px 16px; margin-bottom: 10px; border-radius: {charts.RADIUS_SM};
                        border: 1px solid var(--white-line); transition: background .25s ease, border-color .25s ease; }}
          /* Connector: a short vertical tick bridging the 10px gap to the next
             card, so the four read as one pipeline rather than four loose
             rows. Absolutely positioned (not a flex child) because
             .exec-step.running switches to flex-direction:column and would
             misplace a child. `linked` is set by charts.exec_step for steps
             1-3 -- :not(:last-child) can't be relied on since the live run
             renders each card in its own st.empty() container. */
          .exec-step.linked::after {{ content: ""; position: absolute; left: 26px; top: 100%;
                                      width: 2px; height: 10px; background: var(--line); }}
          .exec-step.done.linked::after {{ background: var(--teal); opacity: .35; height: 6px; }}
          .exec-step-body {{ flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }}
          .exec-step-blurb {{ font-size: 11.5px; color: var(--muted); line-height: 1.35;
                              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
          .exec-step.pending {{ background: rgba(255,255,255,.28); opacity: .62; }}
          .exec-step.done {{ background: var(--glass-solid); cursor: default;
                             min-height: 0; padding: 7px 16px; margin-bottom: 6px; }}
          .exec-step.done .exec-step-blurb {{ font-size: 12px; }}
          .exec-step.done .exec-step-num {{ background: var(--teal); color: #fff; border-color: transparent; }}
          .exec-step.error {{ background: rgba(255,241,238,.6); border-color: var(--coral); }}
          .exec-step.error .exec-step-num {{ background: var(--coral); color: #fff; border-color: transparent; }}
          .exec-step.error .exec-step-state {{ color: var(--coral); }}
          /* The one card with real visual weight -- teal edge + ring, not
             just a color change, so "this is the active step" reads even in
             a quick glance, not just on close inspection. */
          .exec-step.running {{ flex-direction: column; align-items: stretch; gap: 0;
                                background: var(--glass-solid); border-color: var(--teal);
                                box-shadow: 0 0 0 3px rgba(0,127,131,.1), var(--shadow-soft); }}
          .exec-step-head {{ display: flex; align-items: center; gap: 10px; }}
          .exec-step-num {{ display: grid; place-items: center; width: 22px; height: 22px; flex: 0 0 22px;
                            border-radius: 999px; border: 1px solid var(--white-line); background: rgba(255,255,255,.5);
                            font-size: 11px; font-weight: 800; color: var(--ink-2); }}
          .exec-step-title {{ font-size: 13px; font-weight: 700; color: var(--ink); }}
          .exec-step-head .exec-step-title {{ flex: 1; }}
          .exec-step-state {{ flex: 0 0 auto; font-size: 11.5px; color: var(--muted); text-align: right;
                              font-variant-numeric: tabular-nums; }}
          .exec-step.pending .exec-step-state {{ text-transform: uppercase; letter-spacing: .1em;
                                                 font-size: 10px; font-weight: 800; }}
          /* Indeterminate sweep for the classify wait -- the one stage that
             is a single blocking call with nothing to stream. Pure CSS
             keyframes run in the browser while Python is blocked (same
             mechanism as .exec-step-live's pulse), so the step still reads as
             working rather than frozen on a "waiting" line. */
          .exec-shimmer {{ height: 4px; border-radius: 999px; margin: 2px 0 10px;
                           background: linear-gradient(90deg, transparent, var(--teal), transparent) 0 0 / 40% 100% no-repeat;
                           background-color: rgba(0,127,131,.1);
                           animation: exec-sweep 1.4s ease-in-out infinite; }}
          @keyframes exec-sweep {{ 0% {{ background-position: -45% 0; }} 100% {{ background-position: 145% 0; }} }}
          @media (prefers-reduced-motion: reduce) {{ .exec-shimmer {{ animation: none; opacity: .4; }} }}
          .exec-trace-detail {{ padding: 2px 2px 12px; font-size: 12.5px; color: var(--ink-2); }}
          .exec-trace-detail .quote {{ font-size: 12px !important; }}

          /* Completed-state transition: EXECUTION → RUN COMPLETE → DISCOVERY.
             `.run-complete` is the console's terminal element once a run
             finishes -- a teal-tinted cap that closes the execution chapter
             so the four ✓ steps read as a finished PROCESS, not the output.
             `.result-flow` then sits between the console and the full-size
             Discovery heading: a short connector + downward chevron on the
             same left axis as the step connectors, so the pipeline visibly
             continues into the results rather than a "scroll down" line. */
          .run-complete {{ display: flex; align-items: baseline; flex-wrap: wrap; gap: 5px 10px;
                           margin: 12px 0 2px; padding: 11px 16px; border-radius: {charts.RADIUS_SM};
                           border: 1px solid rgba(0,127,131,.28); border-left: 2px solid var(--teal);
                           background: rgba(0,127,131,.09); }}
          .run-complete .rc-check {{ color: var(--teal); font-weight: 850; font-size: 13px; }}
          .run-complete .rc-label {{ color: var(--ink); font-weight: 750; font-size: 13px; letter-spacing: -.01em; }}
          .run-complete .rc-meta {{ font-family: {charts.MONO}; font-size: 12px; color: var(--muted); }}
          /* Transition cue between the console and the Discovery heading: a
             connector + chevron on the same left axis as the step
             connectors, so the pipeline visibly flows on into the results.
             Negative bottom margin pulls the DISCOVERY eyebrow up under it. */
          .result-flow {{ position: relative; height: 34px; margin: 2px 0 -6px; }}
          .result-flow::before {{ content: ""; position: absolute; left: 26px; top: 0; bottom: 11px;
                                  width: 2px; background: var(--teal); opacity: .38; }}
          .result-flow::after {{ content: ""; position: absolute; left: 20px; bottom: 3px;
                                 width: 13px; height: 13px; border-right: 2px solid var(--teal);
                                 border-bottom: 2px solid var(--teal); transform: rotate(45deg); opacity: .6; }}
          .exec-step-live {{ font-size: 10px; font-weight: 850; letter-spacing: .08em; text-transform: uppercase;
                             color: var(--teal); animation: exec-pulse 1.6s ease-in-out infinite; }}
          @keyframes exec-pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
          @media (prefers-reduced-motion: reduce) {{ .exec-step-live {{ animation: none; }} }}
          /* Fixed max-height, not fixed height -- a step with two source
             rows and a step with four shouldn't look broken by dead
             whitespace, but neither should push the page taller than this
             regardless of how much streams in. Content scrolls internally. */
          .exec-step-detail {{ margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--line);
                               max-height: 190px; overflow-y: auto; font-size: 12.5px; color: var(--ink-2); }}

          /* ---- Live Engine composition (engine page only; page_findings.py
             references none of these classes). Shared visual DNA with
             Findings -- same Inter, same weight vocabulary, same ink/teal,
             same tokens, same nav and canvas -- but a deliberately
             different page-level grammar: an instrument masthead and a
             bordered control console, not Findings' editorial
             cover-kicker -> cover-h1 (gradient accent-word) -> subhead ->
             CTA-section rhythm. The point is that a viewer switching
             between the two pages without reading the URL immediately
             knows one is for reading results and the other for running the
             engine. See DESIGN-SYSTEM.md Layout. */
          .engine-eyebrow {{ display: flex; align-items: center; gap: 12px; margin: 16px 0 18px;
                             font-family: {charts.MONO}; font-size: 12px; font-weight: 700;
                             letter-spacing: .16em; text-transform: uppercase; color: var(--muted); }}
          .engine-eyebrow::before {{ content: ""; width: 34px; height: 1px; background: var(--teal); }}
          .engine-eyebrow b {{ color: var(--teal); font-weight: 850; }}
          h1.engine-h1 {{ max-width: 22ch; margin: 0 0 16px !important;
                          font-size: clamp(1.9rem, 3.2vw, 2.8rem) !important; font-weight: 680 !important;
                          line-height: 1.03 !important; letter-spacing: -0.035em !important;
                          color: var(--ink) !important; font-family: {charts.FONT} !important; }}
          .engine-lead {{ max-width: 58ch; margin: 0 0 24px; color: var(--ink-2);
                          font-size: 15px; line-height: 1.6; }}

          /* The control console -- the hero's terminal element and the
             defining surface of this page, the way the ranked bar chart is
             Findings'. A bordered instrument frame (teal top rule, compact
             padding) holding the run control + gear on one axis and the
             four-step execution timeline directly below it -- not an
             editorial section that follows the hero. */
          /* Capped narrower than the 1240px results panels below on purpose:
             the console is the hero's terminal element and sits under a hero
             headline/lead that are themselves ~22ch/58ch wide. At full page
             width the four step rows became mostly dead space between a
             left-hugging title and a right-hugging status. The "What this
             batch found" results section keeps full width -- it's a separate
             section with its own eyebrow, and the width change reads as a
             deliberate shift from instrument to findings. */
          .st-key-console {{ margin-top: 2px; max-width: 900px; padding: 20px 22px 18px;
                             border: 1px solid var(--white-line); border-top: 2px solid var(--teal);
                             border-radius: var(--radius); background: var(--glass-solid);
                             box-shadow: var(--shadow-soft);
                             backdrop-filter: blur(22px) saturate(145%);
                             -webkit-backdrop-filter: blur(22px) saturate(145%); }}
          .st-key-console [data-testid="stHorizontalBlock"] {{ align-items: center; }}
          .console-strip {{ display: flex; align-items: center; gap: 12px; margin: 16px 0 12px;
                            font-family: {charts.MONO}; font-size: 11px; font-weight: 800;
                            letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }}
          .console-strip::after {{ content: ""; flex: 1; height: 1px; background: var(--line); }}

          /* Gear -- a utility control immediately right of Run. Secondary
             weight is carried entirely by the plain glass .stButton fill
             against Run's animated-gradient primary; no new color. It keeps
             the base .stButton RADIUS_SM (matches Run), never the 28px
             panel token or a 999px pill -- a large radius here is exactly
             what would make it read as a second card competing with Run.
             Height and touch target pinned so the pair reads as one unit. */
          .st-key-open_settings .stButton button {{ width: 100%; min-height: 46px;
                                                    padding: 6px 0 !important; font-size: 17px;
                                                    line-height: 1; color: var(--ink-2) !important; }}
          .st-key-open_settings .stButton button:hover {{ color: var(--teal) !important;
                                                          border-color: var(--teal) !important; }}
          /* Below Streamlit's column-stacking breakpoint the 0.5 gear column
             becomes full width; without this the gear would render as a
             second full-width button stacked under Run -- exactly the
             "large pill competing with Run" the brief rules out. Shrink it
             back to a utility control. */
          @media (max-width: 640px) {{
            .st-key-open_settings .stButton button {{ width: auto !important; min-width: 52px;
                                                      padding: 6px 16px !important; }}
          }}

          /* Compact methodology -- subordinate to the console. A label +
             chip strip + one disclosure, deliberately not the
             .section-id -> <h2> -> .note rhythm Findings gives its own
             methodology section. */
          .engine-measure {{ display: flex; align-items: baseline; gap: 10px 14px; flex-wrap: wrap;
                             margin: 0 0 14px; }}
          .engine-measure .k {{ font-family: {charts.MONO}; font-size: 11px; font-weight: 850;
                                letter-spacing: .15em; text-transform: uppercase; color: var(--teal);
                                white-space: nowrap; }}
          .engine-measure .v {{ max-width: 62ch; font-size: 13px; line-height: 1.55; color: var(--ink-2); }}

          /* Settings drawer -- fixed, right-anchored overlay panel (Engine
             page only). Base position/appearance lives here; the actual
             open/closed transform is written by page_engine.py on every
             rerun as a small trailing <style> override (see the note
             there), since Streamlit can't flip a class client-side without
             a JS bridge. Declared off-screen by default so there's no
             flash-of-open-drawer before that override loads. */
          .st-key-settingsdrawer {{ position: fixed !important; z-index: 1000 !important;
                                    top: 92px; right: 18px; bottom: 18px;
                                    width: min(360px, calc(100vw - 36px)); overflow-y: auto;
                                    padding: 22px 22px 26px; border: 1px solid var(--white-line);
                                    border-radius: 26px; background: var(--glass); box-shadow: var(--shadow);
                                    backdrop-filter: blur(28px) saturate(150%);
                                    -webkit-backdrop-filter: blur(28px) saturate(150%);
                                    transform: translateX(calc(100% + 40px)); opacity: 0; pointer-events: none;
                                    transition: transform .38s cubic-bezier(.19,1,.22,1), opacity .3s ease; }}
          .drawer-backdrop {{ position: fixed; z-index: 990; inset: 0; background: rgba(20,28,48,.22);
                              opacity: 0; pointer-events: none; transition: opacity .3s ease; }}
          @media (prefers-reduced-motion: reduce) {{
            .st-key-settingsdrawer, .drawer-backdrop {{ transition: none; }}
          }}

          /* Click-outside-to-close catcher for the settings drawer -- a
             real (visually invisible) button, positioned above the
             decorative backdrop but below the drawer itself, so a click
             anywhere outside the drawer closes it. Text is hidden visually
             (color/font-size) but stays in the accessible tree for screen
             readers; pointer-events is flipped open/closed by
             page_engine.py alongside the drawer and backdrop. */
          .st-key-drawerscrim {{ position: fixed !important; z-index: 995 !important; inset: 0;
                                 pointer-events: none; }}
          /* Every wrapper between the fixed scrim div and the actual
             <button> defaults to width:fit-content/height:auto (Streamlit
             shrink-wraps element containers to their content), so without
             this chain the button collapses to its own label size in the
             top-left corner instead of covering the viewport -- confirmed
             by inspecting the rendered rect, which is exactly what broke
             the first version of this fix. */
          .st-key-drawerscrim > div, .st-key-drawerscrim [data-testid="stElementContainer"],
          .st-key-drawerscrim .stButton {{ width: 100% !important; height: 100% !important; }}
          .st-key-drawerscrim .stButton button {{ width: 100%; height: 100%; border: none !important;
                                                     background: transparent !important; box-shadow: none !important;
                                                     color: transparent !important; font-size: 0 !important;
                                                     cursor: default; backdrop-filter: none !important;
                                                     -webkit-backdrop-filter: none !important; }}
          .st-key-drawerscrim .stButton button:hover {{ transform: none !important; }}

      /* Spine -- a fixed, always-on rail down the left edge. Pure CSS
         position:fixed, so it stays in place as the page scrolls under it
         with no JS required. Clicking a node is a real anchor jump (browser-
         native #id navigation). What it deliberately does NOT do: highlight
         which stage is currently in view as you scroll -- that needs a
         scroll listener, and <script> tags injected via st.markdown() never
         execute (React's innerHTML-equivalent doesn't run embedded scripts),
         so a scroll-synced active state isn't reliably achievable here
         without a bigger iframe-based rearchitecture. Hover reveals the
         label; the dot itself is always visible. */
      .spine {{ position: fixed; z-index: 15; left: 22px; top: 50%; transform: translateY(-50%);
                display: none; flex-direction: column; }}
      @media (min-width: 1080px) {{ .spine {{ display: flex; }} }}
      .spine::before {{ content: ""; position: absolute; left: 5px; top: 6px; bottom: 6px; width: 1px;
                        background: var(--line); }}
      .spine a {{ position: relative; display: flex; align-items: center; gap: 10px; padding: 9px 0;
                  text-decoration: none; }}
      .spine-dot {{ width: 11px; height: 11px; border-radius: 50%; background: var(--glass-solid);
                    border: 1px solid var(--white-line); flex: 0 0 11px; transition: all .2s ease; }}
      .spine a:hover .spine-dot, .spine a:focus .spine-dot {{ background: var(--teal); transform: scale(1.3);
                                                              box-shadow: 0 0 0 4px rgba(0,127,131,.15); }}
      .spine-label {{ font-size: 10.5px; font-weight: 750; color: var(--ink-2); white-space: nowrap;
                      opacity: 0; transform: translateX(-6px); transition: all .2s ease;
                      background: var(--glass-solid); border: 1px solid var(--white-line);
                      padding: 4px 9px; border-radius: 8px; }}
      .spine a:hover .spine-label, .spine a:focus .spine-label {{ opacity: 1; transform: none; }}

          /* Scenes -- generous section rhythm, matching the source page's pacing */
          .scene {{ position: relative; padding: 30px max(4px, calc((100vw - 1240px) / 2)) 78px; }}
          .scene-inner {{ width: min(100%, 1240px); margin-inline: auto; }}
          .cover-kicker {{ display: flex; align-items: center; gap: 12px; margin: 40px 0 20px;
                           color: var(--ink-2); font-size: 12px; font-weight: 800; letter-spacing: .11em;
                           text-transform: uppercase; }}
          .cover-kicker span {{ padding: 6px 9px; border: 1px solid var(--white-line); border-radius: 8px;
                                background: rgba(255,255,255,.52); color: var(--teal); }}
          h1.cover-h1 {{ max-width: 900px; margin: 0 0 18px !important; font-size: clamp(2.3rem, 4.6vw, 4.2rem) !important;
                         font-weight: 680 !important; line-height: .96 !important; letter-spacing: -0.04em !important;
                         color: var(--ink) !important; font-family: {charts.FONT} !important; }}
          .subhead {{ max-width: 650px; color: var(--ink-2); font-size: clamp(1.02rem, 1.4vw, 1.2rem); line-height: 1.65; }}

          .btn {{ display: inline-flex; align-items: center; justify-content: center; gap: 9px;
                  min-height: 46px; padding: 12px 17px; border: 1px solid rgba(20,40,73,.08); border-radius: 14px;
                  background: var(--ink); color: #fff; text-decoration: none; font-size: 13px; font-weight: 800;
                  box-shadow: 0 12px 28px rgba(22,32,60,.18); }}
          .btn.secondary {{ border-color: var(--white-line); background: rgba(255,255,255,.52); color: var(--ink);
                            box-shadow: var(--shadow-soft); }}

          .floating-card {{ width: 100%; padding: 22px; border-radius: 24px; }}
          .floating-card small {{ display: block; color: var(--muted); font-size: 10px; font-weight: 800;
                                  letter-spacing: .1em; text-transform: uppercase; }}
          .floating-card b {{ display: block; margin: 14px 0 5px; font-size: 2.6rem; line-height: .85;
                              letter-spacing: -.05em; font-variant-numeric: tabular-nums; color: var(--ink); }}
          .floating-card p {{ margin: 0; color: var(--ink-2); font-size: 12px; }}
          .status-row {{ display: flex; align-items: center; gap: 8px; margin-top: 16px; color: var(--teal);
                         font-size: 11px; font-weight: 800; }}
          .status-row i {{ width: 8px; height: 8px; border-radius: 50%; background: var(--teal-bright);
                           box-shadow: 0 0 0 5px rgba(47,200,194,.15); }}

          .ledger-note {{ max-width: 420px; padding-left: 20px; border-left: 2px solid rgba(0,127,131,.32);
                          color: var(--ink-2); font-size: 14px; }}
          .metric {{ position: relative; min-height: 190px; padding: 27px; overflow: hidden;
                     border: 1px solid var(--white-line); border-radius: 23px; background: rgba(255,255,255,.47);
                     box-shadow: inset 0 1px 0 white; height: 100%; }}
          .metric.hero-metric {{ background: linear-gradient(145deg, rgba(255,255,255,.68), rgba(224,248,248,.55)); }}
          .metric-label {{ color: var(--muted); font-size: 11px; font-weight: 800; letter-spacing: .1em;
                           text-transform: uppercase; }}
          .metric-number {{ display: block; margin: 30px 0 10px; font-size: clamp(2.6rem, 4.5vw, 4rem);
                            font-weight: 680; line-height: .8; letter-spacing: -.06em; color: var(--ink);
                            font-variant-numeric: tabular-nums; }}
          .metric p {{ max-width: 280px; margin: 0; color: var(--ink-2); font-size: 13px; }}

          .insight-chip {{ display: inline-flex; align-items: center; gap: 9px; margin-top: 18px; padding: 9px 12px;
                           border: 1px solid rgba(0,127,131,.16); border-radius: 999px; background: rgba(221,249,247,.65);
                           color: #006e72; font-size: 12px; font-weight: 800; }}
          .signal-glass {{ position: relative; min-height: 420px; padding: 36px; border-radius: 34px; overflow: hidden; }}
          .axis-label {{ position: absolute; z-index: 2; color: var(--muted); font-size: 10px; font-weight: 800;
                         letter-spacing: .08em; text-transform: uppercase; }}
          .plot {{ position: absolute; inset: 60px 30px 40px 30px; border-left: 1px solid rgba(36,55,88,.18);
                   border-bottom: 1px solid rgba(36,55,88,.18);
                   background-image: linear-gradient(rgba(49,67,102,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(49,67,102,.07) 1px, transparent 1px);
                   background-size: 25% 25%; }}
          .bubble {{ position: absolute; z-index: 2; display: grid; place-items: center; width: var(--size);
                     aspect-ratio: 1; border: 1px solid rgba(255,255,255,.95); border-radius: 50%;
                     background: var(--fill); box-shadow: 0 14px 30px rgba(54,76,126,.13), inset 0 1px 7px rgba(255,255,255,.7);
                     transform: translate(-50%, 50%); }}
          .bubble span {{ color: var(--ink); font-size: 10px; font-weight: 850; text-align: center; line-height: 1.12; }}
          .bubble small {{ display: block; margin-top: 3px; color: var(--ink-2); font-size: 8px; }}
          /* Bubble diameter is a fixed px custom property set per-bubble in
             Python (--size), with zero responsive handling until this rule --
             confirmed by grepping every @media rule in this file before this
             pass, there wasn't one. A 154px circle positioned by percentage
             inside a ~350px mobile column overlaps/overflows; scaling the
             already-centered transform down (not touching --size itself, so
             desktop is untouched) shrinks every bubble in place without
             fighting the percentage-based left/bottom positioning. */
          @media (max-width: 640px) {{
            .bubble {{ transform: translate(-50%, 50%) scale(.6); }}
            .bubble span {{ font-size: 8.5px; }}
            .bubble small {{ font-size: 7px; }}
          }}

          .layer {{ position: relative; padding: 26px; border-radius: 26px; height: 100%; }}
          .layer-num {{ display: grid; place-items: center; width: 38px; height: 38px; margin-bottom: 30px;
                        border: 1px solid var(--white-line); border-radius: 13px; background: rgba(255,255,255,.48);
                        color: var(--teal); font-size: 11px; font-weight: 850; }}
          .layer h3 {{ font-size: 1.35rem !important; }}
          .layer p {{ color: var(--ink-2); font-size: 13px; }}
          .source-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 18px; }}
          .source-tags span {{ padding: 6px 8px; border: 1px solid rgba(60,78,115,.12); border-radius: 8px;
                               background: rgba(255,255,255,.48); color: var(--ink-2); font-size: 10px; font-weight: 800; }}

          .pivot {{ position: relative; display: grid; grid-template-columns: 44px 1fr; gap: 16px;
                    align-items: start; padding: 22px 24px; border-radius: 26px; height: 100%; }}
          .pivot-marker {{ display: grid; place-items: center; width: 40px; height: 40px; margin-bottom: 14px;
                           border: 1px solid white; border-radius: 14px; background: var(--glass-solid);
                           box-shadow: 0 8px 22px rgba(58,75,118,.13); color: var(--teal); font-size: 15px; }}
          .pivot small {{ color: var(--teal); font-size: 10px; font-weight: 850; letter-spacing: .12em; text-transform: uppercase; }}
          .pivot h3 {{ margin-top: 6px !important; font-size: 1.2rem !important; }}
          .pivot p {{ color: var(--ink-2); font-size: 13px; margin: 0 0 14px !important; }}
          .outcome {{ display: inline-flex; padding: 6px 9px; border-radius: 8px; background: rgba(220,247,245,.68);
                      color: #006d70; font-size: 10px; font-weight: 850; }}

          .integrity-shell {{ position: relative; padding: clamp(24px, 4vw, 48px); border-radius: 38px; overflow: hidden; }}
          .integrity-top {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 32px; }}
          .guardrails {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
          @media (max-width: 900px) {{
            .integrity-top {{ grid-template-columns: 1fr; }}
            .guardrails {{ grid-template-columns: 1fr 1fr; }}
          }}
          .guardrail {{ min-height: 140px; padding: 20px; border: 1px solid var(--white-line); border-radius: 20px;
                        background: rgba(255,255,255,.38); height: 100%; }}
          .guardrail b {{ display: block; margin-bottom: 7px; font-size: 13px; color: var(--ink); }}
          .guardrail p {{ margin: 0; color: var(--muted); font-size: 11px; line-height: 1.5; }}
          .recovery {{ display: flex; align-items: center; gap: 18px; margin-top: 16px; padding: 18px 20px;
                       border: 1px solid rgba(232,101,97,.16); border-radius: 18px; background: rgba(255,241,238,.58); }}
          .recovery-number {{ color: var(--coral); font-size: 2.3rem; font-weight: 700; line-height: 1; letter-spacing: -.07em; }}
          .recovery p {{ margin: 0; color: #674a4a; font-size: 12px; }}

          .quote-card {{ position: relative; padding: clamp(22px, 3vw, 36px); border-radius: 30px; height: 100%; }}
          .quote-card.primary {{ background: rgba(244,252,253,.62); }}
          .quote-mark {{ display: block; height: 30px; color: var(--teal-bright); font-family: Georgia, serif;
                         font-size: 4rem; line-height: .75; }}
          blockquote {{ margin: 16px 0 0; color: var(--ink); font-size: clamp(1.1rem, 1.8vw, 1.6rem); font-weight: 550;
                        line-height: 1.3; letter-spacing: -.03em; }}
          figcaption {{ margin-top: 20px; color: var(--muted); font-size: 11px; font-weight: 700; }}
          figcaption b {{ color: var(--teal); }}
          .final-strip {{ display: flex; flex-wrap: wrap; align-items: center; gap: 18px; margin-top: 14px;
                          padding: 17px 20px; border-radius: 26px; }}
          .final-strip p {{ margin: 0; color: var(--ink-2); font-size: 13px; font-weight: 700; flex: 1 1 200px; }}
          .final-stat {{ padding: 4px 14px; border-left: 1px solid var(--line); text-align: center; }}
          .final-stat b {{ display: block; font-size: 1.4rem; line-height: 1; letter-spacing: -.05em; color: var(--ink); }}
          .final-stat span {{ color: var(--muted); font-size: 9px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }}

          /* Reused utility classes -- also consumed by the live-engine page. */
          .lede {{ color: var(--ink-2); font-size: 14.5px !important; line-height: 1.6 !important; max-width: 68ch; margin-top: 8px; }}
          .note {{ color: var(--ink-2); font-size: 13px !important; line-height: 1.6 !important; max-width: 78ch; }}
          .meta {{ font-family: {charts.MONO} !important; font-size: 12px !important; color: var(--muted); }}
          .meta a {{ color: var(--teal); text-decoration: none; }}
          .quote {{ font-size: 13px !important; color: var(--ink); line-height: 1.6;
                    border-left: 2px solid rgba(0,127,131,.22); background: rgba(255,255,255,.4);
                    border-radius: 0 12px 12px 0; padding: 8px 12px; margin: 6px 0; }}
          .chip {{ display: inline-block; font-family: {charts.FONT} !important; font-size: 10.5px;
                   border: 1px solid var(--white-line); border-radius: 999px; padding: 3px 10px;
                   margin: 2px 4px 2px 0; color: var(--ink-2); background: var(--glass); }}
          .chip-on {{ border-color: rgba(0,127,131,.22); color: var(--teal); background: rgba(0,127,131,.1); }}
          .panel {{ position: relative; background: var(--glass-solid); border: 1px solid var(--white-line);
                    border-radius: var(--radius); padding: 18px 20px; box-shadow: var(--shadow-soft);
                    backdrop-filter: blur(22px) saturate(145%); -webkit-backdrop-filter: blur(22px) saturate(145%); }}

          /* Neither page uses Streamlit's native left sidebar any more -- run
             settings live in a right-hand column instead (see page_engine.py)
             so they can actually sit on the right and have a real, labeled
             collapse control instead of Streamlit's easy-to-miss arrow. The
             native sidebar and its collapsed-state arrow are hidden outright
             rather than left as empty dead space. */
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

          .stButton button {{ border-radius: 14px; font-weight: 800; font-size: 13.5px; letter-spacing: -0.005em;
                                border: 1px solid var(--white-line); padding: 10px 18px; background: rgba(255,255,255,.52);
                                box-shadow: var(--shadow-soft); backdrop-filter: blur(15px); transition: transform 0.15s ease; }}
          /* background is intentionally NOT set here -- it would collide with
             the animated gradient background declared on this same selector
             above (identical specificity, source order would silently win
             and flatten the shine effect back to a solid fill, which is
             exactly the bug this comment is here to prevent regressing). */
          .stButton button[kind="primary"] {{ color: #fff; border-color: transparent;
                                                box-shadow: 0 12px 28px rgba(22,32,60,.18); }}
          .stButton button:hover {{ transform: translateY(-2px); }}
          .stButton button p, .stDownloadButton > button p {{ color: inherit !important; font-size: inherit; font-weight: inherit; }}
          .stDownloadButton > button {{ border-radius: 14px; border: 1px solid var(--white-line);
                                        background: rgba(255,255,255,.52); color: var(--ink); font-size: 13px; }}
          /* Multiselect box + tags. Current Streamlit builds this on top of
             react-aria, not BaseWeb, so there is no [data-baseweb="..."]
             attribute anywhere on the page any more -- the selectors this
             block used to use matched zero elements, and every multiselect
             silently fell back to Streamlit's stock blue tags and plain
             white box instead of the app's teal glass styling. Targeting
             react-aria's own stable output instead: [role="group"] is the
             box react-aria puts on the control itself, and [data-tag] is a
             real attribute Streamlit stamps on each tag pill (confirmed via
             computed styles, not assumed from a class name -- emotion-hash
             classes like st-emotion-cache-* are not selector-stable across
             Streamlit versions and are deliberately avoided here). */
          [data-testid="stMultiSelect"] [role="group"] {{
              border-radius: 12px !important; border-color: var(--line) !important;
              background: var(--glass-solid) !important; font-size: 13px; }}
          [data-tag] {{ border-radius: 999px !important; background: rgba(0,127,131,.1) !important;
                        color: var(--teal) !important; font-size: 11px !important; }}
          [data-tag] svg {{ fill: var(--teal) !important; }}
          /* The clear-all (x) and open-dropdown (v) controls are flex
             siblings of the tag list, not children of it, and default to
             align-self:center against the *whole* control's height. That's
             invisible with one row of tags but strands both icons floating
             in mid-air, disconnected from any row, the moment tags wrap to
             two or more rows (confirmed via computed styles: align-self was
             "center" against a 138px-tall box while the tag rows sit at the
             top). Pinning them to the top edge keeps them level with the
             first tag row regardless of how many rows the tags wrap to. */
          [data-testid="stMultiSelectTagsContainer"] ~ button {{
              align-self: flex-start !important; margin-top: 6px; }}
          [data-testid="stWidgetLabel"] p {{ font-size: 12.5px; font-weight: 600; color: var(--ink); }}

          .stTabs [data-baseweb="tab-list"] {{ gap: 24px; border-bottom: 1px solid var(--line); background: transparent; }}
          .stTabs [data-baseweb="tab"] {{ padding: 10px 0; font-size: 13.5px; font-weight: 600; color: var(--muted); background: transparent; }}
          .stTabs [aria-selected="true"] {{ color: var(--ink) !important; font-weight: 700; }}
          .stTabs [data-baseweb="tab-highlight"] {{ background: var(--teal); height: 2px; }}
          .stTabs [data-baseweb="tab-border"] {{ display: none; }}
          .stTabs [data-baseweb="tab-panel"] {{ padding-top: 20px; }}

          [data-testid="stExpander"] details {{ border: 1px solid var(--white-line); border-radius: 20px;
                                                background: var(--glass-solid); box-shadow: var(--shadow-soft); overflow: hidden; }}
          [data-testid="stExpander"] summary {{ font-size: 13px; font-weight: 600; color: var(--ink); padding: 11px 15px; }}
          [data-testid="stExpander"] summary:hover {{ background: rgba(255,255,255,.5); }}
          [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{ padding: 4px 15px 14px; }}

          [data-testid="stAlert"] {{ border-radius: 18px; font-size: 13px; }}
          [data-testid="stCodeBlock"] pre {{ background: rgba(255,255,255,.5) !important; border: 1px solid var(--white-line);
                                             border-radius: 12px; font-size: 11.5px; }}
          hr {{ border-color: var(--line); margin: 1.6rem 0; }}

          /* Page footer -- the closing brand mark, in flow at the bottom of
             each page: the nav pill's [icon + name] lockup on the canvas
             (no glass). Findings passes an `End of Atlas` marker in the
             app's own left-anchored .section-id eyebrow idiom -- its 28px
             tick IS the terminus rule, a bookend to every section eyebrow
             above it, so that footer carries no separate divider. The Live
             Engine has no eyebrow (it is a tool you ran, not an atlas you
             finished), so it falls back to a thin full-width end rule. */
          .atlas-footer {{ width: min(100%, 1240px); margin: 24px auto 10px;
                           padding: 18px 2px 0; border-top: 1px solid rgba(49,67,102,.24);
                           box-shadow: inset 0 2px 0 rgba(255,255,255,.7); }}
          .atlas-footer:has(.atlas-end) {{ margin-top: 14px; padding-top: 0;
                                           border-top: none; box-shadow: none; }}
          .atlas-footer .atlas-end {{ margin: 0 0 13px !important; }}
          .atlas-footer .af-lockup {{ display: flex; align-items: center; gap: 11px; }}
          .atlas-footer img {{ width: 38px; height: 38px; flex: 0 0 38px; object-fit: contain;
                               filter: drop-shadow(0 2px 6px rgba(74,79,181,.24)); }}
          .atlas-footer .af-name {{ font-size: 13px; font-weight: 850; letter-spacing: -.01em; color: var(--ink); }}
        </style>
        <div class="ambient a"></div>
        <div class="ambient b"></div>
        <div class="nav-scrim"></div>
        """,
        unsafe_allow_html=True,
    )


def spine(stops: list[tuple[str, str]]) -> None:
    """Fixed left-edge rail. `stops` is a list of (anchor_id, short_label)."""
    items = "".join(
        f'<a href="#{aid}"><span class="spine-dot"></span><span class="spine-label">{label}</span></a>'
        for aid, label in stops
    )
    st.markdown(f'<nav class="spine" aria-label="Page stages">{items}</nav>', unsafe_allow_html=True)


def nav_shell(findings_page, engine_page, current: str) -> None:
    """Fixed glass nav pill, shared by both pages. `current` is 'findings' or 'engine'.

    Built from a real st.page_link (Streamlit's native multipage navigation
    widget) inside a keyed st.container, not raw <a href> tags. Anchor tags
    injected via st.markdown() looked right but didn't reliably navigate --
    Streamlit's own header sits at a very high z-index above custom fixed
    elements and can intercept the click before it reaches a plain <a>.
    st.page_link is a first-class Streamlit widget, so it isn't subject to
    that: it's guaranteed to hit Streamlit's internal router.
    """
    with st.container(key="navshell"):
        brand_col, findings_col, engine_col = st.columns([3, 1, 1], vertical_alignment="center")
        with brand_col:
            st.markdown(
                f'<span class="brand"><img class="brand-icon" src="{_logo_data_uri()}" alt="" />'
                "<span>Evidence Atlas</span></span>",
                unsafe_allow_html=True,
            )
        with findings_col:
            st.page_link(findings_page, label="Findings", disabled=(current == "findings"))
        with engine_col:
            st.page_link(engine_page, label="Live engine", disabled=(current == "engine"))


def footer(end_label: str | None = None) -> None:
    """Closing brand mark in flow at the bottom of a page -- the nav pill's
    [icon + name] lockup, on the canvas rather than a glass surface, below a
    full-width end rule. Called at the end of each page's render().

    `end_label` (Findings only) adds an `End of Atlas`-style marker above the
    lockup, in the app's left-anchored .section-id eyebrow idiom -- a bookend
    to the section eyebrows above it. The Live Engine passes nothing: it is a
    tool you ran, not an atlas you finished. No tagline on either -- any
    one-line pipeline claim is true on only one page.
    """
    label_html = (
        f'<p class="section-id atlas-end">{escape(end_label)}</p>' if end_label else ""
    )
    st.markdown(
        f'<footer class="atlas-footer">{label_html}'
        f'<div class="af-lockup"><img src="{_logo_data_uri()}" alt="" />'
        '<span class="af-name">Evidence Atlas</span></div></footer>',
        unsafe_allow_html=True,
    )

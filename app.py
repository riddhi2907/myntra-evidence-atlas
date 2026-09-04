"""Myntra Wishlist Discovery Engine -- entrypoint / router.

Two pages, one design system:
  - Discovery Findings (live_engine/page_findings.py): the static
    evidence-collection story (content also in
    docs/DISCOVERY_ENGINE_FINDINGS.md).
  - Live Engine (live_engine/page_engine.py): fetch public consumer
    feedback right now, classify it against the locked codebook, map it
    onto the twelve opportunity themes and six metric-decomposition nodes.

Split via st.navigation rather than one long scroll: each page is its own
Streamlit rerun boundary, so clicking a widget on the live engine page
never re-renders the static findings page next to it. Shared look and feel
comes from live_engine.chrome, imported by both pages -- there is exactly
one CSS block in this app, not two independently-styled ones.

Run locally:   streamlit run app.py
Headless check: python smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from live_engine import page_engine, page_findings  # noqa: E402

st.set_page_config(
    page_title="Myntra Wishlist Discovery Engine",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "evidence-atlas-logo.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

engine_page = st.Page(
    lambda: page_engine.render(findings_page, engine_page),
    title="Live Engine",
    url_path="engine",
)
findings_page = st.Page(
    # No url_path: a direct/fresh browser load of a default page's own named
    # path (confirmed with Playwright -- /engine loads fine cold, /findings
    # didn't) trips Streamlit's "Page not found" fallback dialog. The
    # default page's real, reliable address is the bare root "/".
    lambda: page_findings.render(findings_page, engine_page),
    title="Discovery Findings",
    default=True,
)

nav = st.navigation([findings_page, engine_page], position="hidden")
nav.run()

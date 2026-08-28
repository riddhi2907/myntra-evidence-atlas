"""
Design tokens and chart primitives, rendered as plain HTML/CSS rather than
through a plotting library.

Three reasons, in order: the charts here are all horizontal bars over <=12
categories, which HTML does natively and correctly; a plotting library is a
heavy dependency to add to a deploy whose whole point is starting fast; and
inline CSS gives exact control over the mark spec (rounded data-ends anchored
to the baseline, hairline gridlines) that a library would fight.

Colors come from the validated default palette. Magnitude is carried by bar
LENGTH and a single hue, not by a color ramp. An ordinal ramp was the tempting
choice for the M1-M6 funnel, but the blue ramp cannot produce six steps that
are both visibly separated and clear of the 2:1 light-end contrast floor
(verified with the palette validator: 5 steps pass, 6 fail). Row order plus
the M1..M6 labels carry the funnel order unambiguously, so one hue is both
simpler and correct.

This module is also the single source of design tokens for the page: app.py
imports from here rather than defining a parallel palette inside its own
<style> block, so the chart surface and the page chrome can never drift.

Radius rule, applied everywhere without exception:
    RADIUS_LG   panels, cards, tiles, expanders, the run log
    RADIUS_SM   controls, inputs, buttons, bar ends, code blocks
    RADIUS_PILL chips and status dots only
"""

from __future__ import annotations

from html import escape

# --- surfaces ---------------------------------------------------------------
# Ported directly from deliverables/myntra-wishlist-findings.html ("Evidence
# Atlas") -- that page is now the source of truth for this app's design, not
# an independent interpretation of it. Values are copied, not approximated.
CANVAS = "#eef5ff"
CANVAS_GRADIENT = (
    "radial-gradient(circle at 8% 7%, rgba(47,200,194,.24), transparent 25rem),"
    "radial-gradient(circle at 91% 14%, rgba(141,121,232,.24), transparent 29rem),"
    "radial-gradient(circle at 45% 64%, rgba(105,184,255,.18), transparent 34rem),"
    "linear-gradient(145deg, #f9fcff 0%, #edf4ff 52%, #f6f1ff 100%)"
)
GLASS = "rgba(255,255,255,.55)"
GLASS_SOLID = "rgba(251,253,255,.92)"
GLASS_BORDER = "rgba(255,255,255,.88)"
SURFACE = GLASS_SOLID
SURFACE_SUNK = "rgba(255,255,255,.38)"   # matches .guardrail's wash
BACKDROP_BLUR = "blur(26px) saturate(145%)"

# --- ink ----------------------------------------------------------------
INK_PRIMARY = "#11182b"
INK_SECONDARY = "#34405a"    # ink-2 in the source page
INK_MUTED = "#65718a"

# --- lines ----------------------------------------------------------------
HAIRLINE = "rgba(49,67,102,.15)"
GRIDLINE = "rgba(49,67,102,.07)"
BASELINE = "rgba(49,67,102,.18)"

# --- series and status ------------------------------------------------------
SERIES = "#007f83"           # teal -- primary accent, section-id rules, links
SERIES_SOFT = "#2fc8c2"      # teal-bright -- status dots, gradient stop
SERIES_TINT = "rgba(0,127,131,.12)"
SERIES_DIM = "rgba(0,127,131,.22)"
INDIGO = "#5646c9"
VIOLET = "#8d79e8"
CORAL = "#e86561"
AMBER = "#b96a00"
CRITICAL = CORAL
GOOD = SERIES
WARN = AMBER

# --- type -------------------------------------------------------------------
# Single-quoted family names on purpose: these strings are interpolated into
# inline style="..." attributes, where a double quote would terminate the
# attribute and silently drop the rest of the declaration.
FONT = "'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO = FONT   # the source page uses no separate mono face either

# --- shape --------------------------------------------------------------
RADIUS_LG = "28px"           # the source page's --radius
RADIUS_SM = "14px"
RADIUS_PILL = "999px"

SHADOW_SOFT = "0 12px 42px rgba(61,81,128,.1), inset 0 1px 0 #fff"
SHADOW_DEEP = "0 24px 80px rgba(58,75,118,.14), inset 0 1px 0 rgba(255,255,255,.96)"


def bar_chart(
    rows: list[tuple[str, int, str]],
    *,
    max_value: int | None = None,
    label_width: str = "170px",
    unit: str = "",
) -> str:
    """Horizontal bars. `rows` is (label, value, sublabel).

    Every row is rendered including zero-value ones. For the metric funnel a
    zero is a finding about what this batch surfaced, not a row to hide.
    """
    if not rows:
        return ""
    top = max_value or max((v for _, v, _ in rows), default=0) or 1

    out = [f'<div style="font-family:{FONT};padding:2px 0;">']
    for label, value, sub in rows:
        pct = (value / top) * 100 if top else 0
        # A zero-value row still shows its track, so the row reads as "measured
        # zero" rather than "no data".
        fill = (
            f'<div style="width:{pct:.1f}%;height:20px;background:{SERIES};'
            f'border-radius:0 {RADIUS_SM} {RADIUS_SM} 0;min-width:{3 if value else 0}px;"></div>'
        )
        out.append(
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:5px;">'
            # Overflow is trimmed here rather than by slicing the caller's
            # string, so a long theme name ends in an ellipsis instead of
            # mid-word. The full name is kept in the title attribute.
            f'<div title="{escape(label, quote=True)}" style="width:{label_width};'
            f'flex:0 0 {label_width};font-size:12.5px;line-height:1.3;'
            f'color:{INK_SECONDARY};text-align:right;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{escape(label)}</div>'
            f'<div style="flex:1;border-left:1px solid {BASELINE};padding-left:2px;'
            f'background:linear-gradient(to right,{GRIDLINE} 1px,transparent 1px) 0 0/25% 100%;">'
            f"{fill}</div>"
            f'<div style="width:88px;flex:0 0 88px;font-size:12.5px;color:{INK_MUTED};'
            f'font-family:{MONO};font-variant-numeric:tabular-nums;">'
            f'<b style="color:{INK_PRIMARY};font-weight:600;">{value}</b>{escape(unit)}'
            f'<span style="color:{INK_MUTED};"> {escape(sub)}</span></div>'
            f"</div>"
        )
    out.append("</div>")
    return "".join(out)


def stat_tile(value: str, label: str, sub: str = "", tone: str = "neutral") -> str:
    """A single headline number. Not a one-bar bar chart."""
    color = {
        "neutral": INK_PRIMARY, "good": GOOD, "warn": WARN,
        "critical": CRITICAL, "accent": SERIES,
    }.get(tone, INK_PRIMARY)
    rule = {"good": GOOD, "warn": WARN, "critical": CRITICAL, "accent": SERIES}.get(tone, BASELINE)
    return (
        f'<div style="font-family:{FONT};background:{GLASS_SOLID};border:1px solid {GLASS_BORDER};'
        f"border-left:2px solid {rule};border-radius:{RADIUS_LG};padding:13px 15px;height:100%;"
        f'box-shadow:{SHADOW_SOFT};backdrop-filter:{BACKDROP_BLUR};'
        f'-webkit-backdrop-filter:{BACKDROP_BLUR};">'
        f'<div style="font-family:{MONO};font-size:26px;font-weight:600;color:{color};'
        f'line-height:1.1;letter-spacing:-0.02em;font-variant-numeric:tabular-nums;">{escape(value)}</div>'
        f'<div style="font-size:12.5px;font-weight:500;color:{INK_PRIMARY};margin-top:6px;'
        f'line-height:1.35;">{escape(label)}</div>'
        f'<div style="font-size:11.5px;color:{INK_MUTED};margin-top:3px;line-height:1.4;">{escape(sub)}</div>'
        f"</div>"
    )


def sentiment_row(counts: dict[str, int]) -> str:
    """Aspect sentiment as a small stacked strip. Sentiment is an ordered scale,
    so this is centered on neutral with the diverging pair (blue to red) and a
    gray middle, never a rainbow of four unrelated hues."""
    order = [("positive", SERIES), ("mixed", SERIES_SOFT), ("neutral", "#dedcd4"), ("negative", CRITICAL)]
    total = sum(counts.values()) or 1
    cells = []
    for name, color in order:
        n = counts.get(name, 0)
        if not n:
            continue
        cells.append(
            f'<div title="{name}: {n}" style="width:{n / total * 100:.1f}%;height:10px;'
            f'background:{color};margin-right:2px;border-radius:2px;"></div>'
        )
    labels = "  ".join(f"{k} {v}" for k, v in counts.items() if v)
    return (
        f'<div style="font-family:{FONT};">'
        f'<div style="display:flex;width:130px;">{"".join(cells)}</div>'
        f'<div style="font-family:{MONO};font-size:11px;color:{INK_MUTED};'
        f'margin-top:4px;">{escape(labels)}</div>'
        f"</div>"
    )


def step_strip(steps: list[tuple[str, str]]) -> str:
    """The four pipeline stages as an even grid, one line of detail each.

    Replaces a single run-on sentence of arrows: the stages are parallel in
    structure, so a grid says so and a sentence does not.
    """
    cells = []
    for i, (name, detail) in enumerate(steps, start=1):
        cells.append(
            f'<div style="background:{GLASS_SOLID};border:1px solid {GLASS_BORDER};'
            f'border-radius:{RADIUS_LG};padding:12px 14px;box-shadow:{SHADOW_SOFT};'
            f'backdrop-filter:{BACKDROP_BLUR};-webkit-backdrop-filter:{BACKDROP_BLUR};">'
            f'<div style="font-family:{MONO};font-size:11px;color:{SERIES};font-weight:600;">{i}</div>'
            f'<div style="font-size:13px;font-weight:600;color:{INK_PRIMARY};margin-top:5px;">{escape(name)}</div>'
            f'<div style="font-size:11.5px;color:{INK_SECONDARY};margin-top:3px;'
            f'line-height:1.45;">{escape(detail)}</div>'
            f"</div>"
        )
    return (
        f'<div style="font-family:{FONT};display:grid;gap:10px;'
        f'grid-template-columns:repeat(auto-fit,minmax(210px,1fr));">{"".join(cells)}</div>'
    )


def funnel(steps: list[tuple[str, int, str]], *, total: int) -> str:
    """The selection funnel: how many records survived each gate.

    Width is proportional to the count, so the drop-off is the shape of the
    block rather than a number the reader has to subtract themselves.
    """
    if not total:
        return ""
    rows = []
    for label, value, note in steps:
        pct = max(value / total * 100, 1.5)
        rows.append(
            f'<div style="margin-bottom:7px;">'
            f'<div style="display:flex;align-items:baseline;gap:8px;">'
            f'<span style="font-family:{MONO};font-size:14px;font-weight:600;color:{INK_PRIMARY};'
            f'font-variant-numeric:tabular-nums;min-width:52px;">{value:,}</span>'
            f'<span style="font-size:12.5px;color:{INK_PRIMARY};font-weight:500;">{escape(label)}</span>'
            f'<span style="font-size:11.5px;color:{INK_MUTED};">{escape(note)}</span>'
            f"</div>"
            f'<div style="height:6px;width:{pct:.1f}%;background:{SERIES};'
            f'border-radius:{RADIUS_SM};margin-top:4px;opacity:0.85;"></div>'
            f"</div>"
        )
    return f'<div style="font-family:{FONT};">{"".join(rows)}</div>'


def exec_step(
    num: int,
    title: str,
    state: str,
    detail_html: str = "",
    summary: str = "",
    blurb: str = "",
    timing: str = "",
) -> str:
    """One card in the persistent 4-step execution timeline.

    Replaces the single st.status() box whose contents got overwritten at
    each stage -- that model discarded the history of what already happened
    the moment the next stage started. This is one card per stage, always
    present, that only ever changes its own state:

      pending  -- quiet, waiting, no detail.
      running  -- the one card with real visual weight: teal edge, a live
                  indicator, and a fixed-max-height scrollable detail pane
                  so a fast-growing log (per-source rows, etc.) doesn't push
                  the page taller out from under a scrolled viewer.
      done     -- compact, a checkmark and a one-line summary of what
                  happened. Detail content isn't rendered here (the caller
                  reads it back from session_state for a real st.expander
                  once interactivity is possible again post-run) -- during
                  the live run itself nothing is clickable anyway, since the
                  script is blocked inside pipeline.run().
    """
    linked = " linked" if num < 4 else ""
    if state in ("pending", "done", "error"):
        glyph = {"pending": "○", "done": "✓", "error": "!"}[state]
        if state == "pending":
            mid, right = blurb, "queued"
        elif state == "error":
            mid, right = (summary or "run stopped here"), "failed"
        else:  # done -- timing rides the summary line, no stranded right column
            mid = f"{summary} · {timing}" if (summary and timing) else (summary or timing or "done")
            right = ""
        return (
            f'<div class="exec-step {state}{linked}">'
            f'<span class="exec-step-num">{glyph}</span>'
            f'<span class="exec-step-body"><span class="exec-step-title">{escape(title)}</span>'
            f'<span class="exec-step-blurb">{escape(mid)}</span></span>'
            f'<span class="exec-step-state">{escape(right)}</span></div>'
        )
    return (
        f'<div class="exec-step running{linked}"><div class="exec-step-head">'
        f'<span class="exec-step-num">{num}</span><span class="exec-step-title">{escape(title)}</span>'
        f'<span class="exec-step-live">live</span></div>'
        f'<div class="exec-step-detail">{detail_html}</div></div>'
    )


def status_row(label: str, state: str, detail: str = "") -> str:
    """A credential or health row. A colored dot here carries real semantic
    state (configured / missing / degraded), which is the one case where a
    status dot earns its place."""
    color = {"ok": GOOD, "warn": WARN, "bad": CRITICAL}.get(state, INK_MUTED)
    return (
        f'<div style="font-family:{FONT};display:flex;align-items:flex-start;gap:8px;'
        f'padding:5px 0;">'
        f'<span style="width:7px;height:7px;border-radius:{RADIUS_PILL};background:{color};'
        f'flex:0 0 7px;margin-top:6px;"></span>'
        f"<span>"
        f'<span style="font-size:12.5px;color:{INK_PRIMARY};">{escape(label)}</span>'
        f'<span style="display:block;font-size:11px;color:{INK_MUTED};line-height:1.4;">{escape(detail)}</span>'
        f"</span></div>"
    )


def factor_rows(factors: list[tuple[str, int, dict]]) -> str:
    """Factors with their aspect-sentiment split, as one grid.

    Built as a single block rather than a per-row st.columns pair: Streamlit's
    column gutter is sized for page layout, not for a label and the 130px strip
    that belongs to it, and it pushed the two apart far enough to read as
    unrelated.
    """
    if not factors:
        return ""
    rows = []
    for factor, n, sentiments in factors:
        rows.append(
            f'<div style="display:flex;align-items:center;gap:14px;padding:7px 0;'
            f'border-bottom:1px solid {HAIRLINE};">'
            f'<span style="font-family:{MONO};font-size:12.5px;color:{INK_PRIMARY};'
            f'flex:0 0 120px;">{escape(factor)}</span>'
            f'<span style="font-family:{MONO};font-size:12.5px;font-weight:600;'
            f'color:{INK_PRIMARY};flex:0 0 24px;text-align:right;">{n}</span>'
            f'<span style="flex:1;">{sentiment_row(dict(sentiments))}</span>'
            f"</div>"
        )
    return f'<div style="font-family:{FONT};">{"".join(rows)}</div>'

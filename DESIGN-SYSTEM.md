# Evidence Atlas (Myntra Wishlist Discovery Engine): Design System

Light theme, editorial layout on a soft glass-and-gradient canvas. One visual
language across both pages, whether showing a static analysis or a live API
call in flight.

These are guidelines, not a contract. Token values live in
`src/live_engine/charts.py` and the CSS is injected once by
`src/live_engine/chrome.py`. This document describes that system in prose; if
it and the code disagree, the code is current and this file is stale. Update
it to match rather than hand-editing around the drift.

Both pages (`page_findings.py`, `page_engine.py`) call `chrome.inject_css()`
once at the top of `render()`, so there is exactly one CSS block in the app.
Every color, type, and shape value in that block is read from `charts.py`,
never restated, so the chart primitives and the page chrome stay in sync.
Only this document can drift from the code.

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Teal | `#007f83` | `--teal` / `SERIES` | Primary accent — section-id rules, links, primary data series in every chart, the one hue that carries magnitude |
| Teal Bright | `#2fc8c2` | `--teal-bright` / `SERIES_SOFT` | Status-dot "ok" state, gradient stop paired with Indigo/Violet in the hero accent-word and primary-button shine |
| Indigo | `#5646c9` | `--indigo` / `INDIGO` | Second stop in the three-color gradient sweep (accent-word, primary button) — never used alone as a flat fill |
| Violet | `#8d79e8` | `--violet` / `VIOLET` | Third gradient stop, softest of the three — same rule as Indigo, gradient-only |
| Coral | `#e86561` | `--coral` / `CORAL` | Critical/negative state only — status-dot "bad", negative sentiment bar. Never decorative |
| Amber | `#b96a00` | `--amber` / `AMBER` | Warning state only — status-dot "warn" (e.g. YouTube key missing) |
| Ink Primary | `#11182b` | `--ink` / `INK_PRIMARY` | Headings, primary button fill/text-on-dark, the darkest neutral in the system |
| Ink Secondary | `#34405a` | `--ink-2` / `INK_SECONDARY` | Body copy, card descriptions — the workhorse text color |
| Ink Muted | `#65718a` | `--muted` / `INK_MUTED` | Captions, sublabels, metadata rows (record counts, timing, source tags) |
| Canvas | `#eef5ff` | `--bg` / `CANVAS` | Page background base, under the gradient wash |
| Canvas Gradient | 3 radial teal/violet/blue blooms + linear wash | `CANVAS_GRADIENT` | `background-attachment: fixed` on `.stApp` — the ambient color, always present, never swapped per-page |
| Glass | `rgba(255,255,255,.55)` | `--glass` / `GLASS` | Translucent panel fill, paired with `backdrop-filter: blur(26px) saturate(145%)` |
| Glass Solid | `rgba(251,253,255,.92)` | `--glass-solid` / `GLASS_SOLID` | Near-opaque panel fill — status rows, credential panels, the multiselect control box |
| Glass Border | `rgba(255,255,255,.88)` | `--white-line` / `GLASS_BORDER` | The 1px edge on every glass surface — this, not a shadow, is what separates a panel from the canvas behind it |
| Hairline | `rgba(49,67,102,.15)` | `--line` / `HAIRLINE` | Dividers, `hr`, factor-row borders |

**Accent discipline:** Teal is the only color used as a flat fill or standalone accent. Indigo and Violet exist *only* as gradient stops alongside Teal and Ink (hero accent-word, primary button shine) — never as a solid background, never alone. Coral and Amber are reserved for real semantic state (critical/warn), same rule Mintlify's doc calls out for its own green: functional punctuation, not decoration.

## Tokens — Typography

### Inter — the only family in the system
`FONT = "'Inter', 'SF Pro Display', 'Segoe UI', system-ui, -apple-system, sans-serif"`. `MONO` is the same stack — there is no separate monospace face, including for numbers in the funnel/bar-chart primitives (`font-variant-numeric: tabular-nums` does the alignment work a mono face would otherwise do).

Loaded via `@import url('https://fonts.googleapis.com/...')` inside the injected `<style>` block — every page pays this cost once, on first paint.

### Type Scale (as used, not aspirational)

| Role | Size | Weight | Notes |
|------|------|--------|-------|
| Hero H1 | `clamp(2.2rem, 4.4vw, 3.6rem)` | 680 | `line-height: .96`, `letter-spacing: -0.04em` — the only place type gets this large |
| H2 (section) | `clamp(1.6rem–2.2rem, ...)` per-section | 680 | `line-height: 1`, `text-wrap: balance` on all headings |
| H3 (card title) | `1.15–1.35rem` depending on card class | 720 | |
| Body / `.stMarkdown` | `14.5px` | 400 | `line-height: 1.6` |
| Note / caption | `13px` | 400 | `.note`, `.lede` |
| **Meta / data label** | **`12px`** | 400 | `.meta`, monospace-styled via the shared `MONO` stack. Meets the 12px body-text floor; do not drop it lower. |
| Chip / tag | `10.5–12.5px` | 500–800 | Theme IDs, source tags, status-row labels |
| Eyebrow (`.section-id`) | `11px` | 850 | Uppercase, `letter-spacing: .15em`, always paired with a `::before` 28px rule, never used bare |

**Weight vocabulary:** 400 (body), 500–600 (labels, buttons), 680 (headings), 720–850 (card titles, eyebrows). There is no 300 or 900 anywhere in the system.

## Tokens — Spacing & Shape

**Density:** comfortable-to-airy (VISUAL_DENSITY ≈ 3–4 on the 1–10 scale, per `design-taste-frontend`'s dial vocabulary) — `.scene` sections use `padding: 30px … 78px`, cards breathe at 18–36px internal padding.

### Radius rule (from `charts.py`'s own docstring — applied everywhere, no exceptions)

| Token | Value | Applies to |
|-------|-------|------------|
| `RADIUS_LG` (`--radius`) | **28px** | Panels, cards, tiles, the settings drawer, expanders, the run-log status box |
| `RADIUS_SM` | **14px** | Controls, inputs, buttons, bar-chart ends, code blocks |
| `RADIUS_PILL` | **999px** | Chips and status dots *only* |

Component classes deviate slightly from the two named tokens for visual variety (`.layer` 26px, `.quote-card` 30px, `.integrity-shell` 38px, nav pill 20px) — treat these as "large-radius family," interchangeable with `RADIUS_LG`, not as a third independent value to invent new numbers within. **When two components sit flush against each other with no gap** (e.g. a status panel stacked directly on a button), they must round only their *outer* corners as one continuous shape (`R R 0 0` / `0 0 R R`) — see the `.st-key-statusstack` pattern in `chrome.py`. A visible seam of two different radii at a zero-gap joint is a bug, not a style choice.

### Shadows

| Name | Value | Token |
|------|-------|-------|
| Soft | `0 12px 42px rgba(61,81,128,.1), inset 0 1px 0 #fff` | `SHADOW_SOFT` |
| Deep | `0 24px 80px rgba(58,75,118,.14), inset 0 1px 0 rgba(255,255,255,.96)` | `SHADOW_DEEP` |

Both are tinted toward the canvas's blue-violet hue, never neutral black — same discipline `design-taste-frontend` calls out generally ("tint shadows to the background hue").

### Layout

- **Page max-width:** 1240px (`.block-container`)
- **Scene padding:** `30px [responsive gutter] 78px` per section
- **Card grid gap:** 10–14px depending on density
- **Nav pill:** fixed, `min(calc(100% - 36px), 900px)` wide, centered, `top: 18px`

## Components

### Nav Pill
Fixed glass pill, `z-index: 999`, built from a real `st.container(key="navshell")` wrapping real `st.page_link` widgets — not raw `<a>` tags (Streamlit's own header sits at a higher default z-index and silently swallows clicks meant for a plain anchor underneath it; `st.page_link` is a first-class widget so it isn't subject to that). Capped at 900px even on wide viewports, so it never covers a full-width row of scrolling content by itself — **that's what the nav-scrim (below) is for.**

### Nav Scrim
A full-width fixed bar, `z-index: 998` (just under the pill), `mask-image` fade from opaque-canvas to transparent over its ~92px height. Exists because the pill alone left scrolling content colliding visibly with its edges on wide viewports. Any new fixed header element must sit *under* this scrim or extend it.

### Settings Drawer (`page_engine.py` only)
Fixed, right-anchored overlay panel (`position: fixed`, `width: min(360px, calc(100vw - 36px))`, slides via `translateX` + `opacity`). Open/closed state is baked into a small trailing `<style>` override written fresh on every Streamlit rerun — **not a JS-toggled class**, because `<script>` tags injected via `st.markdown()` never execute (standard `innerHTML` behavior, not a Streamlit bug). Dismiss paths: the `✕` button, and a full-viewport invisible `st.button` layered between the backdrop and the drawer (click-outside-to-close). **There is no Escape-to-close** — that needs a real keydown listener, which hits the same script-tag wall. Known, accepted limitation; don't silently re-attempt it without a custom Streamlit component.

**Information architecture:** the drawer opens by *restating* the main page's config summary sentence ("Currently: 4 of 4 sources, 10 records per run") before presenting any controls — opening it should read as zooming into that sentence, not switching to an unrelated screen. Below that, two labeled groups, not a flat widget list: **"What to run"** (the multiselect + slider — real adjustable settings) and **"Readiness"** (collapsed to a single "Ready to run" line when nothing's missing; only breaks out into named per-provider rows — "Gemini classifier", "YouTube Data API" — when something actually needs attention). Named credential rows are *not* the default view: a viewer pressing a demo button doesn't need to know which specific vendor API backs which feature, only whether it's ready. See `ux.md` for the reasoning.

Two build traps to remember if this pattern gets reused elsewhere:
1. Streamlit's `stElementContainer` wrapper defaults to `width: fit-content; height: auto` — a "full viewport" click-catcher button needs `width/height: 100% !important` forced down the *entire* ancestor chain (container → element-container → stButton → button), not just the button itself.
2. The generic `.stButton button` rule sets `backdrop-filter: blur(15px)`. Any full-screen invisible button built from it must explicitly override `backdrop-filter: none`, or it blurs the entire page behind it.

### Control Console (`page_engine.py`, `st-key-console`)
Engine-only. A bordered instrument frame (1px glass border, 2px teal top rule, `var(--radius)`, glass-solid fill, compact `20px 22px 18px` padding, **`max-width: 900px`** — capped narrower than the 1240px results panels below it on purpose: the console sits under a ~22ch/58ch hero headline+lead, and at full page width the four step rows were mostly dead space between a left-hugging title and a right-hugging status. The "What this batch found" results section keeps full width — a separate section with its own eyebrow, and the width shift reads as instrument → findings) that is the terminal element of the Engine hero — not a section that follows it. It holds, in order: a row of `[ Run live discovery ]` (primary) + the gear + a one-line `status_row` readiness summary; the `.console-strip` "Execution" label (mono, hairline); and the four-step execution timeline. The timeline renders here in **all** states — `pending` on idle load, the live `st.empty()` choreography during a run, the re-openable `st.expander`s after — so the first viewport is always headline + control + visible mechanism, never headline + button + prose. Earlier versions used an unstyled `st-key-actionframe` grouping and only rendered the timeline once a run was clicked; that left the idle page reading as an editorial article about the pipeline. Do not append a separate `st.status` widget below the console.

### Gear / Run-settings button (`page_engine.py`, `st-key-open_settings`)
Engine-only. A compact `st.button("⚙", help="Run settings")` sitting immediately right of Run inside the console, in its own narrow `st.columns` cell. It opens the existing Settings Drawer. It is deliberately a utility control, not a second action: **secondary weight comes entirely from the plain glass `.stButton` fill against Run's animated-gradient `type="primary"`** — no new color, no new component. It keeps the base `.stButton` `RADIUS_SM` (matches Run) — never the 28px panel token or a 999px pill, either of which makes it read as a card competing with Run. `min-height` is pinned to Run's so the pair reads as one unit with no mismatched seam. Plain `⚙` glyph (U+2699), not the VS16 emoji variant. Tooltip/accessible label "Run settings"; Streamlit's focus ring is kept. There is no longer a textual "Configure" link in the reading flow — the gear is the only entry point to run settings from the page body.

### Execution Timeline (`charts.exec_step`, `.exec-step`)
Four **persistent** step cards — Fetch, Normalize, Classify, Validate — that never get replaced the way a single `st.status()` box's contents used to be overwritten at each stage. Each card only ever changes its own state:

- **pending** — quiet, `opacity:.62`, an `○` glyph, and a one-line *blurb* ("Query every public source in parallel") in the middle zone so the resting console reads as the plan for a run, not four empty rows. State label reads `queued`.
- **running** — the one card with real visual weight: teal border + ring (`box-shadow`), a pulsing "LIVE" label, and a detail pane capped at `max-height:190px` with internal scroll — a fast-growing log (per-source rows) scrolls in place rather than pushing the page taller. Classify is the one stage that is a single blocking call with nothing to stream: instead of a frozen "waiting…" line it renders the real in-flight manifest (record count, per-source breakdown, 2–3 actual snippets — all staged from the `normalize` payload *before* the blocking call) plus `.exec-shimmer`, a pure-CSS indeterminate sweep that keeps animating while Python is blocked (same mechanism as `.exec-step-live`'s pulse).
- **done** — compact (`min-height:0`, `7px 16px` padding), a `✓`, and one line: `summary · timing` (e.g. `4 of 4 sources responded · 5.5s`; Normalize's is the terse count chain `331 → 179 → 120 → 10 records`, from `pipeline.py`). Timing rides the summary line, **not** a stranded right-hand column — that gap was dead space. No detail rendered inline.
- **error** — coral border/badge, reserved for the step that was running when `result.error` got set.

A short vertical connector (`.exec-step.linked::after`, absolutely positioned — not a flex child, because `.exec-step.running` switches to `flex-direction:column`) bridges steps 1→2→3→4 so they read as one pipeline; it goes teal once a step is `done`.

**Why not `st.expander` for the live choreography:** an expander's `expanded=` is fixed at creation and can't be flipped mid-script, and nothing is clickable while the script is blocked inside `pipeline.run()` anyway. The four cards are `st.empty()` placeholders rewritten with plain HTML as `on_stage` fires — cheap, and correct for a moment where the user can't interact regardless.

**Why the four steps reappear after the run:** `page_engine.py` stores each step's title/summary/detail/timing/state into `st.session_state["run_log"]` as it goes, then calls `st.rerun()` the instant `pipeline.run()` returns. That rerun lands on `elif st.session_state.get("run_log")...`. Because the completed state's job is to make the *results payoff* dominant (ux.md / STEP 5), not the execution history, that branch renders **only** the compact `done`-card strip (accumulated ✓✓✓✓ + connectors + inline timing) and the `.run-complete` cap. The full per-step detail is **not** in the console — it renders as a collapsed `st.expander` ("Full execution trace · Ns end to end") near the bottom of the page, beside "How the sample was selected", after the discovery results. Two rendering paths (live `st.empty()` cards, post-run `run_log` replay), one data model; don't let them drift.

**Execution → Discovery transition (completed state only).** A first-time viewer can otherwise stop at the completed console thinking it *is* the output. The composition carries the `EXECUTION → RUN COMPLETE → DISCOVERY` narrative without a "scroll down" line:
1. **Top control is state-aware** — the primary button label flips `Run live discovery` → `Run again` once `run_log` exists (styling and the gear unchanged), and the `meta_col` row drops to `Complete · run again for a fresh sample`. Both signal "the run is finished, this is its result."
2. **`.run-complete`** — the console's terminal element: a teal-tinted cap (`rgba(0,127,131,.09)` fill, 2px teal left rule) reading `✓ Run complete · N sources · N records · Ns end to end`. It closes the execution chapter. The compact step strip above it is tight enough that this cap sits fully within the first post-run viewport.
3. **`.result-flow`** — a short vertical connector + downward chevron on the **same left axis (`left: 26px`) as the step connectors**, between the console and the Discovery heading (negative bottom margin pulls the eyebrow up under it), so the pipeline visibly continues into the results.
4. The results eyebrow is **`Discovery`**; the full-size `<h2>` is followed by a single quiet `.meta` provenance line (`From N sources · N records · mapped onto the twelve locked themes, not re-derived`), **not** the old explanatory paragraph — the methodology is already on the idle screen and the trust line. The **selection funnel** and the **execution trace** are both collapsed `st.expander`s *below* the theme chart and quotes — P1 process context, never between the run and the payoff.

### Error Panel (results state, `result.error`)
A `.panel` with a 2px coral left border and a "Run failed" `.meta` label, not a bare `st.error()` red box — failure should look like the rest of the page, not a foreign component dropped into it. Reserved for the case `ux.md` defines as the error state (nothing to show at all); a partial/degraded run is not this state and renders normally. The sources-queried panel and, where the data exists, the selection funnel still render above the error panel — a classify-stage failure still has real fetch/normalize data worth showing. Gate that on `selection_stats` having data, not on the absence of an error.

### Status Panel + Action Button (stacked, zero-gap)
Wrapped in a keyed container (`st-key-statusstack`) so the two can share one outer-rounded shape instead of showing a mismatched-radius seam at the touching edge. See the Radius Rule above. This panel shows one line — a plain-language config summary plus a single readiness dot (`ok`/`bad`) — not a named credential row; see Settings Drawer above for why.

### Quote Card / Theme Card (`.quote-card`, `.layer`)
Glass surface, hover lift (`translateY(-6px)`, shadow grows), a diagonal "glare" sweep on hover (pure CSS, `::after` pseudo-element, no JS/cursor-tracking). `reveal-in` mount animation plays once per page-load, never re-triggers on a Streamlit rerun the page doesn't own.

### Multiselect (`st.multiselect`)
As of the current Streamlit version, this renders on **React Aria, not BaseWeb** — there is no `[data-baseweb="..."]` attribute anywhere on the page. Style hooks: `[role="group"]` for the control box, `[data-tag]` for each tag pill (a real Streamlit-stamped attribute, confirmed via computed styles — **do not** style against `st-emotion-cache-*` classes, they're hash-based and not selector-stable across versions). The clear/dropdown icon buttons are flex siblings of the tag list (`[data-testid="stMultiSelectTagsContainer"] ~ button`), not children — they default to `align-self: center` against the *whole* control's height and will float in dead space the moment tags wrap past one row unless pinned to `flex-start`.

### Chart Primitives (`charts.py`)
`bar_chart`, `stat_tile`, `sentiment_row`, `step_strip`, `funnel`, `status_row`, `factor_rows` — all plain HTML/CSS, deliberately not a plotting library (dependency weight, startup time, and exact control over the mark spec — rounded data-ends anchored to a baseline, hairline gridlines — that a library would fight). Magnitude is always carried by bar *length* on a single hue, never a color ramp; `status_row`'s colored dot is the one place a decorative-looking dot is allowed, because it carries real semantic state (configured/missing/degraded).

## Do's and Don'ts

### Do
- Style Streamlit's own widgets by `[data-testid="..."]` or a genuine ARIA role/attribute (`[role="group"]`, `[data-tag]`) — these are the only selector types confirmed stable across a Streamlit version bump.
- Use real typographic characters in visible copy (`→`, not `->`); ASCII stand-ins read as broken formatting. Follow the frontend/UI skills on copy punctuation and tone.
- Round only the outer corners when two components sit flush with no gap between them.
- Verify a claimed CSS rule is actually live with a computed-style check (`getComputedStyle`) before trusting it, especially after a Streamlit version upgrade — an entire selector family (`[data-baseweb]`) can silently stop matching anything.
- Keep body/meta text at 12px or larger.
- Use the descendant combinator for `.stButton` rules (`.stButton button`), never a direct child (`.stButton > button`). See Constraints below — confirmed to break silently the moment `help=` is added to any button.
- Show a single readiness signal by default for viewer-facing config; break out named implementation detail (specific provider/credential names) only when something's actually not ready.

### Don't
- Don't introduce a second flat accent color. Teal is the only standalone accent; Indigo/Violet are gradient-only.
- Don't add a shadow tinted pure black or pure gray — tint toward the canvas's blue-violet.
- Don't assume a CSS transition will animate across a Streamlit rerun the way it would on a live DOM mutation elsewhere — it depends on whether the keyed container is diffed in place or remounted. Verify in the browser, don't assume.
- Don't write a client-side interaction (Escape-to-close, scroll-position-aware nav) that depends on injected `<script>` execution — it will not run. Solve with real Streamlit widgets + CSS state, or accept the limitation explicitly.
- Don't restate these tokens as new hex/px literals in a page file. Import from `charts.py`.
- Don't gate "does this section have data to show" on `result.error` — gate on whether the relevant data actually exists (e.g. `selection_stats` being populated). A classify-stage failure still has real fetch data; don't hide it because a later stage failed.

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Canvas | `#eef5ff` + radial-gradient wash | Page background, fixed attachment |
| 1 | Glass | `rgba(255,255,255,.55)` + blur(26px) | Primary panel surface — cards, tiles, the drawer |
| 2 | Glass Solid | `rgba(251,253,255,.92)` | Near-opaque panel where legibility over motion matters more than translucency (status rows, credential panels) |
| 3 | Ink | `#11182b` | Primary button fill, dark inverted-text contexts |

## Layout

Two pages, one shared chrome, **deliberately different page-level composition**. They must feel like one product (identical nav, canvas, tokens, Inter + weight vocabulary, ink/teal palette, component language, `st.columns`-ratio asymmetry with no width-capped container) while a viewer switching between them without reading the URL immediately perceives two different experiences: Findings is for **reading** the research, Live Engine is for **running** the pipeline.

`Findings` (default route, no explicit `url_path` — a deliberate Streamlit quirk workaround, see `app.py`) is the static analysis story, an editorial article: `.cover-kicker` pill → large `.cover-h1` with a gradient `.accent-word` phrase → `.subhead` → a CTA that closes the hero's argument, then a repeated `scene whitespace → .section-id eyebrow → <h2> with one accent phrase → .note → full-grid content` rhythm down the page (evidence stats → what-we-found → consumer voices → pipeline → sources/pivots → signal landscape → integrity).

`Live engine` (`/engine`) uses an **instrument grammar**, not that editorial one:
- **Hero = instrument masthead.** `.engine-eyebrow` (mono, uppercase, leading teal rule — not a pill-chip) → `.engine-h1` (`clamp(1.9rem,3.2vw,2.8rem)`, solid ink, **no gradient accent-word**, tighter than `.cover-h1`) → one `.engine-lead` line. Shared face and weights, smaller scale, different arrangement.
- **Hero's terminal element = the Control Console** (`st-key-console`, see Components), not a CTA section. Action → live execution → discovery reads off the console's structure: run control + gear on one axis, then the four-step execution timeline, visible in every state.
- **Below the console: no editorial `<h2>` section until the results payoff.** Methodology / themes are demoted to a compact `.engine-measure` label + chip strip + one disclosure ("what the engine measures against"), subordinate to the run action, timeline, live state, and results — never the `.section-id → <h2> → .note` treatment Findings gives its own methodology.
- **Results keeps the full-size `<h2>`** (`"N of 12 locked themes fired…"`), larger panel padding, and the run's config echoed back into it. This is the DISCOVERY leg of the arc and earns the one editorial moment on the page; the ranked bar chart + Consumer-Voices-style quote trio below it reuse Findings' components intentionally.
- Then the trust/export line (never in a collapsed expander).

Do not re-add a shared "both pages open with the same shape" rule, a `.cover-h1`/`.cover-kicker` treatment on the Engine hero, or a gradient accent-word in `.engine-h1` — the divergence is the point, and CLAUDE.md's tiebreak (skills win on composition) backs it. Tokens, radius, color, nav, and spacing *scale* stay shared.

Navigation is a single fixed floating pill, transparent-canvas-to-content (no separate "on hero vs. on content" nav treatment, unlike sites with a dark hero band — this app has no dark hero, so the nav pill's glass treatment is constant everywhere).

The brand mark is `assets/evidence-atlas-logo.png` — a finished rounded-square app icon in the system's own teal→indigo→violet gradient, carrying its own edge and highlight. It renders as an `<img>` (never cropped): 38px in the nav pill (`.brand-icon`, lifted by a drop-shadow that follows the PNG alpha, slight rotate-scale on `.brand:hover`) and 38px in the shared page footer (`chrome.footer()` — the closing brand mark: the nav pill's `[icon + name]` lockup on the canvas. Findings passes `end_label="End of Atlas"`, rendered above the lockup in the left-anchored `.section-id` eyebrow idiom — its 28px tick is the terminus rule, a bookend to the section eyebrows above it, so that footer carries no separate divider. The Live Engine passes nothing (a tool you ran, not an atlas you finished) and falls back to a thin full-width end rule. No tagline on either). `chrome._logo_data_uri()` inlines the 96px copy as a data URI in both places (no extra asset route); the 256px copy is the `st.set_page_config(page_icon=…)` browser-tab favicon. Both sizes live in `phase3_live_engine/assets/` so the phase stays independently publishable.

## Agent Prompt Guide

Quick reference:
- primary accent: `#007f83` (Teal) — flat fill, links, chart series
- gradient trio (never flat): `#11182b → #007f83 → #5646c9 → #8d79e8` depending on component (hero accent-word vs. primary button shine use different subsets/order — check `chrome.py`'s `.accent-word` and `button[kind="primary"]` rules directly rather than assuming one universal gradient string)
- text: `#34405a` (body) / `#11182b` (headings) / `#65718a` (muted/meta)
- background: `#eef5ff` base + radial gradient wash, `background-attachment: fixed`
- panel: `rgba(255,255,255,.55)` + `blur(26px) saturate(145%)`, border `rgba(255,255,255,.88)`
- radius: 28px (panels/cards) · 14px (controls/buttons) · 999px (chips/dots only)

Example component prompt: *"Create a status panel: glass-solid background (`rgba(251,253,255,.92)`), 28px radius, 1px `rgba(255,255,255,.88)` border, 12–14px padding, containing a 12px meta line and a `status_row` (7px dot + label + muted detail). If it sits flush against a button below with no gap, round only the outer corners of the pair."*

## Constraints Worth Remembering (Streamlit-specific)

- **No client-side JS.** `<script>` tags injected via `st.markdown()` never execute. Every "interactive" behavior (drawer open/close, hover states, mount animations) has to be either pure CSS or a real Streamlit widget driving `st.session_state` + `st.rerun()`.
- **Hot-reload is not guaranteed.** This app's dev server has shown both behaviors in the same session — sometimes a `st.rerun()`-triggering click picks up an edited `.py` file, sometimes it takes a full process restart. When a CSS/copy change doesn't appear to take effect, restart the server before concluding the fix is wrong.
- **BaseWeb is gone.** Current Streamlit renders on React Aria. Any inherited guidance (including in older comments in this codebase) that references `data-baseweb` attributes should be treated as suspect until verified against the live DOM.
- **`st.button(..., help=...)` changes the DOM around the button.** Adding a `help=` tooltip wraps the button in `stTooltipIcon`/`stTooltipHoverTarget` divs for the hover "?" affordance. Any CSS selector written as a *direct child* of `.stButton` (`.stButton > button`) silently stops matching the moment `help=` is added anywhere — confirmed live: the primary run button reverted to Streamlit's stock blue, computed `background-image: none`, the instant a `help=` string was added to it. Every `.stButton` rule in `chrome.py` now uses the descendant combinator (`.stButton button`) specifically because of this.
- **Real stage timing isn't even.** Live test runs of the pipeline have varied from ~5s to ~29s total, with the classify stage (one blocking Gemini call) typically the largest single share when the run isn't near-instant. The Execution Timeline (above) doesn't need to encode this directly since it shows each step's actual elapsed detail once done, not a proportional bar — but any future progress UI for this pipeline should stay aware that step durations are uneven and can vary run to run, not budget a fixed animation length per step.
- **Content height changes substantially and repeatedly across empty → running → results**, and this is only partially mitigated, not solved. Streamlit doesn't offer an easy, robust way to reserve exact pixel space for content that hasn't rendered yet without guessing a fixed height that could be wrong for a different run's content. If a future pass wants to fully eliminate scroll-jump during a run, that likely needs a custom Streamlit component, not more CSS.

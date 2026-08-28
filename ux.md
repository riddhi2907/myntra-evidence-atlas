# Evidence Atlas — UX Guide
Complements DESIGN-SYSTEM.md (tokens, CSS, components). This file covers page
purpose, states, and interaction judgment calls — not colors, type, or CSS.
If a rule here would require restating a hex value, radius, or class name,
it belongs in DESIGN-SYSTEM.md instead; link to it, don't repeat it.

## Page purpose and user goals

The app answers one question for a grader/reviewer: **"is the Wishlist
research pipeline real, and does it work on evidence it hasn't seen before?"**

- **Discovery Findings** (`/`, default route) — the static story. Sixteen
  thousand records already classified. Goal: let a first-time viewer
  understand the corpus, the themes, and the metric decomposition without
  clicking anything.
- **Live Engine** (`/engine`) — the proof. Goal: let the same viewer press
  one button and watch the pipeline fetch, classify, and map fresh public
  records in real time, using the same codebook and theme set as Findings.

Both pages exist to be *trusted*, not just used. Every design and copy
decision should ask: does this make the pipeline's behavior more legible, or
does it just make the page busier?

## Findings vs. Live Engine responsibilities

| | Findings | Live Engine |
|---|---|---|
| Data | Precomputed, static | Fetched at click time, ephemeral |
| Themes | Displayed as derived (already clustered) | Displayed as matched against the same locked set |
| Metric nodes | Shown as the decomposition story | Not shown (cut — see DESIGN-SYSTEM.md Layout) |
| Primary interaction | Scroll | One run button + a gear opening the settings drawer |
| Page grammar | Editorial article (kicker pill → gradient cover-h1 → repeated section-id/`<h2>` rhythm) | Instrument (mono eyebrow → tighter solid-ink headline → control console → execution timeline). Shared DNA, deliberately different composition — see DESIGN-SYSTEM.md Layout |
| Proof burden | None — numbers are the artifact | High — must show its own work (status feed, source panel, audit line) |

Do not let Live Engine grow Findings-style narrative sections (e.g. a second
metric-decomposition block) — that duplication was deliberately cut once
already (see `page_engine.py`'s module docstring). Do not let Findings grow
interactive controls — it has none by design, and adding one blurs the
static/live distinction that is the whole point of having two pages.

## Information hierarchy

Both pages open with a left-anchored eyebrow → headline → one-sentence lead,
on the shared grid — but in **deliberately different registers**: Findings'
is an editorial cover (kicker pill, large gradient `.cover-h1`), Live
Engine's is an instrument masthead (mono `.engine-eyebrow`, tighter
solid-ink `.engine-h1`, no gradient phrase) whose next element is the
control console, not more prose. See DESIGN-SYSTEM.md Layout. That opening
sentence is still the page's thesis on both; if a change to it doesn't read
as true in one breath, the copy is wrong, not just the layout.

Below the hero, order content by **how much a viewer needs it before they
can trust anything else on the page**:
1. Proof the pipeline actually ran / actually has data (evidence stats /
   status feed) — before any interpretation.
2. The finding itself (themes, quotes) — the payload.
3. How to verify it independently (audit line, export, quote-source links) —
   always last, always present, never hidden behind an extra click on
   Live Engine (trust content doesn't belong in a collapsed expander).

## States

**Findings** has effectively one state (loaded) since its data ships with
the app — no empty/loading/error UI is needed there.

**Live Engine** has four, and all four must be distinguishable from a
screenshot alone (no state should look identical to another minus a spinner):

- **Empty / idle** — before the first run this session. Controls visible,
  and the four execution steps visible in their `pending` state inside the
  console (they are the *plan* — "here is what a run does" — not a null
  result; each `pending` card is quiet (`opacity .62`, an `○` glyph,
  `queued`) but carries a one-line blurb of what that stage does, so the
  resting console reads as a labeled pipeline rather than four empty rows,
  and stays unmistakably distinct from `running` and `done`). No results section rendered — literally absent, not a "0 results"
  placeholder, so the page doesn't imply a run already happened.
- **Running** — a persistent four-step execution timeline (Fetch, Normalize,
  Classify, Validate) is the state, not a spinner or a single log box whose
  contents get overwritten at each stage. All four steps are visible
  throughout the run; a viewer should be able to tell what step it's on, and
  see what already happened, without reading code. This is the page's core
  credibility mechanism — never replace it with a generic "loading..."
  message.
  - **Each step keeps its own history.** The step that just finished doesn't
    disappear or get overwritten by the next one — it collapses to a
    checkmark + one-line summary and stays visible above the now-running
    step. This is a deliberate correction from an earlier version of this
    page, where a single `st.status()` box's content was replaced stage to
    stage — that discarded the run's own history the moment the next stage
    started, which worked against the page's whole point (proving the
    pipeline actually did something, visibly).
  - **Only the running step gets strong emphasis** (teal border, a live
    indicator) — pending steps stay quiet, completed steps stay compact.
    Nothing about a finished step should compete with the step actually
    running for attention.
  - **Completed steps stay re-openable**, not just visually present. Once
    the run finishes the four steps collapse to a compact ✓-card strip and
    their per-step detail (which sources responded, the funnel counts, the
    theme tally, the verification detail) folds into a single
    "Step-by-step detail" `st.expander` — one disclosure rather than four,
    because the completed state's job is to make the results payoff
    dominant, not the execution history (see `DESIGN-SYSTEM.md`'s Execution
    Timeline entry).
  - **Real content substitutes for a skeleton, deliberately.** This file
    already banned skeleton loaders as liveness-faking (below). The
    corollary: since a skeleton is off the table, the real progressively-
    arriving content (per-source rows, the classify-time theme tally) has to
    actually carry the "something is happening and here's roughly what's
    coming" job a skeleton would otherwise do.
  - **Known, accepted limitation:** total page height still changes across
    empty → running → results, since four stacked step cards are themselves
    taller than the single collapsed box that preceded them, and the running
    step's own detail pane grows (up to its capped max-height) as content
    streams in. Each step's detail pane is capped and internally scrollable
    specifically to bound *that* growth, but the page as a whole isn't
    pinned to a fixed height. A full fix likely needs a custom Streamlit
    component to reserve exact pixel space in advance; don't attempt a
    CSS-only "solution" that guesses a fixed height, it'll be wrong for some
    run.
- **Results** — ranked themes, quote cards, audit line, export. A
  partial result (e.g. one source failed) is still a results state, not an
  error state — see below.
  - **The completed console must not read as the output.** A first-time
    viewer can stop at the four ✓ steps and think "that's it." Defences, in
    order: the primary button flips to **`Run again`** and the status row to
    `Complete`; the four steps collapse to a tight one-line-each strip
    (`outcome · time`); a **`.run-complete`** cap closes the chapter; a
    **`.result-flow`** connector+chevron flows the eye down; the payoff opens
    on a `Discovery` eyebrow + full-size `<h2>` (followed by one quiet
    provenance line, not a paragraph). The hierarchy itself carries
    `EXECUTION → RUN COMPLETE → DISCOVERY`. Priority below the run: **P0**
    themes fired + evidence quotes · **P1** execution summary, selection
    funnel · **P2** source breakdown, methodology. Both the selection funnel
    ("How the sample was selected") and the full per-step execution trace
    ("Full execution trace") are collapsed disclosures *below* the quotes —
    optional process transparency, never between the run and the payoff.
- **Error** — reserved for the case the page has *nothing* to show (the
  classification call failed entirely, per DESIGN-SYSTEM.md's "single point
  of failure" note). A degraded-but-nonempty run is not this state.

**Per-source failure is not a page-level error.** Following the existing
invariant ("shown in the UI as failed, with the reason — never silently
dropped"), a source that fails renders inline in the source panel with its
reason, and the run proceeds to results with whatever the other sources
returned. Never let one source's failure block or blank the whole page.

## Interaction principles

- **One primary action per page state.** Live Engine's primary action is
  "run"; once results exist, there is no second competing primary button —
  re-run, export, and settings are secondary/tertiary weight.
- **Every control's effect must be visible without leaving the page.**
  Opening the settings drawer, toggling a source, changing record count —
  none of these require a rerun to confirm; the drawer state itself is the
  confirmation.
- **Nothing here fakes liveness.** No skeleton loaders standing in for data
  that isn't coming, no optimistic UI implying a result before the API has
  returned one. Given the page's whole purpose is proving the pipeline is
  real, a state that misrepresents timing undermines the point of the page.
- **Prefer a real Streamlit widget over a CSS/JS approximation** wherever
  one exists (per DESIGN-SYSTEM.md's client-side-JS constraint) — this is a
  UX call as much as a technical one: a fake control that silently doesn't
  do what it looks like it does is worse than a plainer real one.
- **Show readiness, not implementation detail, by default.** The audience is
  a grader/reviewer pressing a demo button, not the developer. Config UI
  should default to one signal ("ready to run" / "not ready, see why") —
  naming specific providers or credentials ("Gemini classifier," "YouTube
  Data API") is implementation detail that belongs one level down, surfaced
  only when something's actually not ready and the viewer needs to know
  which piece. This generalizes past the settings drawer: any future
  viewer-facing config on either page should default to the same collapse.
- **A result should carry a visible thread back to the config that produced
  it.** The settings drawer is closed and its state forgotten (visually) by
  the time a result renders below. Echo the run's actual config (source
  count, record count) back into the results section itself — a viewer
  shouldn't have to remember or scroll back up to know what was run.

## Copy / tone

- Direct and factual, second person to the viewer where natural ("Press
  run."), never marketing voice ("Unlock powerful insights!").
  See existing hero copy in `page_findings.py` / `page_engine.py` for the
  register to match.
- State what's real plainly: "nothing here is precomputed," "ten records are
  a demonstration, not a finding" — the app's existing copy already
  self-qualifies its own limitations; keep doing that rather than smoothing
  it into generic confidence.
- No unnecessary exclamation points, no emoji, no filler adjectives
  ("amazing," "seamless"). One clean sentence beats a punchy one here.
- Numbers get exact framing, not vibes: "0–4 quote failures per run," not
  "very few failures."
- For punctuation and tone, follow the frontend/UI skills (see CLAUDE.md's
  "UI work (Phase 3)"). ASCII stand-ins for real characters ("->" for "→")
  read as broken formatting.

## Accessibility expectations

- Meet the 12px body-text floor already codified in DESIGN-SYSTEM.md — don't
  reintroduce sub-12px text anywhere, including new components.
- Every status-dot / colored state (ok / warn / critical) must carry a text
  label alongside the color — color is never the only signal (this already
  holds for `status_row`; preserve it in any new indicator).
- Interactive elements (buttons, links, the settings drawer's dismiss paths)
  must have a visible focus state — don't strip Streamlit's default outline
  without replacing it with an equally visible one.
- Images/icons that carry meaning (not pure decoration) need accessible
  text — alt text or an adjacent label, not color/shape alone.
- Contrast: body text on glass surfaces must hold up against the *lightest*
  point of the canvas gradient behind it, not just the average — check on
  the brightest region of `.stApp`'s background, since glass is translucent.
- Known, accepted gap (per DESIGN-SYSTEM.md): no Escape-to-close on the
  settings drawer. Don't silently re-attempt a JS fix; either add a real
  Streamlit-widget-driven close path or leave it as a documented limitation.

## Definition of done for UI changes

A UI change is done only when all of the following hold:

0. It went through CLAUDE.md's "UI work (Phase 3)" process: multiple
   frontend/UI skills consulted as critique lenses, composition established
   before implementation, self-critique done.
1. It follows DESIGN-SYSTEM.md's tokens/components with no new hex/px
   literals restated outside `charts.py`.
2. It fits this file's page responsibilities (§Findings vs. Live Engine) and
   information hierarchy — no scope creep across the two pages.
3. Every state it touches (empty/running/results/error) still looks
   distinguishable from the others.
4. It has been **viewed in a running browser** (`streamlit run app.py`), not
   just read as a diff — per the project's UI verification standard.
5. If the change touches Live Engine, verification used the **idle/empty
   state and any cached/previous run output already on screen** — it did
   **not** trigger a fresh paid API call (Gemini/YouTube/Groq) just to look
   at a screen. If seeing the results state genuinely requires a live run,
   that's a call for the user to make, not one to trigger automatically.
6. Copy changes were read once for tone (§Copy/tone) and checked against the
   frontend/UI skills' copy guidance before committing.

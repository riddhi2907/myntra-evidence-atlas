"""
Keyword relevance scoring and the brand gate -- the two things that decide
which fetched records reach the classifier.

In Phase 1 this scoring was a *diagnostic only*: collection deliberately kept
low-scoring records so downstream analysis could decide (plan.md's "don't
perform analytical filtering prematurely"). A live demo has the opposite
constraint -- it can only show ~10 records, so something has to choose which
10. This module is that chooser, and the choice is made explicit in the UI
rather than hidden.

Two rules do the work:

1. **The brand gate.** A record must be about Myntra. YouTube comment threads
   and Reddit fashion subs are full of posts about Ajio, Meesho and Amazon that
   have nothing to do with the research question; before this gate existed they
   reached the classifier because competitor names were being scored as
   positive keywords. Now a competitor mention only counts *when Myntra is also
   present*, where it is genuine cross-platform comparison evidence (theme T5).
   Alone, it is noise.

2. **Weighted scoring.** Wishlist language scores highest, then explicit
   journey narrative, then decision-factor vocabulary.

Note on scope: the fellowship brief and the Phase 2 codebook both frame the
subject as "Myntra/AJIO". This engine gates on **Myntra only** -- AJIO is
treated as a competitor whose mention is comparison signal, not as a second
in-scope brand. Widen `PRIMARY_BRAND_TERMS` if that framing changes.

Keyword sets are condensed from phase1_collection/reference_code/keywords.py.
"""

from __future__ import annotations

import re

# The gate. A record must mention one of these to be about our subject at all.
# Misspellings are included because app reviews and comments are full of them
# and they are unambiguous.
PRIMARY_BRAND_TERMS = ["myntra", "myntara", "mynthra", "myntraa", "mantra app"]

# Other platforms. These are NOT scored on their own -- see the module
# docstring. When Myntra is present too, they are strong comparison signal.
COMPETITOR_TERMS = [
    "ajio", "amazon", "flipkart", "meesho", "nykaa", "tata cliq", "tatacliq",
    "shein", "zara", "h&m", "westside", "snapdeal", "limeroad", "urbanic",
]

# Direct wishlist / save-for-later vocabulary, incl. Hinglish phrasing.
# `favourite`/`favorite` are deliberately NOT here: in practice they fire on
# "favourite colour" far more than on "add to favourites", so they were pure
# noise in the score. Kept broad enough for `matched_terms` to stay useful.
WISHLIST_TERMS = [
    "wishlist", "wish list", "wishlisted", "wishlisting", "save for later",
    "saved item", "shortlist", "heart icon", "bookmark", "cart", "add to bag",
    "pasand", "baad me", "baad mein", "save karke",
]

# The subset that unambiguously means save-for-later behaviour -- not "cart"
# (fires on every checkout complaint), not Hinglish near-misses. A record
# carrying one of these is the evidence this demo most wants to surface, so it
# gets a large score bonus AND a reserved selection slot (see select_top).
WISHLIST_STRONG = [
    "wishlist", "wish list", "wishlisted", "wishlisting",
    "save for later", "saved item", "save karke",
]

# Journey/intent language -- narrative markers that a record describes a decision
JOURNEY_TERMS = [
    "was going to buy", "didn't buy", "did not buy", "never bought", "finally bought",
    "thinking of buying", "planning to buy", "decided not to", "changed my mind",
    "for my wedding", "for a party", "for office", "gift",
]

# Decision-factor vocabulary: what stops a saved item becoming a purchase
FRICTION_TERMS = [
    "out of stock", "sold out", "size not available", "price drop", "price increase",
    "waiting for sale", "waiting for discount", "expensive", "too costly", "budget",
    "return", "refund", "exchange", "delivery", "delayed", "cancelled",
    "fake", "first copy", "duplicate", "counterfeit", "original",
    "quality", "fabric", "material", "fit", "size chart", "too small", "too tight",
    "loose", "measurement", "review", "rating", "photo", "picture", "looks different",
    "compare", "comparing", "trust", "scam", "cheated", "customer care", "support",
]

WEIGHTS = {"wishlist": 3, "journey": 2, "friction": 1, "brand": 4, "competitor": 2}
MAX_COMPETITOR_BONUS = 4  # one comparison is signal; five brand names is a listicle
# Applied once if any WISHLIST_STRONG term is present. Sized to clear a
# friction-heavy rant (a long generic review hits ~6-10 distinct friction
# terms) so genuine save-for-later evidence outranks it -- the whole point of
# the live demo is the wishlist step, and public feedback is overwhelmingly
# post-purchase complaint.
STRONG_WISHLIST_BONUS = 8

_SCORED = (
    [(t, "wishlist") for t in WISHLIST_TERMS]
    + [(t, "journey") for t in JOURNEY_TERMS]
    + [(t, "friction") for t in FRICTION_TERMS]
)


def mentions_brand(text: str) -> bool:
    """The gate itself. Kept separate from `score` because the two sources whose
    records are brand-scoped by construction (app-store reviews *of the Myntra
    app*) legitimately never say the word."""
    low = (text or "").lower()
    return any(b in low for b in PRIMARY_BRAND_TERMS)


def has_strong_wishlist(text: str) -> bool:
    """True if the text carries unambiguous save-for-later language. Drives both
    the score bonus and the reserved selection slot in select_top."""
    low = (text or "").lower()
    return any(t in low for t in WISHLIST_STRONG)


def score(text: str) -> int:
    """Weighted keyword score. Competitor mentions contribute only when Myntra is
    also present -- there they mark cross-platform comparison (T5); alone they
    would rank an Ajio-only post above a genuine Myntra one."""
    if not text:
        return 0
    low = text.lower()
    total = sum(WEIGHTS[kind] for term, kind in _SCORED if term in low)

    if has_strong_wishlist(low):
        total += STRONG_WISHLIST_BONUS

    if mentions_brand(low):
        total += WEIGHTS["brand"]
        n_competitors = sum(1 for c in COMPETITOR_TERMS if c in low)
        total += min(n_competitors * WEIGHTS["competitor"], MAX_COMPETITOR_BONUS)
    return total


def matched_terms(text: str) -> list[str]:
    """Which terms fired -- shown in the UI so the ranking is inspectable rather
    than a black box. Competitors are only listed when the brand gate passed,
    matching how they are scored."""
    if not text:
        return []
    low = text.lower()
    hits = {term for term, _ in _SCORED if term in low}
    hits |= {b for b in PRIMARY_BRAND_TERMS if b in low}
    if mentions_brand(low):
        hits |= {c for c in COMPETITOR_TERMS if c in low}
    return sorted(hits)


def quote_is_off_subject(quote: str) -> bool:
    """A theme-evidence quote that names a competitor but not Myntra. Used to
    demote such quotes when picking which one to *show* for a theme -- a card
    reading 'Ajio is fraud, never refund your money' under a Myntra return
    theme is technically verbatim but reads as being about the competitor.
    T5 (Cross-Platform Comparison) is exempt: naming a competitor is exactly
    what its evidence should do."""
    low = (quote or "").lower()
    return any(c in low for c in COMPETITOR_TERMS) and not any(b in low for b in PRIMARY_BRAND_TERMS)


_JUNK_RE = re.compile(
    r"^(nice|good|super|ok|okay|best|awesome|thanks|thank you|wow|❤+|👍+|\W+)$",
    re.IGNORECASE,
)


def is_junk(text: str, min_chars: int = 40) -> bool:
    """Filters the 'Good portion' / 'Link' / emoji-only floor that app reviews and
    YouTube comments produce in volume. Not a relevance judgement -- a record
    this short carries no extractable journey signal regardless of topic."""
    t = (text or "").strip()
    if len(t) < min_chars:
        return True
    return bool(_JUNK_RE.match(t))

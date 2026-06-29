"""Shared value-scoring logic for the Fantasy TdF helper.

Why this module exists: the value model is used in three places (the full
integration in simple-pcs-script.py, the daily auto-update in app.py, and any
recompute). Keeping it here means one definition, not three drifting copies.

Model:
  * value_points = season-to-date 2026 points (PRIMARY) blended with a small
    12-month rolling helper. A strong season a year ago does NOT prove a rider
    is good now, so 2026 dominates; 12m only nudges riders whose 2026 sample is
    thin. (weight below)
  * points_per_credit = value_points / price (absolute value signal, also used
    for sorting and team optimisation).
  * value_category = GLOBAL absolute tiers by percentile across the WHOLE field,
    NOT per category. PCS points already aggregate every way a rider scores - GC,
    stage wins, breakaways, one-day races - so a GC leader (who also hunts
    stages) and a sprinter are comparable on total output. Global ranking also
    keeps an absolute meaning: a decent rider (e.g. Onley, 199 pts + strong 12m)
    can't be labelled Poor just for being the relatively weakest leader.
"""

# Weight on the 12-month rolling helper; the rest (the majority) is 2026 form.
BLEND_12M = 0.2

# Top-down share of each tier. Tuned to the agreed global distribution
# (Excellent ~5.5%, Great ~7%, Good ~21.5%, Average ~23%, Poor ~43%).
TIER_SHARES = [
    ("Excellent", 0.055),
    ("Great", 0.070),
    ("Good", 0.215),
    ("Average", 0.230),
    ("Poor", 0.430),
]
TIER_ORDER = [name for name, _ in TIER_SHARES]

# Sprinters only: PCS season points undercount a sprinter's fantasy value (Tour
# stage wins aren't rewarded in PCS the way they are in the game), while the game
# price already anticipates that output. So lift ONLY the sprinter tier badge by
# this factor against the same global thresholds. Nothing else changes — no value
# number anywhere, and no other category's tier. Tune up/down to taste.
SPRINT_BOOST = 1.4


def compute_value_points(points_ytd, points_12m):
    """2026 season points (primary) plus a small 12-month helper.

    Falls back to season-to-date when a rider is absent from the 12-month
    ranking (so domestiques are not double-penalised)."""
    ytd = points_ytd or 0
    p12 = points_12m if points_12m else ytd
    return round(BLEND_12M * p12 + (1 - BLEND_12M) * ytd, 1)


def points_per_credit(value_points, price):
    return value_points / price if price and price > 0 else 0.0


def _tier_thresholds(ppc_desc, n):
    """Absolute points_per_credit cut-offs at the TIER_SHARES percentile
    boundaries of the global field — used to re-tier sprinters without
    disturbing anyone else."""
    thr, cum = {}, 0.0
    for name, share in TIER_SHARES[:-1]:
        cum += share
        i = max(0, min(int(round(cum * n)) - 1, len(ppc_desc) - 1))
        thr[name] = ppc_desc[i]
    return thr


def _band(ppc, thr):
    return ("Excellent" if ppc > thr["Excellent"] else
            "Great" if ppc > thr["Great"] else
            "Good" if ppc > thr["Good"] else
            "Average" if ppc > thr["Average"] else "Poor")


def assign_value_categories(riders):
    """Assign value_category by GLOBAL percentile on points_per_credit.

    Ranked across the WHOLE field, not per category, because PCS points already
    capture total output across GC, stage wins and one-day races. Sprinters get a
    final tier-only adjustment (see SPRINT_BOOST). Mutates each rider in place;
    unmatched / price<=0 riders are marked 'Unknown' and excluded."""
    ranked = []
    for r in riders:
        if r.get("pcs_match_found") and r.get("price", 0) > 0:
            ranked.append(r)
        else:
            r["value_category"] = "Unknown"

    ranked.sort(key=lambda x: x.get("points_per_credit", 0), reverse=True)
    n = len(ranked)

    # 1) Global percentile tiers for everyone (this fixes all non-sprinter tiers).
    counts, assigned = {}, 0
    for name, share in TIER_SHARES[:-1]:
        counts[name] = round(n * share)
        assigned += counts[name]
    counts["Poor"] = max(0, n - assigned)
    idx = 0
    for name in TIER_ORDER:
        for _ in range(counts.get(name, 0)):
            if idx < n:
                ranked[idx]["value_category"] = name
                idx += 1
    while idx < n:  # rounding leftovers
        ranked[idx]["value_category"] = "Poor"
        idx += 1

    # 2) Sprinter-only override against the same global thresholds, using a boosted
    #    ppc. Touches ONLY sprinter badges — every other rider keeps the tier from
    #    step 1, and no value number is modified anywhere.
    thr = _tier_thresholds([r.get("points_per_credit", 0) for r in ranked], n)
    for r in ranked:
        if r.get("category") == "Sprinters":
            r["value_category"] = _band(r.get("points_per_credit", 0) * SPRINT_BOOST, thr)


def recompute_value(riders):
    """Recompute value_points, points_per_credit and value_category for all
    riders from their stored pcs_points_2025 (YTD) and pcs_points_12m."""
    for r in riders:
        if r.get("pcs_match_found") and r.get("price", 0) > 0:
            vp = compute_value_points(r.get("pcs_points_2025", 0), r.get("pcs_points_12m", 0))
            r["value_points"] = vp
            r["points_per_credit"] = points_per_credit(vp, r["price"])
        else:
            r["value_points"] = 0
            r["points_per_credit"] = 0
    assign_value_categories(riders)

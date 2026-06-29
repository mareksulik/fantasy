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

# Stage-win premium. PCS season points undercount the fantasy value of winning (a
# bunch-sprint or breakaway stage win scores big in the game but adds modest PCS
# points), while the game price already anticipates it. So riders with 2026 wins get
# a win premium folded into BOTH their Value (points_per_credit) and tier, scaled by
# their actual win count — covering sprinters AND breakaway stage-hunters (e.g. Cort)
# on the same honest basis. factor = 1 + WIN_STEP * min(wins, WIN_CAP); 0-win riders
# untouched. Tiers are then banded against thresholds frozen from the pre-premium
# distribution, so non-winners keep their exact tier.
WIN_STEP = 0.05
WIN_CAP = 6  # +5% per win, capped at +30% for 6+ wins (matches the chosen 1.3 lift)


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
    """Set points_per_credit (with the stage-win premium folded in) and value_category.

    value/credit is GLOBAL (ranked across the whole field, not per category, because
    PCS points already capture GC + stage wins + one-day races). The win premium
    (1 + WIN_STEP·min(wins, WIN_CAP)) is multiplied into BOTH the Value number and the
    tier. Tier thresholds are frozen from the PRE-premium distribution at the
    TIER_SHARES percentile cuts, so 0-win riders keep their exact tier and only winners
    move up. Idempotent: raw value/credit is recomputed from value_points each call, so
    the premium never compounds. Mutates in place; unmatched / price<=0 -> 'Unknown'."""
    ranked = []
    for r in riders:
        if r.get("pcs_match_found") and r.get("price", 0) > 0:
            ranked.append(r)
        else:
            r["value_category"] = "Unknown"

    n = len(ranked)

    # Raw (pre-premium) value/credit straight from value_points — canonical, so the
    # premium can't compound across repeated calls.
    for r in ranked:
        r["points_per_credit"] = r.get("value_points", 0) / r["price"]
    thr = _tier_thresholds(sorted((r["points_per_credit"] for r in ranked), reverse=True), n)

    # Fold the win premium into Value, then band against the frozen thresholds.
    for r in ranked:
        wins = r.get("wins_2026", 0) or 0
        if wins > 0:
            r["points_per_credit"] *= 1 + WIN_STEP * min(wins, WIN_CAP)
        r["value_category"] = _band(r["points_per_credit"], thr)


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

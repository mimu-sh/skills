#!/usr/bin/env python3
"""
trendmath.py - phase metrics for trend time series.

Computes the metrics the trend-acceleration-radar skill relies on:

  k   growth rate      slope of ln(value) over a trailing window
  A   acceleration     k_recent / k_prior  -- the leading indicator
  T2  doubling time    ln(2) / k
  R   outlier ratio    latest value / trailing median (audience-normalized)
  B   breadth ratio    distinct sources / total mentions

...and classifies the series into a phase. Standard library only.

INPUT FORMATS
-------------
JSON, either a bare list of points:

    [{"date": "2026-01-01", "value": 12}, ...]

or several named series at once (the useful form -- lets the tool report
the discourse/commitment gap, which is the primary phase signal):

    {
      "discourse":  [{"date": "2026-01-01", "value": 12}, ...],
      "commitment": [{"date": "2026-01-01", "value": 3}, ...]
    }

CSV, with a header, either `date,value` or `date,series,value`.

Series named with any of: commitment, downloads, signups, jobs, forks,
revenue, questions -- are treated as commitment signals. Everything else
is treated as discourse. Override with --commitment.

USAGE
-----
    python3 trendmath.py series.json
    python3 trendmath.py series.csv --window 14 --json
    python3 trendmath.py series.json --breadth breadth.json
    python3 trendmath.py cumulative.json --cumulative     # Fisher-Pry position
    python3 trendmath.py --demo                           # run on synthetic data

Values may be zero; log1p is used so zero-floors don't blow up. Values must
not be negative.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date, datetime, timedelta

# Series whose names imply a real cost was paid by the adopter. These lead
# less but lie less -- see references/signal-sources.md.
COMMITMENT_HINTS = (
    "commitment", "download", "install", "signup", "sign_up", "subscriber",
    "job", "hiring", "fork", "contributor", "revenue", "paid", "purchase",
    "question", "issue", "dependent", "edit",
)

ACCEL_HIGH = 1.3   # above: still accelerating
ACCEL_LOW = 0.8    # below (with k>0): decelerating toward saturation

PHASES = {
    "IGNITION": "just turned positive -- earliest actionable moment, highest false-positive rate",
    "ACCELERATING": "growth rate still rising -- the window",
    "LINEAR": "steady growth, mid-S -- viable but more crowded",
    "DECELERATING": "growth slowing -- approaching saturation, late for tools",
    "DECAY": "shrinking",
    "DORMANT": "flat or negligible",
}


# ---------------------------------------------------------------- loading


def _parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[: len(fmt) + 2], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognized date: {s!r} (want YYYY-MM-DD)")


def _points(raw) -> list[tuple[date, float]]:
    """Normalize a list of points into sorted (date, value) tuples."""
    out = []
    for p in raw:
        if isinstance(p, dict):
            d = p.get("date") or p.get("day") or p.get("timestamp")
            v = p.get("value", p.get("count", p.get("y")))
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            d, v = p[0], p[1]
        else:
            raise ValueError(f"cannot read point: {p!r}")
        if d is None or v is None:
            raise ValueError(f"point missing date or value: {p!r}")
        v = float(v)
        if v < 0:
            raise ValueError(f"negative value at {d}: {v}")
        out.append((_parse_date(str(d)), v))
    out.sort(key=lambda t: t[0])
    return out


def load(path: str) -> dict[str, list[tuple[date, float]]]:
    """Return {series_name: [(date, value), ...]}."""
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            raise ValueError(f"{path} is empty")
        cols = {c.lower(): c for c in rows[0]}
        dcol = cols.get("date") or cols.get("day")
        vcol = cols.get("value") or cols.get("count")
        scol = cols.get("series") or cols.get("name") or cols.get("metric")
        if not dcol or not vcol:
            raise ValueError("CSV needs at least `date` and `value` columns")
        grouped: dict[str, list] = {}
        for r in rows:
            key = r[scol].strip() if scol else "series"
            grouped.setdefault(key, []).append({"date": r[dcol], "value": r[vcol]})
        return {k: _points(v) for k, v in grouped.items()}

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if isinstance(raw, list):
        return {"series": _points(raw)}
    if isinstance(raw, dict):
        return {k: _points(v) for k, v in raw.items()}
    raise ValueError("JSON must be a list of points or an object of named series")


# ------------------------------------------------------------------ math


def _ols_slope(xs: list[float], ys: list[float]) -> float:
    """Least-squares slope. Returns 0.0 when x has no variance."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def growth_rate(pts: list[tuple[date, float]]) -> float:
    """Per-day exponential growth rate k, fitted on log1p(value)."""
    if len(pts) < 2:
        return 0.0
    t0 = pts[0][0]
    xs = [(d - t0).days for d, _ in pts]
    ys = [math.log1p(v) for _, v in pts]
    return _ols_slope(xs, ys)


def _slice_days(pts, end: date, days: int):
    start = end - timedelta(days=days)
    return [(d, v) for d, v in pts if start < d <= end]


def doubling_time(k: float) -> float | None:
    return math.log(2) / k if k > 1e-9 else None


def median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def acceleration(pts, window: int) -> dict:
    """Compare growth in the trailing window against the window before it."""
    if len(pts) < 4:
        return {"error": "need at least 4 points"}
    end = pts[-1][0]
    recent = _slice_days(pts, end, window)
    prior = _slice_days(pts, end - timedelta(days=window), window)
    if len(recent) < 2 or len(prior) < 2:
        span = (pts[-1][0] - pts[0][0]).days
        return {"error": (
            f"need >=2 points in each {window}d window (got {len(recent)} recent, "
            f"{len(prior)} prior across {span}d of history) -- collect more often "
            f"or raise --window")}

    k_recent = growth_rate(recent)
    k_prior = growth_rate(prior)

    if k_recent <= 1e-9 and k_prior <= 1e-9:
        phase, a = ("DECAY" if min(k_recent, k_prior) < -1e-4 else "DORMANT"), None
    elif k_recent <= 1e-9:
        phase, a = "DECAY", None
    elif k_prior <= 1e-9:
        phase, a = "IGNITION", None
    else:
        a = k_recent / k_prior
        phase = "ACCELERATING" if a >= ACCEL_HIGH else "LINEAR" if a >= ACCEL_LOW else "DECELERATING"

    return {
        "k_recent": k_recent,
        "k_prior": k_prior,
        "acceleration_index": a,
        "doubling_days": doubling_time(k_recent),
        "prior_doubling_days": doubling_time(k_prior),
        "phase": phase,
        "phase_note": PHASES[phase],
        "n_recent": len(recent),
        "n_prior": len(prior),
    }


def outlier_ratio(pts, window: int) -> dict:
    """Latest value vs the series' own trailing baseline, excluding the window.

    Dividing by a source's own history is what separates signal about the
    *idea* from signal about the source's audience size.
    """
    if len(pts) < 3:
        return {"error": "need at least 3 points"}
    end = pts[-1][0]
    cutoff = end - timedelta(days=window)
    baseline = [v for d, v in pts if d <= cutoff]
    if len(baseline) < 2:
        baseline = [v for _, v in pts[:-1]]
    base = median(baseline)
    latest = pts[-1][1]
    return {
        "latest": latest,
        "baseline_median": base,
        "outlier_ratio": (latest / base) if base > 0 else None,
        "baseline_n": len(baseline),
    }


def breadth(pts_distinct, pts_total, window: int) -> dict:
    """B = distinct sources / total mentions, and its direction.

    Rising volume with falling breadth is one community amplifying itself.
    It is a negative signal, not a weak positive.
    """
    dmap = dict(pts_distinct)
    tmap = dict(pts_total)
    common = sorted(set(dmap) & set(tmap))
    if len(common) < 4:
        return {"error": "need >=4 overlapping dates in distinct and total series"}
    ratios = [(d, dmap[d] / tmap[d]) for d in common if tmap[d] > 0]
    if len(ratios) < 4:
        return {"error": "total series has too many zeros"}
    end = ratios[-1][0]
    recent = [r for d, r in ratios if d > end - timedelta(days=window)]
    prior = [r for d, r in ratios if end - timedelta(days=2 * window) < d <= end - timedelta(days=window)]
    if not recent or not prior:
        half = len(ratios) // 2
        prior = [r for _, r in ratios[:half]]
        recent = [r for _, r in ratios[half:]]
    mr, mp = sum(recent) / len(recent), sum(prior) / len(prior)
    change = (mr - mp) / mp if mp > 0 else 0.0
    direction = "rising" if change > 0.05 else "falling" if change < -0.05 else "flat"
    return {
        "breadth_now": mr,
        "breadth_prior": mp,
        "change_pct": change * 100,
        "direction": direction,
        "warning": (
            "volume-with-falling-breadth: likely echo chamber or amplification"
            if direction == "falling" else None
        ),
    }


def fisher_pry(pts) -> dict:
    """Estimate percent-of-saturation on a cumulative curve.

    If C(t) approaches ceiling L, then ln(C/(L-C)) is linear in t. Grid-search
    L, keep the best linear fit. Only meaningful for cumulative macro series.
    """
    vals = [v for _, v in pts]
    if len(pts) < 6 or vals[-1] <= 0:
        return {"error": "need >=6 cumulative points with a positive final value"}
    if any(b < a - 1e-9 for a, b in zip(vals, vals[1:])):
        return {"error": "series is not monotonic -- Fisher-Pry needs cumulative data"}

    t0 = pts[0][0]
    xs = [(d - t0).days for d, _ in pts]
    peak = vals[-1]
    best = None
    for i in range(1, 400):
        L = peak * (1.0 + i * 0.05)          # 1.05x .. 20x the current level
        ys, xs_ok = [], []
        for x, c in zip(xs, vals):
            if c <= 0 or c >= L:
                continue
            ys.append(math.log(c / (L - c)))
            xs_ok.append(float(x))
        if len(ys) < 4:
            continue
        slope = _ols_slope(xs_ok, ys)
        if slope <= 0:
            continue
        n = len(ys)
        mx, my = sum(xs_ok) / n, sum(ys) / n
        icept = my - slope * mx
        ss_res = sum((y - (slope * x + icept)) ** 2 for x, y in zip(xs_ok, ys))
        ss_tot = sum((y - my) ** 2 for y in ys)
        if ss_tot <= 0:
            continue
        r2 = 1 - ss_res / ss_tot
        if best is None or r2 > best["r2"]:
            best = {"ceiling": L, "r2": r2, "slope": slope}

    if best is None:
        return {"error": "no usable logistic fit -- curve may still be exponential"}
    pct = 100 * peak / best["ceiling"]
    return {
        "estimated_ceiling": best["ceiling"],
        "percent_of_saturation": pct,
        "fit_r2": best["r2"],
        "takeoff_years_to_90pct": (math.log(9) - math.log(pct / (100 - pct))) / best["slope"] / 365.0
        if 0 < pct < 100 else None,
        "caveat": "ceiling is extrapolated; treat as an order of magnitude, not a forecast",
    }


# --------------------------------------------------------------- reporting


def is_commitment(name: str, overrides: list[str]) -> bool:
    n = name.lower()
    if overrides:
        return any(o.lower() in n for o in overrides)
    return any(h in n for h in COMMITMENT_HINTS)


def gap_reading(disc: str | None, comm: str | None) -> str:
    """The discourse/commitment gap IS the phase estimate."""
    up = {"IGNITION", "ACCELERATING", "LINEAR"}
    if disc is None or comm is None:
        return "Only one side measured -- phase estimate is unverified. Add the other series."
    d_up, c_up = disc in up, comm in up
    if d_up and not c_up:
        return ("HYPE ONLY -- discourse moving, commitment flat. Sell attention "
                "(explainers, curation, list-building). Do NOT build paid tooling yet.")
    if d_up and c_up:
        return "THE WINDOW -- both curves live. Attention and tooling plays are both viable."
    if c_up and not d_up:
        return ("QUIET ADOPTION -- commitment rising without noise. Least crowded, best "
                "unit economics. Build tools.")
    return "OVER -- both curves flat or falling. Harvest the asset; don't start here."


def fmt(v, nd=3, suffix=""):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{nd}f}{suffix}"
    return f"{v}{suffix}"


def report(results: dict) -> str:
    L = []
    for name, r in results["series"].items():
        kind = "commitment" if r["is_commitment"] else "discourse"
        a = r["acceleration"]
        L.append(f"\n=== {name}  [{kind}] ===")
        L.append(f"  span            {r['span_days']}d, {r['n']} points, "
                 f"latest {fmt(r['latest'], 1)} on {r['last_date']}")
        if "error" in a:
            L.append(f"  acceleration    -- {a['error']}")
        else:
            L.append(f"  phase           {a['phase']}  ({a['phase_note']})")
            L.append(f"  A               {fmt(a['acceleration_index'], 2)}"
                     f"   (k_recent {fmt(a['k_recent'], 4)} / k_prior {fmt(a['k_prior'], 4)} per day)")
            dt = a["doubling_days"]
            pdt = a["prior_doubling_days"]
            trend = ""
            if dt and pdt and abs(dt - pdt) / pdt > 0.05:
                # below 5% the two fits are indistinguishable; labelling it
                # either way invents a trend that isn't in the data
                trend = "  <- shrinking (accelerating)" if dt < pdt else "  <- lengthening (saturating)"
            L.append(f"  doubling time   {fmt(dt, 1, 'd')}   (was {fmt(pdt, 1, 'd')}){trend}")
        o = r["outlier"]
        if "error" not in o:
            L.append(f"  outlier ratio   {fmt(o['outlier_ratio'], 2, 'x')}   "
                     f"(latest vs trailing median {fmt(o['baseline_median'], 1)})")
        if r.get("fisher_pry"):
            fp = r["fisher_pry"]
            if "error" in fp:
                L.append(f"  saturation      -- {fp['error']}")
            else:
                L.append(f"  saturation      {fp['percent_of_saturation']:.1f}% of estimated "
                         f"ceiling {fp['estimated_ceiling']:.0f} (fit R2 {fp['fit_r2']:.2f})")

    if results.get("breadth"):
        b = results["breadth"]
        L.append("\n=== breadth ===")
        if "error" in b:
            L.append(f"  -- {b['error']}")
        else:
            L.append(f"  B               {b['breadth_now']:.3f} ({b['direction']}, "
                     f"{b['change_pct']:+.1f}% vs prior window)")
            if b["warning"]:
                L.append(f"  WARNING         {b['warning']}")

    L.append("\n=== reading ===")
    L.append(f"  {results['gap_reading']}")
    if results.get("quadrant"):
        L.append(f"  quadrant: {results['quadrant']}")
    L.append("\n  Next: rule out false positives (filter bubble, coordinated launch, bots,")
    L.append("  seasonality, news spike, rebranding) before acting. See SKILL.md step 3.")
    return "\n".join(L)


def quadrant(phase: str | None, direction: str | None) -> str | None:
    """Cross acceleration against breadth -- see the quadrant table in SKILL.md."""
    if not phase or not direction:
        return None
    if phase in ("DECAY", "DORMANT"):
        return "DEAD -- ignore"
    accel = phase in ("ACCELERATING", "IGNITION")
    growing = accel or phase == "LINEAR"
    if direction == "falling":
        # spreading volume without spreading people: contained, whatever the slope
        return ("ECHO CHAMBER -- watch, don't build" if growing
                else "SPIKE & DECAY -- ignore")
    if accel:
        return ("TRUE ACCELERATION -- act" if direction == "rising"
                else "accelerating, breadth flat -- verify it can escape its community")
    if phase == "LINEAR":
        return ("mid-S with breadth rising -- viable, expect competition"
                if direction == "rising" else "mid-S, breadth flat -- unremarkable")
    return "MATURING -- late for generic tools, good for vertical/depth plays"


# ------------------------------------------------------------------- main


def analyze(series: dict, window: int, commitment_overrides: list[str],
            breadth_path: str | None, cumulative: bool) -> dict:
    out = {"series": {}, "window_days": window}
    disc_phase = comm_phase = None

    for name, pts in series.items():
        if len(pts) < 2:
            out["series"][name] = {"error": "need at least 2 points", "n": len(pts)}
            continue
        comm = is_commitment(name, commitment_overrides)
        a = acceleration(pts, window)
        entry = {
            "is_commitment": comm,
            "n": len(pts),
            "span_days": (pts[-1][0] - pts[0][0]).days,
            "last_date": pts[-1][0].isoformat(),
            "latest": pts[-1][1],
            "acceleration": a,
            "outlier": outlier_ratio(pts, window),
        }
        if cumulative:
            entry["fisher_pry"] = fisher_pry(pts)
        out["series"][name] = entry
        ph = a.get("phase")
        if comm and comm_phase is None:
            comm_phase = ph
        elif not comm and disc_phase is None:
            disc_phase = ph

    if breadth_path:
        b = load(breadth_path)
        keys = list(b)
        dk = next((k for k in keys if "distinct" in k.lower() or "source" in k.lower() or "author" in k.lower()), keys[0])
        tk = next((k for k in keys if k != dk), None)
        out["breadth"] = (breadth(b[dk], b[tk], window) if tk
                          else {"error": "breadth file needs two series: distinct and total"})

    out["gap_reading"] = gap_reading(disc_phase, comm_phase)
    bd = (out.get("breadth") or {}).get("direction")
    out["quadrant"] = quadrant(disc_phase or comm_phase, bd)
    return out


def _demo() -> dict:
    """Synthetic accelerating discourse + lagging commitment, for a smoke test."""
    start = date(2026, 1, 1)
    disc, comm = [], []
    for i in range(120):
        d = start + timedelta(days=i)
        # discourse: slow, then accelerating from day 60
        v = 5 * math.exp(0.010 * i) + (0 if i < 60 else 3 * math.exp(0.075 * (i - 60)))
        disc.append({"date": d.isoformat(), "value": round(v, 1)})
        # commitment: same shape, ~30 days behind and much smaller
        j = max(0, i - 30)
        c = 1 * math.exp(0.008 * j) + (0 if j < 60 else 0.4 * math.exp(0.070 * (j - 60)))
        comm.append({"date": d.isoformat(), "value": round(c, 2)})
    return {"mentions": _points(disc), "downloads": _points(comm)}


def main() -> int:
    p = argparse.ArgumentParser(
        description="Phase metrics for trend time series (acceleration, doubling time, outlier & breadth ratios).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("INPUT FORMATS")[1] if "INPUT FORMATS" in __doc__ else None,
    )
    p.add_argument("path", nargs="?", help="JSON or CSV series file")
    p.add_argument("--window", type=int, default=14,
                   help="days per comparison window; needs ~2x this much data (default 14)")
    p.add_argument("--breadth", help="JSON/CSV with two series: distinct sources and total mentions")
    p.add_argument("--commitment", action="append", default=[],
                   help="substring marking a series as a commitment signal (repeatable)")
    p.add_argument("--cumulative", action="store_true",
                   help="treat input as cumulative and estimate percent-of-saturation (Fisher-Pry)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    p.add_argument("--demo", action="store_true", help="run on synthetic data")
    args = p.parse_args()

    if not args.path and not args.demo:
        p.error("provide a series file, or --demo")

    try:
        series = _demo() if args.demo else load(args.path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    results = analyze(series, args.window, args.commitment, args.breadth, args.cumulative)
    print(json.dumps(results, indent=2, default=str) if args.json else report(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())

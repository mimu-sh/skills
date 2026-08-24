# skills

Agent skills from [mimu-sh](https://github.com/mimu-sh). Works with Claude Code, Cursor, and any agent that reads `SKILL.md` skills.

```bash
npx skills add mimu-sh/skills
```

| Skill | What it does |
|---|---|
| [`trend-acceleration-radar`](skills/trend-acceleration-radar) | Find trends in the acceleration phase — past emergence, before saturation — and pick the monetization play that fits where the trend actually is |

---

## trend-acceleration-radar

Anyone can see what is popular. Popularity is the *level* of a curve, and by the time the level is high the money is gone. The exploitable window is the stretch where the growth rate is itself still increasing, adoption is visible enough to verify but not yet served by tooling, and the crowd arriving behind you is large enough to pay for what you built.

```bash
npx skills add mimu-sh/skills@trend-acceleration-radar
```

Or try it without installing:

```bash
npx skills use mimu-sh/skills@trend-acceleration-radar
```

### What it actually does

**1. Separates the two curves everyone collapses into one.**

Most trend analysis fails because it treats "people are talking about X" and "people are paying for X" as the same signal. They are different curves, offset by 12–24 months — Gartner's peak of inflated expectations *precedes* the S-curve adoption inflection. The skill tracks a **discourse** series and a **commitment** series separately, and reads the gap:

| Discourse | Commitment | Reading |
|---|---|---|
| Accelerating | Flat | Hype only. Sell attention, don't build tools. |
| Accelerating | Accelerating | **The window.** Both plays live. |
| Flat/declining | Accelerating | Quiet adoption — least crowded, best economics. |
| Declining | Declining | Over. Harvest or leave. |

**2. Measures acceleration, not volume.** Level lags, velocity is coincident, the second derivative leads. Bundled calculator computes:

- **A** — acceleration index, `k_recent / k_prior` where k is the log-linear growth rate
- **T2** — doubling time; its *direction* is the phase (shrinking = accelerating, lengthening = saturating)
- **R** — outlier ratio, value ÷ that source's own trailing median, which isolates the *idea* from the *audience*
- **B** — breadth ratio, distinct sources ÷ total mentions — the best false-positive filter there is
- **Fisher–Pry** percent-of-saturation for cumulative macro series

**3. Filters false positives.** Filter bubble, coordinated launch, bots, seasonality, news spikes, rebranding, single-source dependence. The filter-bubble check matters most for individuals: a personalized feed manufactures the *sensation* of a trend, and it is indistinguishable from real pattern recognition from the inside.

**4. Matches the play to the phase.** At each phase a different thing is scarce, and you get paid for supplying the scarce thing.

| Phase | Scarce | Play | Build budget |
|---|---|---|---|
| Ignition | Awareness | Stake the name — domain, handle, `awesome-X` | Hours |
| Early acceleration | **Clarity** | Explainers, curation, free tool as lead magnet | Days |
| Mid acceleration | **Time/effort** | Micro-SaaS, templates, done-for-you | 1–3 weeks |
| Late / chasm | **Trust** | Vertical specialization, case studies, services | Weeks |
| Saturation | **Differentiation** | Sell to the sellers, or exit | Don't start |

### Quick start

```bash
# smoke test on synthetic data
python3 skills/trend-acceleration-radar/scripts/trendmath.py --demo

# your own series
python3 .../trendmath.py series.json --breadth breadth.json --window 14
```

Input is JSON or CSV. The useful form gives several named series at once so the tool can report the discourse/commitment gap:

```json
{
  "mentions":  [{"date": "2026-01-01", "value": 12}, ...],
  "downloads": [{"date": "2026-01-01", "value": 3}, ...]
}
```

Series named `downloads`, `signups`, `jobs`, `forks`, `revenue`, `questions` (etc.) are auto-classified as commitment signals. Stdlib only — no dependencies.

Sample output:

```
=== downloads  [commitment] ===
  phase           ACCELERATING  (growth rate still rising -- the window)
  A               1.64   (k_recent 0.0310 / k_prior 0.0189 per day)
  doubling time   22.4d   (was 36.7d)  <- shrinking (accelerating)
  outlier ratio   4.25x   (latest vs trailing median 1.2)

=== reading ===
  THE WINDOW -- both curves live. Attention and tooling plays are both viable.
```

### Contents

```
skills/trend-acceleration-radar/
├── SKILL.md                      6-step workflow, phase quadrant, output template
├── references/
│   ├── signal-sources.md         endpoint cookbook — backfillable vs forward-only
│   ├── psychology.md             why acceleration happens + self-deception modes
│   └── monetization.md           play catalog, build-budget math, kill criteria
└── scripts/trendmath.py          A, T2, outlier & breadth ratios, Fisher–Pry
```

#### On signal sources

The cookbook prioritizes **backfillable** sources — Wikipedia pageviews, the Hacker News Algolia API, npm/PyPI download stats — because you cannot reconstruct a second derivative from a snapshot. These let you compute acceleration today instead of starting a log and waiting a month. Most of them are free and need no API key.

#### On the psychology

Four mechanisms with operational consequences, not trivia:

- **Threshold crossing** — acceleration is a property of the network, not the idea, which is why breadth is the observable proxy and why "this failed before" is weak evidence.
- **The status clock** — early adopters are paid in perishable positional currency, so *peak evangelism precedes peak adoption*. Loud enthusiasm is a buy signal; early adopters going quiet is the sell signal.
- **The pragmatist gate** — the early majority buys on peer references, producing a directly observable content shift from "X is amazing" to "how we did X at [ordinary company]". That shift is when tool demand becomes real.
- **Triggers predict duration; velocity doesn't** — something with no everyday cue dies fast regardless of how steep the climb was.

### Design notes

The skill is deliberately calibration-first. A plausible narrative about why something is about to blow up is easy to generate for any topic and is worth nothing, so the instructions require reporting which metrics were actually computed, distinguishing measurement from interpretation, and stating low confidence when that's the honest answer. Talking someone out of a bad bet is treated as the highest-value output.

Thresholds (A ≥ 1.3, R ≥ 10, etc.) are stated as explicit, revisable assumptions. The weak-signals literature is candid that no universal validated rubric exists and human judgment stays in the loop — so the skill leans on cross-platform replication, which *is* well supported, rather than faking precision.

### References

Built from published work rather than vibes. Principal sources:

- Rogers, *Diffusion of Innovations* — S-curve, takeoff at the first inflection of the non-cumulative curve
- Moore, *Crossing the Chasm* — pragmatist psychology and the reference catch-22
- Berger, *Contagious* — STEPPS; triggers as the duration predictor
- Granovetter threshold models — why acceleration is a network property
- [Gartner hype cycle methodology](https://www.gartner.com/en/research/methodologies/gartner-hype-cycle) and [when hype cycles meet S-curves](https://www.b2venture.vc/stories/when-hype-cycles-meet-s-curves-the-roll-out-conundrum-of-generative-ai) — the offset between the two curves
- [Infectivity enhances prediction of viral cascades](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0214453) — onset is predictable, size is not
- [Launch-day diffusion: Hacker News impact on GitHub stars](https://arxiv.org/html/2511.04453v1) — quantified shock effect on star series
- [Detecting trends before they break](https://smarterarticles.co.uk/detecting-trends-before-they-break-how-weak-signals-become-strong-evidence) — cross-source fusion, and the absence of a universal rubric

## License

MIT

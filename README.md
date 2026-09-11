# skills

Agent skills from [mimu-sh](https://github.com/mimu-sh). Works with Claude Code, Cursor, and any agent that reads `SKILL.md` skills.

```bash
npx skills add mimu-sh/skills
```

| Skill | What it does |
|---|---|
| [`trend-acceleration-radar`](skills/trend-acceleration-radar) | Find trends in the acceleration phase — past emergence, before saturation — and pick the monetization play that fits where the trend actually is |
| [`domain-price-check`](skills/domain-price-check) | Check what a domain really costs before you recommend or buy it — premium tier, renewal price, and launch-phase pricing for any TLD |

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

---

## domain-price-check

The advertised price of a TLD applies to the names nobody wants. Registries quietly carve the good phrases into **premium tiers** with a permanently higher annual fee, and an availability check that only answers "taken / not taken" hides this completely.

In `.here` the standard rate is €20.17/yr. `sign.here` renews at **€1,385.33/yr** — 69x, forever — while `signhere.here` sits at the standard rate. Same registry, one word apart. A shortlist priced from the TLD's advertised rate is a shortlist of names whose real cost nobody checked.

```bash
npx skills add mimu-sh/skills@domain-price-check
```

Or try it without installing:

```bash
npx skills use mimu-sh/skills@domain-price-check
```

### What it actually does

**1. Prices the exact name, not the extension.** Registry premium tiers are per-name, set by the registry rather than the registrar, and they survive transfer — so shopping around finds a few percent, never a way out of the tier. The only reliable signal is a live lookup on that specific string. Tiering targets bare, high-frequency words, so the compound form usually escapes what the bare noun falls into: `sign` premium, `signhere` standard; `menu.eat` €1,385/yr, `ourmenu.eat` €20.17. When a shortlist comes back expensive, re-run it with compounded variants before abandoning the concept.

**2. Ranks on renewal, because the first year is marketing.** Results sort by the number that compounds:

| TLD | First year | Renewal |
|---|---|---|
| `.com` | €11.00 | €31.98 |
| `.app` | €8.99 | €40.00 |

A list ordered by first-year price is ordered by promotion depth.

**3. Reconstructs launch calendars for TLDs that have not launched yet.** `--tld-info` returns every phase, its price and its exact start timestamp, pulled from live registry data — the calendar is otherwise published only as prose in registrar blog posts, and ICANN's own startup export covers just the 2012 round. It also flags **flat rungs**: `.here` prices `eap6` and `eap7` identically at €132.17, so buying on the last day of a rung costs the same as the first and buys a day less exclusivity. Early Access is a descending Dutch auction, not a discount — each day is a one-off surcharge that buys a smaller field, not a guarantee.

**4. Says "unknown" rather than guessing.** Roughly 300 TLDs — `.io` among them — have no RDAP service at all, and a generic RDAP proxy returns 404 both for "unregistered" and "no server for this TLD". Reading those alike reports registered domains as available: `google.io` comes back 404. The script resolves the authoritative server from IANA's bootstrap registry and reports `unknown` when a TLD has none.

### Quick start

```bash
export GANDI_API_KEY=...        # free Personal Access Token, no purchase needed

# price a shortlist, cheapest renewal first
python3 scripts/check_domains.py --names signhere,sign,almost --tlds here

# sweep a file of candidates, hide anything registry-premium
python3 scripts/check_domains.py --names-file names.txt --tlds com,io,dev --standard-only

# launch calendar + Early Access fee ladder
python3 scripts/check_domains.py --tld-info here
```

```
DOMAIN         STATUS      TIER       1ST YR EUR   RENEWAL EUR
signhere.here  available   standard   20.17        20.17
almost.here    available   premium    464.01       189.59
sign.here      available   premium    1,099.12     1,385.33
```

### Contents

```
skills/domain-price-check/
├── SKILL.md                      workflow, how to read tiers and ladders
├── references/
│   ├── providers.md              registrar API comparison + the parsing trap
│   └── launch-phases.md          sunrise/EAP/GA mechanics, EAP economics
├── scripts/check_domains.py      availability, tier, renewal, phase ladder
└── scripts/test_check_domains.py contract tests pinning the parser to real payloads
```

```bash
python3 -m unittest discover -s skills/domain-price-check/scripts -p 'test_*.py'
```

#### On the data source

Gandi's documented `/v5/domain/check` is the only supported API that both carries TLDs **before** General Availability and returns the per-phase price ladder. Spaceship, Dynadot, Porkbun and Namecheap all return premium pricing but list a TLD only once it goes live — which excludes exactly the launches worth researching. Domainr/Fastly has the best availability coverage of any provider and returns no prices at all, so it complements rather than replaces.

### Design notes

The skill refuses to guess. Availability without a resolvable RDAP service reports `unknown`, a rejected API key warns loudly instead of degrading into silent blanks, and a taken domain shows no tier rather than an inherited default — because in this domain a confident wrong number costs real money on a recurring basis.

One trap is worth naming for anyone reading the registry response directly: in `products[process=create]`, the `prices[]` and `periods[]` arrays look parallel and are not. Prices come back in arbitrary order, each tagged under `options.phase`. Zipping by index scrambles the entire Early Access ladder while looking plausible, because `golive` tends to land last in both — which is precisely how the bug survives an eyeball check.

### References

- [Gandi API documentation](https://api.gandi.net/docs/domains/) — `/v5/domain/check`, premium and per-phase pricing
- [IANA RDAP bootstrap registry](https://data.iana.org/rdap/dns.json) — authoritative RDAP server per TLD
- [ICANN TLD startup information](https://newgtlds.icann.org/en/program-status/sunrise-claims-periods) — sunrise and claims periods, 2012 round only
- [Chromium HSTS preload list](https://source.chromium.org/chromium/chromium/src/+/main:net/http/transport_security_state_static.json) — which TLDs browsers force to HTTPS; registrar marketing is not a reliable guide
- [CSC weekly launch guide](https://www.cscdbs.com/blog/) — upcoming gTLD launches, published as prose

## License

MIT

---
name: trend-acceleration-radar
description: Find trends that are in the acceleration phase — past emergence, before saturation — and pick the monetization play that fits where the trend actually is. Use this whenever the user asks how to spot trends early, find what's about to blow up, catch a wave, identify emerging niches, time a product launch to a trend, evaluate whether a hyped topic is worth building for, or turn attention into revenue. Also use it when the user names a specific topic and asks "is it too late for X?", "is X still growing?", "should I build for X?", or wants a trend radar, trend dashboard, or early-signal monitoring system. Prefer this over generic market-research or social-media skills whenever timing relative to an adoption curve is part of the question.
---

# Trend Acceleration Radar

Anyone can see what is popular. Popularity is the *level* of a curve, and by the time the level is high the money is gone. The exploitable window is the **acceleration phase**: the stretch where the growth rate is itself still increasing, adoption is visible enough to verify but not yet served by tooling, and the crowd arriving behind you is large enough to pay for what you built.

This skill does two things: it measures where a trend sits on its curve using signals that lead rather than lag, and it maps that position to a monetization play the user can actually execute.

## The one distinction that matters most

Most trend analysis fails because it collapses two different curves into one.

**Discourse** — mentions, searches, views, posts, stars, press. Cheap to produce, cheap to fake, peaks early. Gartner's "peak of inflated expectations" lives here, and it *precedes* real adoption by a year or more.

**Commitment** — actions with a cost attached: paid signups, job postings, package downloads, forks, "how do I fix X" support questions, integrations, conference talks by practitioners rather than vendors.

Discourse acceleration and commitment acceleration are monetized by completely different products. Discourse acceleration sells attention: explainers, curation, courses, media. Commitment acceleration sells tools: software, templates, services. Building a tool during a discourse-only spike is the single most expensive mistake in this domain — it is how most AI-wrapper startups died.

**Always track at least one series from each column, and report the gap.** The gap *is* the phase estimate:

| Discourse | Commitment | Reading |
|---|---|---|
| Accelerating | Flat | Hype only. Sell attention, do not build tools. |
| Accelerating | Accelerating | **The window.** Both plays are live. |
| Flat/declining | Accelerating | Quiet adoption — often the best and least crowded. Build tools. |
| Declining | Declining | Over. Harvest or leave. |

Quiet adoption (row 3) is worth hunting deliberately. It has no competition precisely because it produces no excitement.

## Step 1: Pick the timescale before anything else

Trends run on wildly different clocks, and the clock dictates what can possibly be monetized. Matching your build time to the trend's clock is the main practical constraint — a six-week build aimed at a five-day trend loses by definition.

| Tier | Duration | Examples | Poll rate | What can be monetized |
|---|---|---|---|---|
| **Micro** | 24h–1 week | Sounds, memes, formats, news cycles | Hourly, automated | Content, and inventory you already hold |
| **Meso** | 2–12 weeks | Tool categories, aesthetics, workflows, product niches | Daily | Digital products, micro-SaaS, lead magnets — **the solo-builder sweet spot** |
| **Macro** | 6–36 months | Behavior shifts, platform shifts, regulation | Weekly | Durable assets: brand, list, SEO surface, real company |

Micro trends now move faster than they used to; short-form formats that took weeks to peak a few years ago can peak in roughly 72 hours and be dead within the week. A human refreshing a feed cannot win at micro. Either automate it or ignore that tier.

Ask the user which tier they're playing on, or infer it from their build capacity. Then only look at signals that resolve on that clock.

## Step 2: Measure acceleration, not volume

Three quantities, in increasing order of usefulness:

- **Level** — how big it is. Lagging. Ignore it except as a sanity floor.
- **Velocity** — first derivative. Coincident. Tells you it's happening, not that it will continue.
- **Acceleration** — second derivative. Leading. This is the signal.

Run the bundled calculator rather than eyeballing charts:

```bash
python3 scripts/trendmath.py --help
python3 scripts/trendmath.py series.json --breadth breadth.json
```

It reports the metrics below. Read `scripts/trendmath.py` for input formats.

### Acceleration index (A)

Fit an exponential to the most recent window and to the window before it, then compare the growth rates:

```
k = slope of ln(value) over a window
A = k_recent / k_prior
```

| A | Meaning |
|---|---|
| `k_prior ≤ 0 < k_recent` | **Ignition** — just turned over. Earliest actionable moment, highest false-positive rate. |
| A ≥ 1.3 | **Accelerating** — the window. |
| 0.8 – 1.3 | Linear growth — mid-S, still fine, more competition. |
| < 0.8, k > 0 | Decelerating — approaching saturation. Late for tools, fine for depth plays. |
| k ≤ 0 | Decay. |

A is the discriminator almost nobody computes, because it requires keeping history. Start logging series before you need them; you cannot reconstruct acceleration from a single snapshot, and that constraint is why this is defensible.

**Guard A with peak-proximity, or it will hand you dead-cat bounces.** A is a ratio, so it explodes when `k_prior` is near zero — which is exactly what happens to something that collapsed and then twitched upward. In one 101-candidate screen the top four hits by A were all at 26–49% of their own historical peak; the genuine risers ranked below them. Require the series to still be near its own high, because a real riser is at its peak more or less by construction:

```
peak_fraction = latest / max(series)      # demand >= ~0.75
```

Then rank on `k_recent` itself rather than on A, and read A as the secondary confirmation that the rate is still increasing. Ratio for classification, rate for ranking.

### Doubling time (T2)

`T2 = ln(2) / k`. More intuitive than a slope, and the trajectory of T2 is the phase: **shrinking T2 = accelerating, lengthening T2 = saturating**. Also a build-budget check — if T2 is 4 days, anything taking longer than about two doublings to ship will land into a different market than the one you measured.

### Outlier ratio (R)

```
R = observation / that_source's_own_trailing_median
```

The highest-signal-per-unit-effort metric in the whole discipline. Dividing by the source's own baseline removes audience size, which isolates *the idea* from *the distribution*. A 2K-average channel hitting 400K views (R = 200) is a far stronger signal about the idea than a 5M-subscriber channel hitting 1M (R = 0.2, actually a flop). Apply the same trick to subreddit post scores, repo stars, and newsletter open rates.

Rule of thumb: R ≥ 10 is worth a look, R ≥ 25 with rising breadth is worth acting on.

### Breadth ratio (B)

```
B = distinct sources (authors, subreddits, domains, orgs) / total mentions
```

The best false-positive filter that exists. Real diffusion recruits *new* people, so B holds or rises as volume grows. A volume spike with falling B is one community talking to itself, an amplification campaign, or bots — it will not escape its container.

**Rising volume with falling breadth is the classic trap.** Treat it as a negative signal, not a weak positive.

### Phase quadrant

|  | Breadth rising | Breadth flat/falling |
|---|---|---|
| **A ≥ 1.3** | **True acceleration** — act | **Echo chamber** — watch, don't build |
| **A < 0.8** | **Maturing** — late for tools, good for depth/vertical plays | **Spike & decay** — ignore |

### Fisher–Pry position (optional, macro tier)

For macro trends with a plausible ceiling, linearize the cumulative curve: if `C(t)` approaches ceiling `L`, then `ln(C / (L − C))` is linear in time. Grid-search `L`, take the best fit, and report percent-of-saturation. Useful for "is it too late?" on multi-year technology shifts. The script does this when given cumulative data.

## Step 3: Filter false positives

Run every candidate through this before spending anything. Most candidates die here, which is the point.

1. **Your own filter bubble.** By far the most common failure for individuals. You saw it three times today because a recommender learned you clicked it once. *A personalized feed manufactures the sensation of a trend.* Never confirm from a logged-in feed — verify with an API, a logged-out session, or a cold account. If you cannot reproduce the signal without your account, it isn't real.
2. **Coordinated launch.** Genuine diffusion has *lag structure* — it appears on one platform, then another, then another. Simultaneous appearance everywhere means a press push or ad spend, and the curve will collapse when the budget does.
3. **Bot / engagement farming.** Falling breadth, young accounts, engagement ratios far off the platform norm, comment text with low lexical diversity.
4. **Seasonality.** Compare to the same window in prior years before calling anything a breakout. Google Trends "Breakout" means roughly +5000%, which a low base produces trivially.
5. **News-event spike.** Sharp rise, no movement in any commitment series, decay within days. Real trends move commitment signals.
6. **Rebranding.** Check whether the underlying commitment series was already growing under a previous name. If so you're late, not early — you just met the new vocabulary.
7. **Single-source dependence.** Require confirmation on at least two independent platforms with sensible lag between them. Weak signals only become evidence through replication across sources that don't share a population.

There's no universal threshold that separates signal from noise — published work in this area is candid that scoring rubrics are domain-specific and human judgment stays in the loop. So state thresholds as explicit, revisable assumptions rather than pretending to precision.

## Step 4: Where signals actually come from

Full endpoint cookbook, with free no-key sources and copy-pasteable queries: **`references/signal-sources.md`**. Read it whenever building collection.

Highest value per unit effort, in order:

1. **Wikipedia pageviews API** — free, no key, daily granularity, years of history, and crucially *not personalized*. The cleanest general-interest series available, and it can be backfilled instantly.
2. **Hacker News Algolia API** — free, no key, full historical search. You can construct a multi-year mention series in one afternoon.
3. **npm / PyPI download stats** — free, no key. The single best *commitment* signal for anything developer-facing. Stars are discourse; downloads are commitment.
4. **Reddit JSON endpoints** — subscriber counts and post velocity per subreddit. Subreddit *growth rate* beats subreddit size.
5. **Job postings count over time** — the slowest and most trustworthy commitment signal. Companies pay real money.
6. **GitHub star timestamps** — velocity is derivable; use forks and contributor counts as the commitment counterpart.
7. **YouTube Data API** — compute outlier ratio as video views ÷ channel median.

Backfill matters more than it seems. Sources with history (Wikipedia, HN, npm, PyPI) let you compute acceleration *today*. Sources without it (most social APIs) require you to start logging and wait. Begin with the backfillable ones.

## Step 5: Match the play to the phase

Detail, economics, and kill criteria: **`references/monetization.md`**. Read it before recommending any specific play.

The governing logic: **at each phase a different thing is scarce, and you get paid for supplying the scarce thing.**

| Phase | What's scarce | Play | Build budget |
|---|---|---|---|
| Ignition | Awareness | Stake the name — domain, handle, `awesome-X` repo, newsletter #1. Near-free options. | Hours |
| Early acceleration | **Clarity** | Explainer content, curation, a free tool as a lead magnet. Capture emails. | Days |
| Mid acceleration | **Time and effort** | Paid tool, templates, done-for-you service. Picks and shovels. | 1–3 weeks |
| Late / chasm | **Trust and proof** | Vertical specialization, case studies, integrations, services | Weeks |
| Saturation | **Differentiation** | Sell to the sellers, consolidate, or exit | Don't start new builds |
| Decay | — | Harvest the asset | — |

Two rules that survive every specific case:

**Sell to the participants, not in the trend.** Whoever supplies the people chasing a trend has a larger, more reliable, and less fashionable market than the trend itself.

**Every bet must leave an asset behind.** Trends decay; audiences, domains, ranked content, mailing lists, and reusable code do not. A trend play that ends with cash and nothing else puts you back at zero for the next one. Judge each play by what remains after the trend dies.

## Step 6: Size the bet

Trend bets have venture-style return distributions — most are worthless, a few pay for everything. Act accordingly:

- Run 5–10 small bets rather than one large one.
- Cap effort at what the timescale supports (see Step 1). Micro: hours. Meso: days to weeks. Macro: months.
- **Write the kill criterion before starting** — a specific metric and date, e.g. "if A drops below 0.8 or I have under 50 signups by day 21, I stop." Sunk-cost pressure is strongest exactly when a trend is loudest.
- Reserve the majority of capacity for follow-on investment into whichever bet works. The winner deserves more than the portfolio did.

## The psychology

Read **`references/psychology.md`** when the user asks *why* trends accelerate, when designing messaging, or when estimating how long a trend will last. Short version of what's load-bearing:

- Acceleration is a **threshold-crossing** phenomenon, not a property of the idea. Each person has a private threshold for how many others they must see adopting before they adopt. Acceleration begins when the adopting population gets dense enough to trip the modal threshold — which is why the same idea can fail and then later succeed unchanged.
- Once a cascade starts, people evaluate **the crowd instead of the thing**. Quality briefly stops predicting spread. This makes onset somewhat predictable and peak size nearly unpredictable — so bet on being early, never on how big it gets.
- **Status is the engine and the timer.** Early adopters earn social currency from knowing first. That currency decays as adoption spreads, so they evangelize hardest at the *start* of acceleration and abandon at saturation, when being visibly into it starts signaling lateness instead. Peak evangelism precedes the peak; it does not mark it.
- **The pragmatist gate**: the early majority wants evolution, not revolution, and buys only on references from people like themselves — a genuine catch-22 at the chasm. This produces a directly observable signal: content shifts from "X is amazing" to "how we did X at [ordinary company]". That shift is the chasm being crossed, and it's the moment tool demand becomes real.
- **Duration is predicted by trigger frequency**, not by peak intensity. Things with no everyday cue to remind people of them die fast no matter how steep the climb. Score candidates on the transmission properties from Berger's STEPPS — social currency, triggers, emotion, public visibility, practical value, story — to forecast staying power separately from speed.
- For monetization framing: during acceleration people pay to **keep up** far more than to get ahead. Loss framing beats gain framing. And the scarce good during acceleration is clarity — everyone can find the thing; almost nobody knows what to do about it.

## Output format

When analyzing a specific trend, use this structure. It keeps the reasoning auditable and forces the assumptions into the open.

```markdown
## [Trend name] — [PHASE] (confidence: low/med/high)

**Timescale tier:** micro / meso / macro
**Discourse:** [series, A = x.xx, T2 = N days, direction]
**Commitment:** [series, A = x.xx, T2 = N days, direction]
**Breadth:** [rising / flat / falling] — [what that implies]
**Quadrant:** [true acceleration / echo chamber / maturing / spike-decay]

### False positives ruled out
- [each check, with the evidence that cleared it — or flag it as unchecked]

### Window estimate
[How long the current phase likely lasts, and what would end it.]

### Recommended play
[One primary play matched to phase, with build budget and the asset it leaves behind.]

### Kill criteria
[Specific metric + date.]
```

When scanning for *unknown* trends rather than evaluating a named one, produce a ranked shortlist with A, R, and B for each, then apply this template only to the top few. Screening should be cheap; analysis should be expensive.

## Honesty constraints

This domain rewards calibration and punishes confident storytelling — a plausible narrative about why something is about to blow up is easy to generate and worthless.

- Report the metrics that were actually computed. If a series couldn't be collected, say the phase estimate is unverified rather than inferring it from vibes.
- Distinguish measured signal from interpretation.
- Give confidence levels, and let them be low. Most candidates deserve "low."
- If the honest answer is "this is already saturated" or "this is hype with no commitment behind it," say so plainly. Talking someone out of a bad bet is the highest-value output this skill produces.

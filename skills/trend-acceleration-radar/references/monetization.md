# Monetizing by Phase

How to convert a phase estimate into a specific play, with build budgets, economics, and exit rules.

## Contents
- [The two governing rules](#the-two-governing-rules)
- [Play catalog by phase](#play-catalog-by-phase)
- [Choosing between plays](#choosing-between-plays)
- [Build budget math](#build-budget-math)
- [Portfolio construction](#portfolio-construction)
- [Kill criteria](#kill-criteria)
- [Common ways this goes wrong](#common-ways-this-goes-wrong)

---

## The two governing rules

### 1. Sell to the participants, not in the trend

Whoever supplies the people chasing a trend has a better business than the people chasing it. The market is larger, the customers are motivated by fear of missing out rather than by ordinary need, and the competition is thinner because supplying is less exciting than participating.

Concretely, for any trend X, the participant-facing businesses are: tooling that makes doing X faster, education on how to do X, curation of what's happening in X, done-for-you X, marketplaces connecting X buyers and sellers, and analytics on X performance.

This also survives the trend's death better. The people who supplied a fading trend already have the audience, the distribution, and the operating knowledge to supply the next one.

### 2. Every bet must leave an asset behind

Trends decay by definition. If a play ends with cash and nothing else, the next trend starts you at zero — an exhausting treadmill that never compounds.

Assets that outlive trends:

- **Email list** — the most portable. Survives platform changes entirely.
- **Domain with ranked content** — compounds, and can be repointed at an adjacent topic.
- **Distribution channel** — an audience anywhere you can reach without paying.
- **Reusable codebase** — the collector, the dashboard, the payment plumbing.
- **Operating knowledge** — knowing the shape of a trend cycle is itself the asset this skill builds.
- **Brand/reputation in a category** — slowest to build, hardest to lose.

Judge every play by what remains on day 200 after the trend dies on day 90. A play that leaves nothing should be priced accordingly — it must pay for itself entirely in cash, immediately.

---

## Play catalog by phase

### Ignition — awareness is scarce

Signal: `k_prior ≤ 0 < k_recent`, tiny absolute numbers, breadth low but non-zero, high false-positive rate.

**Budget: hours. Cash risk: near zero.** The entire point of this phase is to take cheap options on many trends, most of which will expire worthless.

| Play | Why it works here | Leaves behind |
|---|---|---|
| Register the exact-match domain | Costs ~$10, worth thousands if the trend lands | Domain |
| Claim the handle on 3–4 platforms | Free; unavailable later | Distribution |
| Create the `awesome-X` list / wiki / glossary | Ranks first because nothing else exists; becomes the canonical reference | SEO surface |
| Start the newsletter, issue #1 | First mover on a category newsletter is durable | List |
| Write the definitive "what is X" page | Captures the entire search wave when it arrives | SEO surface |

The economics here are option-like: pay a few dollars and a few hours per trend, take 20 of them, and the one that lands pays for all of them many times over. Do not build product at this phase — the false-positive rate is too high to justify any real cost.

### Early acceleration — clarity is scarce

Signal: A ≥ 1.3, breadth rising, discourse strong, commitment starting. No mature tooling exists yet.

**Budget: days.** This is where the highest returns per hour occur, because everyone can find the thing and almost nobody knows what to do about it.

| Play | Notes |
|---|---|
| Explainer content series | The "clarity" product. Ranks fast while competition is thin. |
| Curated roundup / directory | Low effort, high perceived value, extremely linkable |
| Free tool as lead magnet | A single-purpose calculator or converter that solves one annoying step. Best list-builder in existence for a technical audience. |
| Template / starter pack | Whatever people are rebuilding by hand right now |
| Paid community or cohort | Works only if the trend has genuine practitioner depth |

The strategic point of this phase is **not primarily revenue — it's capture.** Whatever you sell, the priority is converting the traffic wave into an owned list before the wave passes. Revenue at this phase is a bonus; the list is the point.

### Mid acceleration — time and effort are scarce

Signal: A between 0.8 and 1.3, commitment series clearly rising, first tools appearing, job postings starting.

**Budget: 1–3 weeks.** Clarity has become abundant; people know what to do and don't want to do it manually.

| Play | Notes |
|---|---|
| Micro-SaaS | The classic picks-and-shovels play. Target one painful step, not the whole workflow. |
| Paid templates / component libraries | Faster to ship than SaaS, no support burden, no churn |
| Done-for-you service | Highest margin per hour, lowest scalability. Excellent for validating what a tool should do. |
| API / data product | If you built the collector for detection, the data may itself be sellable |
| Integration with an incumbent | Ride an existing distribution channel (app store, plugin marketplace) |

Sequencing note that saves a lot of wasted building: **run the service before the tool.** Doing the work manually for five customers teaches you exactly which step to automate, and they pay you for the research. The most common failure at this phase is building the wrong automation confidently.

### Late acceleration / chasm — trust and proof are scarce

Signal: commitment accelerating, discourse flattening, content shifting to "how we did X at [ordinary company]", job postings established.

**Budget: weeks.** The early majority has arrived and they buy on peer references, not novelty.

| Play | Notes |
|---|---|
| Vertical specialization | "X for dental practices" beats "X" — the reference problem is solved within a niche |
| Case studies and proof assets | The actual product being bought at this phase |
| Integrations and migrations | Moving people from the incumbent to X, or connecting X to what they already run |
| Consulting / implementation | Trust is the scarce good and services deliver it directly |
| Certification / training | Works once a job market exists for the skill |

Generic tools get hard here because well-funded competitors have arrived. Narrowness is the advantage: a vertical is defensible against a generalist because the references are peer-matched.

### Saturation — differentiation is scarce

Signal: A < 0.8, breadth flat or falling, tooling abundant, discourse mixed with backlash.

**Budget: don't start new builds.** New generic entries at this phase almost always lose.

Still viable: selling to the sellers (tools for the X-tool vendors), consolidating small players, arbitraging into an underserved geography or language, or selling the asset while it still has revenue.

### Decay — harvest

Signal: both series negative, early adopters visibly moved on.

Extract the asset: retarget the email list to the adjacent next trend, repoint the domain, redeploy the codebase. This is why rule 2 exists — decay is only a loss if the play left nothing behind.

---

## Choosing between plays

Given a phase, several plays are usually viable. Decide with these, in order:

1. **Timescale fit.** Can it ship inside two doublings of the current T2? If not, cut it — the market you measured won't be the market you launch into.
2. **Asset yield.** What remains after decay? Prefer higher.
3. **Existing leverage.** Does the user already have an audience, a codebase, or domain expertise that shortcuts this? Leverage beats fit.
4. **Reversibility.** Prefer plays that can be abandoned cheaply. Inventory and headcount are the least reversible; content and code are the most.
5. **Competition density.** Count existing entries. Zero is a warning (maybe there's no market), five to fifteen is healthy, fifty means you're late for generic and need a vertical.

---

## Build budget math

A simple discipline that prevents most losses. Given doubling time T2 and a phase estimate:

```
max_build_days ≈ 2 × T2   (capped by the tier ceiling)
```

Two doublings is roughly how long a trend stays recognizably the same shape. Beyond that you are launching into different conditions than the ones you measured.

| T2 observed | Max build | Realistic plays |
|---|---|---|
| 1–3 days | Hours | Content only, or existing inventory |
| 1 week | ~2 weeks | Templates, lead magnets, explainers |
| 1 month | ~2 months | Micro-SaaS, paid products |
| 3+ months | Quarters | Real company, durable asset |

If the honest build estimate exceeds the budget, the correct move is not to work faster. It's to pick a smaller play at the same phase, or to target a slower-moving trend.

---

## Portfolio construction

Trend bets have venture-shaped returns: most produce nothing, a few produce everything. Structure accordingly.

- **5–10 concurrent small bets** rather than one large one. Small enough that any single failure is unremarkable.
- **Staged capital.** Ignition plays get hours. Only bets showing traction earn the multi-week build. Never grant week-scale effort on the strength of a phase estimate alone — make the market pay for the escalation with a real signal (signups, preorders, inbound).
- **Reserve the majority of capacity for follow-on.** When one bet works, it deserves more than the whole portfolio got. Most people under-invest in their winner because they're still tending the losers.
- **Deliberately include quiet-adoption bets** — commitment rising while discourse is flat. Lower excitement, far less competition, better unit economics. See `psychology.md` on the trough of disillusionment.
- **Track the portfolio's hit rate over time.** After ~20 bets you'll have a personal base rate, which is worth more than any individual analysis.

---

## Kill criteria

Write these **before starting**, in specifics, because the pressure to continue peaks exactly when the trend is loudest and criteria written after commitment get renegotiated.

A usable kill criterion has a metric, a threshold, and a date:

> "Kill if A drops below 0.8 for two consecutive weeks, **or** fewer than 50 signups by day 21, **or** more than 3 funded competitors ship the same thing."

Standard triggers worth including:

| Trigger | Threshold |
|---|---|
| Acceleration collapse | A < 0.8 sustained across two measurement windows |
| Breadth collapse | B falling while volume rises — it never escaped its container |
| Commitment never followed | Discourse peaked and commitment stayed flat for the whole window |
| Traction miss | Your own funnel misses a pre-set number by a pre-set date |
| Competitive flood | Well-funded entrants in the generic position |
| Personal | You've stopped wanting to work on it — a real and commonly ignored signal |

Killing well matters as much as picking well. The portfolio math only works if losers are cut fast enough that capacity flows to the winner.

---

## Common ways this goes wrong

**Building a tool on a hype-only signal.** Discourse accelerating, commitment flat, and someone ships a paid product into a market of spectators. The most expensive mistake available. The discourse/commitment split exists to prevent exactly this.

**Timescale mismatch.** A six-week build aimed at a five-day trend. Lost before it started.

**Confusing "no competition" with "opportunity."** Sometimes nobody built it because nobody will pay. Zero competitors at mid-acceleration is a warning sign, not a green light.

**Riding without capturing.** A content wave produces 200k views and no emails collected. All of the cost, none of the asset.

**Over-investing in the analysis.** The radar is a screening tool, not the product. If more time goes into measuring trends than into shipping against them, the skill is being used as a procrastination device. Screening should be cheap and fast; only the shortlist deserves depth.

**Falling in love with the first candidate.** The portfolio logic requires emotional flatness across bets. Enthusiasm should follow traction, not precede it.

# Signal Sources Cookbook

Concrete, mostly free endpoints for building trend series. Organized by whether a source is **backfillable** (you can reconstruct history today and compute acceleration immediately) or **forward-only** (you must start logging and wait).

Prefer backfillable sources when starting. They turn a multi-week wait into an afternoon.

## Contents
- [Backfillable sources](#backfillable-sources)
- [Forward-only sources](#forward-only-sources)
- [Commitment vs discourse classification](#commitment-vs-discourse-classification)
- [Collection architecture](#collection-architecture)
- [Rate limits and etiquette](#rate-limits-and-etiquette)

---

## Backfillable sources

### Wikipedia Pageviews — free, no key, best general-interest series

The most underrated source in trend detection. Daily granularity, years of history, and **not personalized**, which makes it immune to the filter-bubble failure mode.

```
GET https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/
    en.wikipedia/all-access/user/{ARTICLE}/daily/{YYYYMMDD}/{YYYYMMDD}
```

Requires a descriptive `User-Agent`. Use `all-agents` instead of `user` only if you want bot traffic included (you don't). `{ARTICLE}` is the URL-encoded title with underscores.

Caveats: only works for concepts that have an article; article renames break series continuity; general-public interest, so it lags niche professional adoption.

### Hacker News (Algolia) — free, no key, full history

Build a multi-year mention series in minutes. Best early source for developer, startup, and technology trends.

```
GET https://hn.algolia.com/api/v1/search_by_date
    ?query={TERM}
    &tags=story
    &numericFilters=created_at_i>{UNIX_START},created_at_i<{UNIX_END}
    &hitsPerPage=0
```

`hitsPerPage=0` returns just `nbHits` — a count, cheaply. Loop over monthly or weekly buckets to build the series. Add `&tags=comment` for a separate, noisier, higher-frequency series.

**`nbHits` can be a wild over-estimate on large result sets — gate on magnitude, not on the `exhaustiveNbHits` flag.** An unfiltered monthly query returned `nbHits: 366301` for a month whose true story total was 31,310 — an 11× error. Retrying does not help; the approximation is deterministic and cached.

The intuitive fix is to trust `exhaustiveNbHits`, and it is wrong in both directions. That flag tracks Algolia's internal query budget, not count truncation: the same query returned `exhaustiveNbHits: true` and `false` on different calls with an identical count, and small counts routinely come back with the flag false while being exactly right. Paginating `search_by_date` and counting hits by hand confirmed nbHits values of 41, 13, and 11 were all exact *with the flag false*. Gating on it discards most of your good data.

What actually predicts a bad count is the result set being large relative to the bucket. So:

```python
n = nbHits(term, bucket)
if n > 0.2 * total_stories_in(bucket):      # no term is a fifth of all HN
    n = sum(nbHits(term, wk) for wk in weeks_in(bucket))   # sub-buckets are exact
```

Worth being strict about, because of the failure mode: one inflated early bucket followed by exact later buckets manufactures a *decay* curve out of a flat one, and a dropped bucket manufactures a spike. Both are indistinguishable from real trend signal.

HN exposure also has a measurable downstream effect: an event-study of 138 AI/LLM repository launches found average GitHub star gains of roughly 121 at 24h, 189 at 48h, and 289 at 7 days, with medians far below the means — a long-tail distribution where a few launches dominate. Treat HN as a *shock source*, not just a mention counter: an HN front page hit is an intervention on the star series, and acceleration measured across that boundary is contaminated.

### npm downloads — free, no key, the best developer commitment signal

Downloads are commitment; stars are discourse. This distinction resolves most "is this real?" questions about developer tooling.

```
GET https://api.npmjs.org/downloads/range/{YYYY-MM-DD}:{YYYY-MM-DD}/{PACKAGE}
```

Up to 18 months per request. Scoped packages need URL encoding (`@scope%2Fname`).

Caveat: CI runs inflate download counts and produce a strong weekday/weekend cycle. Use 7-day rolling sums, never raw daily.

### PyPI downloads

Same role for the Python ecosystem. `pypistats` (CLI/library) wraps the public dataset; the underlying data also lives in the public BigQuery `pypi` dataset for heavier analysis. Same CI-inflation caveat applies.

### GitHub — stars with timestamps, plus commitment counterparts

Star history is backfillable if you request the starred-at timestamps:

```
GET https://api.github.com/repos/{OWNER}/{REPO}/stargazers
Accept: application/vnd.github.star+json
```

Paginated at 100/page and capped around 40k results, so very popular repos can only be partially reconstructed — a reason to catch repos early.

Discovery of *new* repos in a space:

```
GET https://api.github.com/search/repositories
    ?q={TERM}+created:>{YYYY-MM-DD}&sort=stars&order=desc
```

Commitment counterparts on GitHub: **forks**, **distinct contributors**, **dependent repos**, and issue volume containing "error"/"how do I". Stars cost nothing; those cost effort.

### Stack Overflow / Stack Exchange — pure commitment signal

People only ask questions about things they are actually using and stuck on.

```
GET https://api.stackexchange.com/2.3/questions
    ?site=stackoverflow&tagged={TAG}&fromdate={UNIX}&todate={UNIX}&filter=total
```

`filter=total` returns just a count. Note the platform-wide decline in question volume post-LLMs — always normalize against total site volume for the same window rather than reading raw counts.

### Google Trends — confirmatory, not leading

Useful, but treat as a check rather than a discovery tool. Two things to know:

- Values are **normalized 0–100 within the requested window**, not absolute. Two separately-pulled series are not comparable. Query terms together to compare them.
- "Breakout" in Rising Queries means roughly **+5000%**, which a near-zero base produces trivially. Breakout labels are frequently artifacts rather than meaningful behavior change.

Access via `pytrends` or a paid wrapper. Expect rate limiting.

### Wayback Machine — reconstruct anything

For sources with no API, the Internet Archive's CDX API lists snapshots of a URL over time; fetch a few and extract the number you care about (member counts, product counts, pricing). Slow but it works on almost anything.

```
GET http://web.archive.org/cdx/search/cdx?url={URL}&output=json&from=2023&to=2026
```

### Reddit historical archives

Pushshift was restricted to verified moderators after Reddit's 2023 API changes. **Arctic Shift** is the active successor for historical Reddit data with free unauthenticated access to archives. Use it for backfill; use the live JSON endpoints below for ongoing collection.

---

## Forward-only sources

### Reddit live JSON — subreddit growth and post velocity

```
GET https://www.reddit.com/r/{SUB}/about.json          -> subscribers, active_user_count
GET https://www.reddit.com/r/{SUB}/new.json?limit=100  -> post stream
GET https://www.reddit.com/r/{SUB}/search.json?q={TERM}&restrict_sr=1&sort=new&t=week
```

Send a real descriptive `User-Agent` or you'll get 429s immediately. Poll `about.json` daily and store — **subreddit growth rate is a far better signal than subreddit size**, and it's only available if you started logging.

For post-level outlier ratios, compare a post's score against the subreddit's trailing median score for the same hour-of-day.

### YouTube Data API — outlier ratios

Free quota (10,000 units/day by default; search costs 100 units, so budget carefully).

```
GET https://www.googleapis.com/youtube/v3/search?q={TERM}&order=date&publishedAfter={ISO8601}
GET https://www.googleapis.com/youtube/v3/videos?part=statistics&id={IDS}
GET https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL}
```

Compute `R = video_views / channel_trailing_median_views`. Channel median requires pulling that channel's recent uploads — cache it, it changes slowly. Commercial tools (vidIQ, ViewStats, and similar) productize this same ratio as an "outlier score", typically combining views-vs-baseline with views-per-hour; a score above 1.0× means the video is beating the channel's recent history. You can reproduce it with the raw API for free.

### TikTok / Instagram

No usable free API for trend data. Options, in order of practicality:

- **TikTok Creative Center** — free web tool with trending hashtags, sounds, and creators, filterable by region and window. Best available free source. The key metric to watch is *rate of increase in usage*, not usage.
- Sound velocity: track the video-count on a sound page over time (scrape or manual). A sound going 2K → 50K videos in days is ignition.
- Third-party APIs exist and are paid; only worth it if playing the micro tier seriously.

Given micro-tier trends can peak in ~72 hours, manual checking is not competitive here. Either automate or restrict yourself to meso/macro.

### Job postings — slowest, most trustworthy commitment signal

Companies spending money to hire for a skill is about as strong a commitment signal as exists. No clean free API; practical approaches: query a job board's search UI for a term and record the result count daily, or use Hacker News "Who is Hiring" monthly threads (fully backfillable via Algolia, well-structured, developer-skewed).

```
GET https://hn.algolia.com/api/v1/search?query=who+is+hiring&tags=story
```

Then count term occurrences in each month's comments. This gives a free, backfillable, monthly hiring-demand series.

### Product Hunt / app stores

New-launch counts in a category signal builder attention (discourse-adjacent — builders arrive before customers). App store rank movement signals consumer commitment. Both mostly require scraping or paid tools.

### Domain registrations

Bulk registrations containing a term is an early builder-intent signal. Zone files and paid registration-trend tools; niche but occasionally decisive.

---

## Commitment vs discourse classification

Keep this straight — it drives the whole phase estimate.

| Discourse (cheap, early, fakeable) | Commitment (costly, late, honest) |
|---|---|
| Mentions, posts, comments | Paid signups, revenue |
| Search volume | Package downloads |
| GitHub stars | GitHub forks, contributors, dependents |
| Video views, likes | Job postings |
| Press coverage | Support/help questions |
| Newsletter mentions | Conference talks *by practitioners* |
| Vendor blog posts | Integrations shipped by third parties |
| Wikipedia pageviews | Wikipedia edit count |

A vendor talking about a category is discourse. A non-vendor company hiring for it is commitment.

---

## Collection architecture

A workable minimal design for a solo builder:

1. **Watchlist table** — terms, aliases, tier, and which sources apply to each.
2. **Daily collector** — one row per (term, source, date, value). Append-only; never overwrite. Historical revisions destroy acceleration math.
3. **Backfill once** — Wikipedia, HN, npm/PyPI, GitHub star timestamps. This gives you A on day one instead of day thirty.
4. **Derived view** — compute A, T2, R, B per term per day via `scripts/trendmath.py`.
5. **Alert rule** — fire when A ≥ 1.3 **and** breadth is non-falling **and** the term clears an absolute floor (to suppress noise from tiny bases).
6. **Digest** — a ranked daily list, not a stream. Streams get ignored.

Two design notes that matter more than they look:

- **Store raw values, compute metrics downstream.** You will change the metric definitions; you cannot un-lose raw data.
- **Log the collection timestamp separately from the data date.** Many APIs revise recent values, and you need to know which vintage you acted on.
- **Drop the trailing partial bucket, always.** Today is almost never the end of a week or month, so the newest bucket is a fraction of a period and reads as a collapse. Since acceleration is dominated by the most recent window, one partial bucket is enough to turn a healthy series into a fake "decay" verdict — and it does it to *every* series at once, which is the tell. If a whole screen suddenly reads as decaying, suspect the harness before the world.
- **Normalize against platform volume where the platform itself drifts.** Total HN story volume moved from ~24k to ~34k per month over 16 months; a term holding constant share was silently "growing" 40% until divided through.
- **Check the provider's own coverage growth before trusting any of its history.** This is the most dangerous trap in the whole document, because it survives normalization. A commercial aggregator that is still scaling its crawler manufactures trends out of nothing: one job-postings API's monthly sample grew from 604 to 1,194,643 postings — **1,978×** — over sixteen months. Share-of-total corrects for sample *size* but not for a changing sample *frame*, and the frame moved: the summed share of the top 21 skills fell from ~2.0 to 1.39 over the same window, which cannot happen in a stable market. Every skill in that dataset looked like it was collapsing. The diagnostic is cheap — plot the denominator, and plot the sum of shares across a fixed basket. If either moves substantially, the history is unusable and the source is **forward-only**: start logging from the point coverage stabilizes. Prefer sources whose coverage is structurally fixed (a public register, a package registry, an encyclopedia) over vendors whose product is still growing.

Aliases deserve explicit handling: trends get renamed mid-flight, and a series that splits across two names looks like two dying trends instead of one accelerating one.

---

## Rate limits and etiquette

- Send a descriptive `User-Agent` identifying yourself. Reddit and Wikimedia both enforce this.
- Cache aggressively; most of these series change once per day at most.
- Respect `robots.txt` and terms of service. Public JSON endpoints are fine; scraping behind authentication is not.
- Back off on 429s rather than retrying tightly.
- Prefer official APIs over scraping wherever one exists — scrapers break, and breakage silently produces flat series that read as "trend died."

That last failure mode is worth guarding explicitly: **a broken collector and a dead trend look identical in the data.** Add a per-source health check that alerts on zero-rows rather than treating absence as a value.

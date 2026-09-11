---
name: domain-price-check
description: Check what a specific domain really costs and whether it can actually be registered - live availability, registry premium tier, renewal price, and launch-phase pricing for any TLD. Use it whenever a real domain name meets a money or availability question: how much is X, is X taken, first-year vs renewal, 5- or 10-year holding cost, which registrar is cheapest over that span, is this name premium-tier, is it a sane spend, or pricing a whole shortlist or file of candidates in one pass. Reach for this instead of quoting an advertised TLD rate or answering from memory - registries silently place desirable names into permanent premium tiers costing 5-70x list, and $9 first-year promos routinely renew at $40, so an unchecked price is usually wrong. Also returns launch calendars for unlaunched TLDs: the exact GA timestamp and the Early Access fee ladder. Not for DNS records, nameservers, transfers or WHOIS edits; to invent new name ideas use a naming skill, then come back here to price the survivors.
---

# Domain price check

## Why this exists

The advertised price of a TLD applies to the names nobody wants. Registries reserve
the good phrases into **premium tiers** with a permanently higher annual fee, and
availability lookups that only answer "taken / not taken" hide this completely.

The gap is large enough to invert a decision. In `.here`, the standard rate is
€20.17/yr, but `sign.here` renews at **€1,385.33/yr** - 69x - while `signhere.here`
sits at the standard rate. Same TLD, same registry, one word apart. Recommending a
shortlist without checking tiers means recommending names that cost four figures a
year to hold.

So: never quote a domain price from a TLD's advertised rate. Check the specific name.

## Quick start

```bash
python3 scripts/check_domains.py --names signhere,meetme,almost --tlds here
python3 scripts/check_domains.py --names-file candidates.txt --tlds com,io,dev --standard-only
python3 scripts/check_domains.py --tld-info here          # launch calendar + fee ladder
```

Pricing requires `GANDI_API_KEY` (free, see Setup). Without it the script still
runs but answers availability only, which covers almost none of the questions
worth asking - so set the key before relying on this.

Output is sorted cheapest-renewal-first, because renewal is the number that
compounds:

```
DOMAIN         STATUS      TIER       1ST YR EUR   RENEWAL EUR
signhere.here  available   standard   20.17        20.17
almost.here    available   premium    464.01       189.59
sign.here      available   premium    1,099.12     1,385.33
```

Useful flags: `--standard-only` (drop premium names entirely), `--available-only`,
`--json` (for further processing), `--currency`, `--country`, `--concurrency`.

## Setup

Pricing needs a Gandi **Personal Access Token** - free, no purchase required:
gandi.net → User Settings → Authentication options → Personal Access Token.

```bash
export GANDI_API_KEY=...
```

The token is read-only for this purpose and costs nothing; no domain purchase or
balance is required. Without it the script falls back to RDAP, which answers
availability only - no prices, no tiers, and blind to the premium tiers that are
the whole point. If the key is rejected the script says so immediately rather
than retrying, so a stale token fails loudly instead of looking like "no results".

## Reading the results

**Renewal, not first year, is the real price.** First-year figures are frequently
promotional or carry a one-off launch fee. `.com` shows €11.00 first year against
€31.98 renewal; `.app` shows €8.99 against €40.00. A shortlist ranked on first-year
price is ranked on marketing.

**Premium is permanent and travels with the name.** It is set by the registry, not
the registrar, so shopping around finds a few percent, never a way out of the tier.
Transferring the domain does not reset it.

**"unknown" means unknown, not available.** Around 300 TLDs - `.io` among them -
have no RDAP service at all, so the keyless availability path cannot see them and
says so rather than guessing. Treat `unknown` as "check with a registrar", never as
free. A generic RDAP proxy reports `google.io` as unregistered, which is how this
class of mistake usually reaches a recommendation.

**`reserved` is not `available`.** Reserved names are held back by the registry and
may never be sold, regardless of what a search box shows.

**Availability before GA is provisional.** A name reported available during a launch
phase can still be taken in sunrise, in an earlier Early Access day, or by another
registrar the instant GA opens. Pre-orders are queued requests, never guarantees.

## Unlaunched TLDs

`--tld-info <tld>` reconstructs the whole launch calendar from live registry data -
each phase, its price, and its exact start timestamp:

```
sunrise        20.17   2026-09-01 16:00
eap1         8745.17   2026-11-10 16:00
...
eap7          132.17   2026-11-16 16:00
golive         20.17   2026-11-17 16:00
```

This matters because the calendar is otherwise only published as prose in registrar
blog posts, and ICANN's own startup-information export covers only the 2012 round.

`--tld-info` also flags **flat rungs** - consecutive days priced identically - and
names the cheapest rung's first day. This matters more than it sounds: `.here`
prices eap6 and eap7 both at EUR 132.17, so buying on the last day costs the same
as the first and buys a day less exclusivity. Always enter a rung on its first day.

How to read a ladder: **Early Access is a descending Dutch auction**, not a discount.
Each day is a one-off surcharge on top of the normal fee, and it buys exclusivity
for that day rather than a guarantee. The last EAP day is usually the only rung
worth considering, and only for a name that would genuinely hurt to lose - it is
typically 5-10x the GA price for a few hours' head start. Everything else is
cheaper by waiting for `golive`.

## Working with shortlists

When someone brings a list of candidate names, check the whole list in one run
before commenting on any of them, then lead with what the check changed - which
names are premium, which are gone, what the cheap survivors actually are. A tier
result is often more decisive than the naming discussion that produced the list,
and compound or possessive phrasings (`signhere`, `meetme`, `imalmost`) routinely
escape tiers that the bare noun (`sign`, `meet`, `almost`) falls into. That is a
reliable way to rescue a good idea from a four-figure price tag.

Prices come back in the requested currency excluding tax; set `--country` for the
buyer's jurisdiction when tax matters.

## References

- `references/providers.md` - which registrar APIs return what, why Gandi is the
  one that covers pre-GA TLDs and phase pricing, and how to add another provider.
- `references/launch-phases.md` - how new gTLD launches work end to end, what each
  phase means, and where launch calendars are actually published.

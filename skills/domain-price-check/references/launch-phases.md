# How new gTLD launches work

Read this when a TLD has not reached General Availability, or when advising on
whether to pay an Early Access fee.

## The phases

**Sunrise** (typically 30-60 days). Restricted to trademark holders with a
validated Trademark Clearinghouse record. Usually priced at or near the standard
rate. Not available to a general buyer, so a name showing "available" during
sunrise can still disappear before it is purchasable.

**Early Access Period / EAP** (typically 7 days). Open to anyone, priced as a
descending Dutch auction. Day 1 can exceed €8,000; the final day is usually
€130-200. The fee is a **one-off surcharge on top of** the normal registration fee,
and renewals revert to the standard or premium rate for that name.

Two things people get wrong about EAP:

- It is not a discount schedule. Waiting is strictly cheaper; the fee buys a
  shrinking pool of competitors, not a better price.
- It is not a guarantee. It is still first-come, first-served at that day's price.

The honest calculus: the last EAP day is the only rung that usually makes sense,
and only for a name whose loss would genuinely hurt. Everything else should wait
for GA.

**General Availability / golive.** Standard first-come pricing, forever. Note the
exact timestamp - GA opens at a specific UTC instant and desirable names go in the
first seconds.

## Registry premium tiers

Registries carve out desirable strings into premium tiers with permanently elevated
annual fees. Tiers are per-name, set by the registry rather than the registrar, and
survive transfer. Google Registry's `.here` used six tiers: standard, then roughly
3x, 6x, 9x, 36x and 69x the standard rate.

The exploitable pattern: tiering targets bare, high-frequency words. Compound and
possessive forms of the same idea usually escape it - `sign` premium, `signhere`
standard; `almost` premium, `imalmost` standard. When a shortlist comes back
expensive, re-run it with compounded variants before giving up on the concept.

## Finding launch calendars

There is no clean machine-readable feed. In practice:

- `--tld-info <tld>` reconstructs phases, prices and start timestamps from live
  registry data. This is the most reliable route and the reason the flag exists.
- ICANN's TLD startup information page covers only the 2012 round and its CSV
  export runs as a batch job rather than returning a file.
- CSC's weekly launch guide and registrar blogs publish upcoming launches as prose,
  which is useful for discovering that a launch exists at all.

## Practical checks before buying into a launch

- Confirm the GA timestamp in UTC and what it is locally.
- Check the specific name's tier, not the TLD's advertised rate.
- Compare renewal prices across the registrars that carry the TLD - pre-GA that is
  often only two or three, and first-year teasers frequently hide higher renewals.
- Treat pre-orders as queued requests. Multiple registrars race the same instant.
- Check HTTPS enforcement rather than assuming it. Several Google Registry TLDs are
  on Chromium's HSTS preload list, which makes browsers refuse plain HTTP outright -
  `.app`, `.dev`, `.page`, `.new`, `.foo`, `.zip`, `.meme`, and of the 2026 wave both
  `.eat` and `.fly`. **`.here` is not on it**, despite launching alongside them and
  despite registrar marketing describing it as HTTPS-required. Registry policy and
  browser enforcement are different things, and the second is the one that breaks
  redirects and legacy tooling. Verify against the source rather than trusting a
  registrar page:

  ```bash
  curl -s https://raw.githubusercontent.com/chromium/chromium/main/net/http/\
  transport_security_state_static.json \
    | sed 's|^ *//.*||' | python3 -c "import json,sys; \
      n={e.get('name') for e in json.load(sys.stdin)['entries']}; \
      print('preloaded' if 'here' in n else 'not preloaded')"
  ```

# Registrar API landscape

Read this when choosing a data source, adding a provider, or explaining to someone
why a particular API cannot answer their question.

## Comparison

| API | Auth | Premium price | Launch-phase pricing | Carries TLDs pre-GA | Bulk |
|---|---|---|---|---|---|
| **Gandi v5** | free Personal Access Token | yes | **yes** (`periods` + `options.phase`) | **yes**, ~800 TLDs | 1/req |
| Spaceship | API key + secret | yes (`premiumPricing`) | no | no | 20/call |
| Dynadot | API key, any account | yes (`show_price=1`) | no | partial | 60/min free tier |
| Porkbun | free API key | yes | no | no | 1/call, tight limit |
| Namecheap | $50 balance or 20 domains + IP allowlist | yes (`IsPremiumName`) | no | no | 50/call |
| Domainr / Fastly | Fastly key, 10k free/mo | **no prices at all** | no | best coverage | yes |
| RDAP | none | no | no | n/a | 1/req |

## Why Gandi

Two properties matter for this skill and only Gandi has both:

1. **It sells TLDs before General Availability.** Most registrars only list a TLD
   once it goes live, so their APIs return "unsupported TLD" for exactly the
   launches worth researching. During `.here`'s sunrise only three registrars
   carried it at all, and Gandi was the only one of the three with an API.
2. **It returns the per-phase price ladder**, which is the only machine-readable
   source for a launch calendar. Everyone else exposes a single current price.

Domainr is the accuracy leader for *availability* - ICANN-accredited with direct
registry access - so it is the right addition if bulk availability at scale is ever
needed. It returns no pricing, so it complements rather than replaces Gandi.

## Gandi endpoints

**Documented (preferred).** `GET https://api.gandi.net/v5/domain/check`
with `Authorization: Bearer <PAT>`. Parameters: `name`, repeated `processes`
(`create`, `renew`), `currency`, `country`, optional `grid`, `sharing_id`.

Gandi also exposes an unauthenticated endpoint behind its own search box. This
skill deliberately does not use it: it is undocumented, and it rejects clients
that do not present browser headers, which is the operator saying plainly that it
is not a public API. Getting a token takes two minutes and the documented
endpoint returns the same data with a stability guarantee.

The API returns sporadic 503s under light load; retry with backoff and keep
concurrency low. Authentication failures (401 without a key, 403 with a bad one)
are not retryable and should surface immediately.

## The parsing trap

In `products[process=create]`, the `prices[]` and `periods[]` arrays appear
parallel and are **not**. Prices come back in arbitrary order, each tagged with
its own phase under `options.phase`:

```json
{"price": 8745.17, "options": {"phase": "eap1"}}
```

Zipping the two arrays by index scrambles the entire ladder while looking correct,
because `golive` tends to land last in both - which is exactly how the bug survives
a casual eyeball check. Always key on `options.phase`, falling back to positional
order only when the tag is absent, and join to `periods[]` by phase name to recover
each phase's `starts_at`. `check_domains.py` handles both `periods` and `phases`
spellings, since the two Gandi surfaces differ.

`process=renew` carries a single price entry - that is the recurring cost, and the
number worth ranking on.

## Adding a provider

`check_domains.py` expects a function that takes an FQDN and returns the shaped
dict produced by `_shape()`: `available`, `premium`, `reserved`, `currency`,
`first_year`, `renewal`, `phases`, `tier`. Add it to the `order` list in
`check_one()`; providers are tried in sequence and the first success wins, so put
richer sources ahead of thinner ones.

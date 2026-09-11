#!/usr/bin/env python3
"""
Contract tests for the registry response parser.

The parser is the part with no safety net: prices, premium detection, phase
association and renewal sorting all depend on the exact provider payload, and a
schema change would otherwise surface as blank prices or a wrong tier rather
than as an error. The fixtures below are trimmed from real responses.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import unittest

import check_domains as C


def _price(amount, phase=None, ptype=None, max_duration=1):
    p = {"duration_unit": "y", "min_duration": 1, "max_duration": max_duration,
         "price": amount, "price_before_taxes": amount, "price_after_taxes": amount,
         "discount": False, "options": {}, "features": []}
    if phase:
        p["options"] = {"phase": phase, "force_registration_display": True}
    if ptype:
        p["type"] = ptype
    return p


# Real .here ladder. Note the deliberate scrambling: this is the order the
# registry actually returns, and it is why index-zipping silently breaks.
SCRAMBLED_PRICES = [
    _price(306.17, "eap4"), _price(306.17, "eap5"), _price(20.17, "sunrise"),
    _price(132.17, "eap6"), _price(8745.17, "eap1"), _price(132.17, "eap7"),
    _price(2655.17, "eap2"), _price(915.17, "eap3"),
    _price(20.17, "golive", max_duration=10),
]
PHASE_META = [
    {"name": "sunrise", "starts_at": "2026-09-01T16:00:00Z"},
    {"name": "eap1", "starts_at": "2026-11-10T16:00:00Z"},
    {"name": "eap2", "starts_at": "2026-11-11T16:00:00Z"},
    {"name": "eap3", "starts_at": "2026-11-12T16:00:00Z"},
    {"name": "eap4", "starts_at": "2026-11-13T16:00:00Z"},
    {"name": "eap5", "starts_at": "2026-11-14T16:00:00Z"},
    {"name": "eap6", "starts_at": "2026-11-15T16:00:00Z"},
    {"name": "eap7", "starts_at": "2026-11-16T16:00:00Z"},
    {"name": "golive", "starts_at": "2026-11-17T16:00:00Z"},
]

EXPECTED_LADDER = {"sunrise": 20.17, "eap1": 8745.17, "eap2": 2655.17,
                   "eap3": 915.17, "eap4": 306.17, "eap5": 306.17,
                   "eap6": 132.17, "eap7": 132.17, "golive": 20.17}


class PhaseParsing(unittest.TestCase):
    def test_ladder_keys_on_phase_tag_not_index(self):
        """The bug this guards: zipping prices[] to phases[] by position."""
        ga, ptype, ladder, metas = C._phase_price(
            {"process": "create", "prices": SCRAMBLED_PRICES, "phases": PHASE_META})
        self.assertEqual(ladder, EXPECTED_LADDER)
        self.assertEqual(ga, 20.17)          # golive, not prices[0]
        self.assertEqual(len(metas), 9)

    def test_ladder_is_chronological_not_response_order(self):
        _, _, ladder, _ = C._phase_price(
            {"process": "create", "prices": SCRAMBLED_PRICES, "phases": PHASE_META})
        self.assertEqual(list(ladder), [m["name"] for m in PHASE_META])

    def test_documented_api_periods_spelling(self):
        """The authenticated endpoint says `periods`; the shop says `phases`."""
        _, _, ladder, _ = C._phase_price(
            {"process": "create", "prices": SCRAMBLED_PRICES, "periods": PHASE_META})
        self.assertEqual(ladder, EXPECTED_LADDER)

    def test_single_price_with_no_phases(self):
        ga, _, ladder, _ = C._phase_price(
            {"process": "renew", "prices": [_price(31.98)], "periods": []})
        self.assertEqual(ga, 31.98)
        self.assertEqual(ladder, {})

    def test_premium_type_detected_on_any_entry(self):
        _, ptype, _, _ = C._phase_price(
            {"process": "renew", "prices": [_price(725.06, ptype="premium")]})
        self.assertEqual(ptype, "premium")


class FlatRuns(unittest.TestCase):
    def test_only_consecutive_phases_group(self):
        runs = C.flat_runs(EXPECTED_LADDER)
        self.assertEqual(runs, [["eap4", "eap5"], ["eap6", "eap7"]])

    def test_equal_but_nonadjacent_phases_do_not_group(self):
        """sunrise and golive share a price but are months apart."""
        flat = [n for r in C.flat_runs(EXPECTED_LADDER) for n in r]
        self.assertNotIn("sunrise", flat)
        self.assertNotIn("golive", flat)


class Timestamps(unittest.TestCase):
    def test_utc_marker_survives(self):
        self.assertEqual(C._utc("2026-11-17T16:00:00Z"), "2026-11-17 16:00 UTC")

    def test_offset_is_normalised_to_utc(self):
        self.assertEqual(C._utc("2026-11-17T18:00:00+02:00"), "2026-11-17 16:00 UTC")

    def test_unparseable_passes_through_and_empty_is_empty(self):
        self.assertEqual(C._utc("not-a-date"), "not-a-date")
        self.assertEqual(C._utc(None), "")


class AuthenticatedParse(unittest.TestCase):
    """Exercises via_gandi_api end to end with _get stubbed."""

    def _run(self, payload, fqdn="signhere.here"):
        original = C._get
        C._get = lambda url, headers=None, timeout=25: (200, json.dumps(payload))
        try:
            return C.via_gandi_api(fqdn, "token", "EUR", "US")
        finally:
            C._get = original

    def test_standard_name(self):
        r = self._run({"currency": "EUR", "products": [
            {"status": "available", "process": "create",
             "prices": SCRAMBLED_PRICES, "periods": PHASE_META},
            {"status": "available", "process": "renew", "prices": [_price(20.17)],
             "periods": PHASE_META}]})
        self.assertTrue(r["available"])
        self.assertFalse(r["premium"])
        self.assertEqual(r["tier"], "standard")
        self.assertEqual(r["first_year"], 20.17)
        self.assertEqual(r["renewal"], 20.17)
        self.assertEqual(r["phases"], EXPECTED_LADDER)
        self.assertEqual(r["phase_dates"]["golive"], "2026-11-17T16:00:00Z")

    def test_premium_name_reports_its_recurring_price(self):
        r = self._run({"currency": "EUR", "products": [
            {"status": "available", "process": "create",
             "prices": [_price(1099.12, "golive", ptype="premium")],
             "periods": [{"name": "golive", "starts_at": "2026-11-17T16:00:00Z"}]},
            {"status": "available", "process": "renew",
             "prices": [_price(1385.33, ptype="premium")]}]}, "sign.here")
        self.assertTrue(r["premium"])
        self.assertEqual(r["tier"], "premium")
        self.assertEqual(r["renewal"], 1385.33)

    def test_taken_name(self):
        r = self._run({"currency": "EUR", "products": [
            {"status": "unavailable", "process": "create", "prices": []}]},
            "google.com")
        self.assertFalse(r["available"])

    def test_reserved_is_not_available(self):
        r = self._run({"currency": "EUR", "products": [
            {"status": "unavailable_reserved", "process": "create", "prices": []}]})
        self.assertFalse(r["available"])
        self.assertTrue(r["reserved"])

    def test_rejected_key_raises_rather_than_returning_blanks(self):
        import urllib.error

        def boom(url, headers=None, timeout=25):
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)

        original = C._get
        C._get = boom
        try:
            with self.assertRaises(C.AuthError):
                C.via_gandi_api("signhere.here", "bad", "EUR", "US")
        finally:
            C._get = original


class Sorting(unittest.TestCase):
    def test_unknown_renewal_sorts_last_not_as_free(self):
        rows = [{"domain": "b", "renewal": None}, {"domain": "a", "renewal": 20.17},
                {"domain": "c", "renewal": 1385.33}]
        rows.sort(key=lambda r: (r.get("renewal") is None, r.get("renewal") or 0,
                                 r["domain"]))
        self.assertEqual([r["domain"] for r in rows], ["a", "c", "b"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

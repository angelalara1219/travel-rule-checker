import unittest
from pathlib import Path

from travel_rule.check import check_transfer, near_threshold, run
from travel_rule.generate import build
from travel_rule.report import markdown, summary

DATA = Path(__file__).resolve().parent.parent / "data"
VASPS = {"Sample Exchange A"}


def row(**kw):
    base = dict(txn_id="T1", timestamp="2026-11-10T09:00", direction="outgoing", customer_id="C1",
                amount_usd="3000.00", asset="BTC", counterparty_type="VASP",
                counterparty_vasp="Sample Exchange A", originator_name="Ana Kim",
                originator_address="100 Main St, Phoenix, AZ", originator_account="ACCT-1",
                beneficiary_name="Luis Chen", beneficiary_account="bc1qxyz", travel_rule_status="sent")
    base.update(kw)
    return base


def codes(r):
    return sorted(e.code for e in check_transfer(r, VASPS))


class TravelRuleTests(unittest.TestCase):
    def test_exactly_3000_is_in_scope_and_clean(self):
        self.assertEqual(codes(row()), [])
        self.assertEqual(codes(row(originator_address="")), ["MISSING_ORIGINATOR_INFO"])

    def test_under_threshold_is_out_of_scope(self):
        self.assertEqual(codes(row(amount_usd="2999.99", originator_address="", travel_rule_status="")), [])

    def test_missing_beneficiary_and_not_sent(self):
        self.assertEqual(codes(row(beneficiary_account="", travel_rule_status="failed")),
                         ["MISSING_BENEFICIARY_INFO", "NOT_TRANSMITTED"])

    def test_unreviewed_vasp(self):
        self.assertEqual(codes(row(counterparty_vasp="Unknown Exchange")), ["UNREVIEWED_VASP"])

    def test_unhosted_needs_records_not_transmission(self):
        self.assertEqual(codes(row(counterparty_type="unhosted", counterparty_vasp="",
                                   travel_rule_status="n/a")), [])
        self.assertEqual(codes(row(counterparty_type="unhosted", counterparty_vasp="",
                                   travel_rule_status="n/a", originator_address="")), ["RECORD_INCOMPLETE"])

    def test_incoming_missing_originator(self):
        r = row(direction="incoming", originator_name="", travel_rule_status="received")
        self.assertEqual(codes(r), ["INCOMING_MISSING_ORIGINATOR"])

    def test_near_threshold_pattern(self):
        rows = [row(txn_id="A", amount_usd="2900", timestamp="2026-11-10T09:00"),
                row(txn_id="B", amount_usd="2950", timestamp="2026-11-10T20:00"),
                row(txn_id="C", amount_usd="2950", timestamp="2026-11-12T09:00"),   # 2 days later, alone
                row(txn_id="D", amount_usd="1200", timestamp="2026-11-10T10:00")]   # below the band
        self.assertEqual(sorted(e.txn_id for e in near_threshold(rows)), ["A", "B"])

    def test_one_near_threshold_transfer_alone_is_fine(self):
        self.assertEqual(near_threshold([row(amount_usd="2990")]), [])

    def test_generator_is_repeatable(self):
        self.assertEqual(build(), build())

    def test_sample_data_finds_every_seeded_gap(self):
        rows, exceptions = run(DATA / "transfers.csv", DATA / "reviewed_vasps.csv")
        found = {e.code for e in exceptions}
        self.assertEqual(found, {"MISSING_ORIGINATOR_INFO", "MISSING_BENEFICIARY_INFO", "NOT_TRANSMITTED",
                                 "UNREVIEWED_VASP", "INCOMING_MISSING_ORIGINATOR",
                                 "NEAR_THRESHOLD_PATTERN", "RECORD_INCOMPLETE"})
        self.assertNotIn("2999.99", {f"{e.amount_usd:.2f}" for e in exceptions})
        s = summary(rows, exceptions)
        self.assertLess(s["complete_and_sent"], s["outgoing_to_vasps"])
        self.assertIn("## Exception detail", markdown(rows, exceptions))


if __name__ == "__main__":
    unittest.main()

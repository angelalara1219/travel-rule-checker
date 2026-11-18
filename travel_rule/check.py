"""Travel Rule checks on crypto transfers.

The US Travel Rule (31 CFR 1010.410(f)) applies to transmittals of funds of $3,000 or more.
FinCEN has said it applies to convertible virtual currency the same way. For outgoing
transfers to another financial institution (here, a VASP), the sending institution has to
pass along the originator's name, address and account, the amount and date, and the
beneficiary details it has. Transfers to unhosted wallets have no receiving institution,
so nothing is transmitted, but the records still have to be kept.
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

THRESHOLD = 3000.00
NEAR_THRESHOLD = 2500.00          # start of the "just under" band
NEAR_WINDOW = timedelta(hours=24)

ORIGINATOR = ["originator_name", "originator_address", "originator_account"]
BENEFICIARY = ["beneficiary_name", "beneficiary_account"]

EXCEPTIONS = {
    "MISSING_ORIGINATOR_INFO": "Outgoing transfer is missing originator information",
    "MISSING_BENEFICIARY_INFO": "Outgoing transfer is missing beneficiary information",
    "NOT_TRANSMITTED": "Travel Rule information was not sent to the receiving VASP",
    "UNREVIEWED_VASP": "Counterparty VASP has no completed due diligence on file",
    "INCOMING_MISSING_ORIGINATOR": "Incoming transfer arrived without originator information",
    "NEAR_THRESHOLD_PATTERN": "Several transfers just under $3,000 within 24 hours",
    "RECORD_INCOMPLETE": "Unhosted-wallet transfer record is missing required fields",
}


@dataclass(frozen=True)
class Exception_:
    code: str
    txn_id: str
    customer_id: str
    amount_usd: float
    detail: str


def _missing(row, fields):
    return [f for f in fields if not row.get(f, "").strip()]


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_vasps(path):
    if not Path(path).exists():
        return set()
    return {r["vasp"].strip() for r in load(path) if r.get("due_diligence_completed", "").strip()}


def in_scope(row):
    return float(row["amount_usd"]) >= THRESHOLD


def check_transfer(row, reviewed_vasps):
    """Exceptions for one transfer. Under the threshold, the Travel Rule doesn't apply."""
    if not in_scope(row):
        return []
    out = []
    amt = float(row["amount_usd"])
    add = lambda code, detail: out.append(Exception_(code, row["txn_id"], row["customer_id"], amt, detail))
    vasp = row["counterparty_type"].strip() == "VASP"

    if row["direction"] == "outgoing":
        if vasp:
            if gaps := _missing(row, ORIGINATOR):
                add("MISSING_ORIGINATOR_INFO", "Missing: " + ", ".join(gaps))
            if gaps := _missing(row, BENEFICIARY):
                add("MISSING_BENEFICIARY_INFO", "Missing: " + ", ".join(gaps))
            if row["travel_rule_status"].strip() != "sent":
                add("NOT_TRANSMITTED", f"Status: {row['travel_rule_status'] or 'blank'}")
            if row["counterparty_vasp"].strip() not in reviewed_vasps:
                add("UNREVIEWED_VASP", row["counterparty_vasp"] or "No VASP named")
        elif gaps := _missing(row, ORIGINATOR + ["beneficiary_account"]):
            add("RECORD_INCOMPLETE", "Missing: " + ", ".join(gaps))
    elif vasp:
        if gaps := _missing(row, ["originator_name", "originator_account"]):
            add("INCOMING_MISSING_ORIGINATOR", "Missing: " + ", ".join(gaps) + "; follow up with sending VASP")
        if row["counterparty_vasp"].strip() not in reviewed_vasps:
            add("UNREVIEWED_VASP", row["counterparty_vasp"] or "No VASP named")
    return out


def near_threshold(rows):
    """Customers with 2+ outgoing transfers between $2,500 and $2,999.99 in 24 hours
    that add up to $3,000 or more. Not a Travel Rule violation by itself; a pattern to review."""
    by_customer = defaultdict(list)
    for r in rows:
        amt = float(r["amount_usd"])
        if r["direction"] == "outgoing" and NEAR_THRESHOLD <= amt < THRESHOLD:
            by_customer[r["customer_id"]].append((datetime.fromisoformat(r["timestamp"]), amt, r["txn_id"]))
    out = []
    for cust, txns in by_customer.items():
        txns.sort()
        flagged = set()
        for i, (t0, _, _) in enumerate(txns):
            window = [x for x in txns[i:] if x[0] - t0 <= NEAR_WINDOW]
            total = sum(x[1] for x in window)
            if len(window) >= 2 and total >= THRESHOLD:
                for t, amt, txn in window:
                    if txn not in flagged:
                        flagged.add(txn)
                        out.append(Exception_("NEAR_THRESHOLD_PATTERN", txn, cust, amt,
                                              f"{len(window)} transfers totaling ${total:,.2f} within 24 hours"))
    return out


def run(transfers_path, vasps_path):
    rows = load(transfers_path)
    reviewed = load_vasps(vasps_path)
    exceptions = [e for r in rows for e in check_transfer(r, reviewed)] + near_threshold(rows)
    return rows, exceptions

"""Build a synthetic week of crypto transfers with known Travel Rule gaps seeded in.

Usage:
    python -m travel_rule.generate            # writes data/transfers.csv
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

FIELDS = ["txn_id", "timestamp", "direction", "customer_id", "amount_usd", "asset",
          "counterparty_type", "counterparty_vasp",
          "originator_name", "originator_address", "originator_account",
          "beneficiary_name", "beneficiary_account", "travel_rule_status"]

FIRST = ["Maria", "James", "Linda", "Robert", "Ana", "David", "Grace", "Luis", "Karen", "Omar"]
LAST = ["Lopez", "Smith", "Nguyen", "Johnson", "Patel", "Garcia", "Kim", "Brown", "Rivera", "Chen"]
STREETS = ["Main St", "Oak Ave", "Mesa Dr", "Saguaro Ln", "Cactus Rd", "Central Ave"]
CITIES = ["Phoenix, AZ", "Tucson, AZ", "Dallas, TX", "Atlanta, GA", "Miami, FL", "Chicago, IL"]
KNOWN_VASPS = ["Sample Exchange A", "Sample Exchange B", "Sample Custodian C", "Sample Wallet D"]


def _person(rng):
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    address = f"{rng.randint(100, 9999)} {rng.choice(STREETS)}, {rng.choice(CITIES)}"
    return name, address


def _wallet(rng):
    return "bc1q" + "".join(rng.choice("023456789acdefghjklmnpqrstuvwxyz") for _ in range(30))


def build(seed=7, start=datetime(2026, 11, 9, 8, 0)):
    rng = random.Random(seed)
    customers = []
    for i in range(1, 41):
        name, address = _person(rng)
        customers.append({"id": f"C{i:04d}", "name": name, "address": address, "account": f"ACCT-{i:05d}"})

    rows = []

    def add(ts, direction, cust, amount, ctype="VASP", vasp=None, **overrides):
        other_name, _ = _person(rng)
        vasp = vasp if vasp is not None else (rng.choice(KNOWN_VASPS) if ctype == "VASP" else "")
        if direction == "outgoing":
            row = dict(originator_name=cust["name"], originator_address=cust["address"],
                       originator_account=cust["account"], beneficiary_name=other_name,
                       beneficiary_account=_wallet(rng))
        else:
            _, other_address = _person(rng)
            row = dict(originator_name=other_name, originator_address=other_address,
                       originator_account=_wallet(rng), beneficiary_name=cust["name"],
                       beneficiary_account=cust["account"])
        status = ("sent" if direction == "outgoing" else "received") if ctype == "VASP" else "n/a"
        row.update(txn_id=f"T{len(rows) + 1:05d}", timestamp=ts.isoformat(timespec="minutes"),
                   direction=direction, customer_id=cust["id"], amount_usd=f"{amount:.2f}",
                   asset="BTC", counterparty_type=ctype, counterparty_vasp=vasp,
                   travel_rule_status=status)
        row.update(overrides)
        rows.append(row)

    # Clean background activity: mostly small, some over the threshold, some unhosted.
    for _ in range(180):
        ts = start + timedelta(minutes=rng.randint(0, 7 * 24 * 60))
        amount = rng.choice([rng.uniform(50, 2400), rng.uniform(50, 2400), rng.uniform(3000, 25000)])
        ctype = "unhosted" if rng.random() < 0.25 else "VASP"
        add(ts, rng.choice(["outgoing", "outgoing", "incoming"]), rng.choice(customers), amount, ctype)

    # Seeded gaps, one or more of each kind, so the checks have something to find.
    c = customers
    add(start + timedelta(hours=5), "outgoing", c[0], 4200, originator_address="")
    add(start + timedelta(hours=9), "outgoing", c[1], 12500, beneficiary_name="")
    add(start + timedelta(hours=14), "outgoing", c[2], 3000, travel_rule_status="not_sent")
    add(start + timedelta(hours=30), "outgoing", c[3], 7800, travel_rule_status="failed")
    add(start + timedelta(hours=40), "outgoing", c[4], 5600, vasp="Unreviewed Exchange X")
    add(start + timedelta(hours=52), "incoming", c[5], 9100, originator_name="", originator_account="")
    add(start + timedelta(hours=60), "outgoing", c[6], 3350, beneficiary_account="", originator_account="")
    add(start + timedelta(hours=64), "outgoing", c[9], 6100, ctype="unhosted", originator_address="")
    # Below-threshold pattern: same customer, three transfers just under $3,000 in a few hours.
    for minutes, amount in ((0, 2950), (95, 2900), (210, 2980)):
        add(start + timedelta(hours=70, minutes=minutes), "outgoing", c[7], amount)
    # A transfer under the threshold with missing data is NOT a Travel Rule exception.
    add(start + timedelta(hours=80), "outgoing", c[8], 2999.99, originator_address="")

    rows.sort(key=lambda r: r["timestamp"])
    return rows


def main():
    rows = build()
    path = Path("data/transfers.csv")
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with open("data/reviewed_vasps.csv", "w", newline="", encoding="utf-8") as f:
        f.write("vasp,due_diligence_completed\n")
        for v in KNOWN_VASPS:
            f.write(f"{v},2026-06-30\n")
    print(f"Wrote {len(rows)} synthetic transfers to {path}")


if __name__ == "__main__":
    main()

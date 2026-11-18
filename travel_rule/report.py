"""Write the Travel Rule exceptions report.

Usage:
    python -m travel_rule.report
    python -m travel_rule.report --transfers path/to/export.csv
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

from .check import EXCEPTIONS, THRESHOLD, in_scope, run


def summary(rows, exceptions):
    scoped = [r for r in rows if in_scope(r)]
    scoped_vasp_out = [r for r in scoped if r["direction"] == "outgoing" and r["counterparty_type"] == "VASP"]
    travel_codes = {"MISSING_ORIGINATOR_INFO", "MISSING_BENEFICIARY_INFO", "NOT_TRANSMITTED"}
    failed = {e.txn_id for e in exceptions if e.code in travel_codes}
    clean = len([r for r in scoped_vasp_out if r["txn_id"] not in failed])
    rate = clean / len(scoped_vasp_out) * 100 if scoped_vasp_out else 100.0
    return {
        "transfers": len(rows),
        "in_scope": len(scoped),
        "outgoing_to_vasps": len(scoped_vasp_out),
        "complete_and_sent": clean,
        "pass_rate": rate,
    }


def markdown(rows, exceptions):
    s = summary(rows, exceptions)
    dates = sorted(r["timestamp"][:10] for r in rows)
    counts = Counter(e.code for e in exceptions)
    lines = [
        "# Travel Rule exceptions report",
        "",
        f"Period: {dates[0]} to {dates[-1]}. All data is synthetic.",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Transfers reviewed | {s['transfers']} |",
        f"| At or above ${THRESHOLD:,.0f} | {s['in_scope']} |",
        f"| Outgoing to VASPs at or above ${THRESHOLD:,.0f} | {s['outgoing_to_vasps']} |",
        f"| Complete and sent | {s['complete_and_sent']} ({s['pass_rate']:.1f}%) |",
        f"| Exceptions | {len(exceptions)} |",
        "",
        "## Exceptions by type",
        "",
        "| Code | What it means | Count |",
        "|---|---|---|",
    ]
    lines += [f"| {code} | {text} | {counts.get(code, 0)} |" for code, text in EXCEPTIONS.items()]
    lines += ["", "## Exception detail", "",
              "| Code | Transfer | Customer | Amount | Detail |", "|---|---|---|---|---|"]
    for e in sorted(exceptions, key=lambda e: (e.code, e.txn_id)):
        lines.append(f"| {e.code} | {e.txn_id} | {e.customer_id} | ${e.amount_usd:,.2f} | {e.detail} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description="Travel Rule exceptions report")
    p.add_argument("--transfers", default="data/transfers.csv")
    p.add_argument("--vasps", default="data/reviewed_vasps.csv")
    p.add_argument("--out", default="reports")
    args = p.parse_args(argv)

    rows, exceptions = run(args.transfers, args.vasps)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "exceptions.md").write_text(markdown(rows, exceptions), encoding="utf-8")
    with open(out / "exceptions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "txn_id", "customer_id", "amount_usd", "detail", "reviewer", "disposition", "date_closed"])
        for e in sorted(exceptions, key=lambda e: (e.code, e.txn_id)):
            w.writerow([e.code, e.txn_id, e.customer_id, f"{e.amount_usd:.2f}", e.detail, "", "", ""])
    s = summary(rows, exceptions)
    print(f"{s['transfers']} transfers, {s['in_scope']} in scope, {len(exceptions)} exceptions, "
          f"{s['pass_rate']:.1f}% of outgoing VASP transfers complete and sent")


if __name__ == "__main__":
    main()

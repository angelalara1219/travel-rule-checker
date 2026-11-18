# Travel Rule Checker

Checks crypto transfers against the US Travel Rule and produces an exceptions report a compliance team can work, test and hand to an examiner.

**All data in this repo is synthetic.** Names, addresses, wallets and VASPs are made up.

## Why I built this

I owned the Travel Rule process at Bitcoin Depot and monitored its automation for accuracy. The hard part was never the rule. It was proving, transfer by transfer, that the right information went out, catching the ones where it didn't, and showing the fix. This is the check I'd want running every week.

## The rule, briefly

The Travel Rule (31 CFR 1010.410(f)) applies to transmittals of funds of **$3,000 or more**, and FinCEN has said it covers convertible virtual currency the same way. When a transfer goes to another financial institution (here, another VASP), the sending institution must pass along the originator's name, address and account, the amount and date, and the beneficiary information it has. Transfers to unhosted wallets have no receiving institution, so nothing is transmitted, but the records still have to be kept.

## What it checks

| Code | When it fires |
|---|---|
| `MISSING_ORIGINATOR_INFO` | Outgoing transfer of $3,000+ to a VASP is missing originator name, address or account |
| `MISSING_BENEFICIARY_INFO` | Same, missing beneficiary name or wallet/account |
| `NOT_TRANSMITTED` | The Travel Rule message wasn't sent, or failed |
| `UNREVIEWED_VASP` | The counterparty VASP has no completed due diligence on file |
| `INCOMING_MISSING_ORIGINATOR` | An incoming transfer of $3,000+ arrived without originator information; follow up with the sending VASP |
| `RECORD_INCOMPLETE` | An unhosted-wallet transfer of $3,000+ is missing required record fields |
| `NEAR_THRESHOLD_PATTERN` | Two or more outgoing transfers of $2,500 to $2,999.99 from one customer within 24 hours that add up to $3,000+. Not a Travel Rule violation by itself, but worth a look for structuring around the threshold |

Transfers under $3,000 are out of scope for the Travel Rule checks, even when data is missing.

## Output

- [`reports/exceptions.md`](reports/exceptions.md): summary, exceptions by type and the full list
- `reports/exceptions.csv`: the same list with blank **reviewer**, **disposition** and **date closed** columns, so it doubles as a remediation log

From the sample week:

| Measure | Value |
|---|---|
| Transfers reviewed | 192 |
| At or above $3,000 | 76 |
| Outgoing to VASPs at or above $3,000 | 43 |
| Complete and sent | 38 (88.4%) |
| Exceptions | 12 |

## Run it

No packages to install. Python 3.10 or later.

```bash
python -m travel_rule.generate        # rebuild the synthetic week
python -m travel_rule.report          # write the reports
python -m unittest discover -s tests  # 10 tests
```

To run it on your own export, pass `--transfers path/to/file.csv` with these columns: `txn_id, timestamp, direction, customer_id, amount_usd, asset, counterparty_type, counterparty_vasp, originator_name, originator_address, originator_account, beneficiary_name, beneficiary_account, travel_rule_status`. Reviewed VASPs go in `data/reviewed_vasps.csv`.

## What this is not

- **Not a Travel Rule messaging solution.** It checks the records; it doesn't send anything.
- **Not legal advice.** Confirm requirements against the current regulation and FinCEN guidance, and note that other countries set different thresholds.

## Related

- [MTL Renewal Calendar](https://github.com/angelalara1219/mtl-renewal-calendar): license renewals, bonds, filings and exam items
- [CTR & GTO Monitor](https://github.com/angelalara1219/ctr-gto-monitor): daily CTR, GTO and structuring checks
- [State Money Transmitter Licensing Tracker](https://github.com/angelalara1219/state-mt-licensing-tracker): changes in state money transmitter law

## License

MIT

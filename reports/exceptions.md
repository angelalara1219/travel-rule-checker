# Travel Rule exceptions report

Period: 2026-11-09 to 2026-11-16. All data is synthetic.

| Measure | Value |
|---|---|
| Transfers reviewed | 192 |
| At or above $3,000 | 76 |
| Outgoing to VASPs at or above $3,000 | 43 |
| Complete and sent | 38 (88.4%) |
| Exceptions | 12 |

## Exceptions by type

| Code | What it means | Count |
|---|---|---|
| MISSING_ORIGINATOR_INFO | Outgoing transfer is missing originator information | 2 |
| MISSING_BENEFICIARY_INFO | Outgoing transfer is missing beneficiary information | 2 |
| NOT_TRANSMITTED | Travel Rule information was not sent to the receiving VASP | 2 |
| UNREVIEWED_VASP | Counterparty VASP has no completed due diligence on file | 1 |
| INCOMING_MISSING_ORIGINATOR | Incoming transfer arrived without originator information | 1 |
| NEAR_THRESHOLD_PATTERN | Several transfers just under $3,000 within 24 hours | 3 |
| RECORD_INCOMPLETE | Unhosted-wallet transfer record is missing required fields | 1 |

## Exception detail

| Code | Transfer | Customer | Amount | Detail |
|---|---|---|---|---|
| INCOMING_MISSING_ORIGINATOR | T00186 | C0006 | $9,100.00 | Missing: originator_name, originator_account; follow up with sending VASP |
| MISSING_BENEFICIARY_INFO | T00182 | C0002 | $12,500.00 | Missing: beneficiary_name |
| MISSING_BENEFICIARY_INFO | T00187 | C0007 | $3,350.00 | Missing: beneficiary_account |
| MISSING_ORIGINATOR_INFO | T00181 | C0001 | $4,200.00 | Missing: originator_address |
| MISSING_ORIGINATOR_INFO | T00187 | C0007 | $3,350.00 | Missing: originator_account |
| NEAR_THRESHOLD_PATTERN | T00189 | C0008 | $2,950.00 | 3 transfers totaling $8,830.00 within 24 hours |
| NEAR_THRESHOLD_PATTERN | T00190 | C0008 | $2,900.00 | 3 transfers totaling $8,830.00 within 24 hours |
| NEAR_THRESHOLD_PATTERN | T00191 | C0008 | $2,980.00 | 3 transfers totaling $8,830.00 within 24 hours |
| NOT_TRANSMITTED | T00183 | C0003 | $3,000.00 | Status: not_sent |
| NOT_TRANSMITTED | T00184 | C0004 | $7,800.00 | Status: failed |
| RECORD_INCOMPLETE | T00188 | C0010 | $6,100.00 | Missing: originator_address |
| UNREVIEWED_VASP | T00185 | C0005 | $5,600.00 | Unreviewed Exchange X |

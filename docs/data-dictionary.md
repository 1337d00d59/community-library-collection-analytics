# Data dictionary

`data/sample_ledger.csv` is a fictional 12-month event ledger. Each row is uniquely identified by `(period, community_id, collection_family)`.

| Field | Type | Meaning |
|---|---|---|
| `period` | `YYYY-MM` | Calendar month; analysis requires an explicit start and number of months |
| `community_id` | text | Stable four-letter identifier in this sample |
| `community_name` | text | Display name, consistent for each ID |
| `collection_family` | text | Broad nonoverlapping category |
| `opening_count` | nonnegative integer or blank | Count carried into the month, when known |
| `added` | nonnegative integer or blank | Newly recorded items |
| `withdrawn` | nonnegative integer or blank | Items removed |
| `transferred_in` | nonnegative integer or blank | Items assigned from another community |
| `transferred_out` | nonnegative integer or blank | Items assigned to another community |
| `closing_count` | nonnegative integer or blank | Independently observed end-of-month count |
| `quality_note` | text | Optional source note about a known issue |

Blank numeric fields mean **unknown**. A literal `0` is a known value. The text `NULL` is invalid input. The generator creates a real zero for Indigo Point's community kits in October 2025.

For a fully reported row, the derived closing value is `opening_count + added - withdrawn + transferred_in - transferred_out`. The observed `closing_count` is never overwritten to make that equation balance; a discrepancy becomes a quality issue. The generator makes transfers balance systemwide for each month and collection family.

The fixture contains three deliberate quality cases:

1. All four Echo Meadow rows in April 2026 have blank numeric fields; the system total is unavailable for that month.
2. Cirrus Landing's February 2026 `audio_video` withdrawal value is blank, while its observed closing count exists; the monthly withdrawal sum is unavailable.
3. Goldleaf Quay's September 2026 `youth_print` closing count is 19 higher than the value implied by its flows; the latest totals are provisional pending reconciliation.

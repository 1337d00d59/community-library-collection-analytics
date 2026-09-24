# Tableau Public build guide

## Status and purpose

This directory is an **import-ready Tableau build kit**, not a completed Tableau workbook or a published viz. The Python/Matplotlib pipeline remains fully reproducible. The Tableau layer adds direct exploration: selecting a community, comparing collection families, changing a measure, and following a three-part data story. Creating a real Tableau workbook in Tableau Public is the remaining authoring step.

Tableau Public supports CSV and browser authoring; the free Desktop Public Edition can also save a workbook locally before publication. Published workbooks and their data are public, and CSV-based sources do not refresh automatically. This project's data is entirely fictional. [Tableau Public FAQ](https://help.tableau.com/current/pro/desktop/en-us/public_faq.htm) · [Save locally or to Public](https://help.tableau.com/current/pro/desktop/en-us/publish_workbooks_tableaupublic.htm)

## Start with these four files

The command `python scripts/export_tableau.py` generates each file from the validated ledger. Copies are included under `tableau/data/`.

| Data source | Rows | Use in Tableau |
|---|---:|---|
| `network_monthly.csv` | 12 | Safe system trend and monthly flow chart |
| `community_family_monthly.csv` | 432 | Interactive community/family exploration and calculated fields |
| `community_latest.csv` | 9 | Current ranking, status, and month-to-month change |
| `quality_issues.csv` | 10 | Exception timeline and detail table |

Import the CSVs as **separate data sources**. They have different grains; joining them naively would multiply rows and totals. Confirm `period_date` is a Date and numeric columns are Numbers after import. An empty numeric cell must remain Null, not text or zero. Web authoring can upload text-based files; Desktop Public Edition can open the CSVs locally. [Web authoring upload help](https://help.tableau.com/current/pro/desktop/en-us/getstarted_web_authoring.htm)

### Key numerical checks

Before designing, check the data pane against these expected values:

- `network_monthly.csv`: April 2026 `reported_total` is **Null**; September 2026 is **264,019**, `reporting_status=provisional`.
- `community_family_monthly.csv`: four Echo Meadow April rows have Null closing counts; the September Goldleaf Quay youth-print row has `reconciliation_delta=19`.
- `community_latest.csv`: nine rows, with Goldleaf Quay marked provisional.
- `quality_issues.csv`: ten issue rows. These include multiple issues for the same missing April report; do not call them ten separate real-world incidents.

## Build two complementary dashboards

### 1. Network overview — the board entry point

From `network_monthly.csv`, create a month-by-month line of `reported_total`, and a second view with monthly `added` and `withdrawn`. Add a small status strip or issue-count indicator so April's missing total and September's provisional count remain visible.

**Critical null setting:** In the trend's measure formatting, choose the special-value option equivalent to **hide and break the line** for Null. Do not plot Null as zero, connect across April, or apply `ZN()`. Tableau documents these options in [Format Numbers and Null Values](https://help.tableau.com/current/pro/desktop/en-us/formatting_specific_numbers.htm). The `period_date` row for April is present; its total is Null, so the missing period can be visibly retained.

Optional interactivity: create a String parameter called `Measure to view` with values `Observed holdings`, `Items added`, and `Items withdrawn`. On the 12-row network source, this aggregate calculated field switches the chart metric:

```tableau
CASE [Measure to view]
WHEN "Observed holdings" THEN SUM([reported_total])
WHEN "Items added" THEN SUM([added])
WHEN "Items withdrawn" THEN SUM([withdrawn])
END
```

Show the parameter control. Use a dynamic title that names the selected metric and retain the status strip. Each month has exactly one row in this source, so this measure will not double-count a repeated system total. Tableau supports calculated fields and parameter controls in Public authoring. [Calculated fields](https://help.tableau.com/current/pro/desktop/en-us/calculations_calculatedfields_create.htm) · [Parameters](https://help.tableau.com/current/pro/desktop/en-gb/changing-views-using-parameters.htm)

### 2. Community explorer — the interactive investigation

Use `community_latest.csv` for a horizontal ranking of `current_total`, coloring or marking `status`. Use `community_family_monthly.csv`, filtered to `is_latest=TRUE`, for a community × collection-family heatmap. Then create a single-community 12-month detail view from the same long table, showing the selected family or all four distinct families.

Put the heatmap and single-community detail on one dashboard. Make the heatmap **Use as Filter**, or add an explicit Community filter shared between the two sheets. Selecting a community should update the detail view; a collection-family selection can further narrow it. Tableau documents this dashboard interaction as a [filter action](https://help.tableau.com/current/pro/desktop/en-us/actions_dashboards.htm).

Keep the detail view restricted to **one community at a time**. Summing the long table across all communities in April would silently produce a partial network total. The overview must use `network_monthly.csv` for system totals.

On the long data source, add a calculated field named `Check closing` to demonstrate independent Tableau reasoning rather than simply displaying Python's label:

```tableau
IF ISNULL([closing_count]) THEN "Missing closing"
ELSEIF ISNULL([opening_count]) OR ISNULL([added]) OR ISNULL([withdrawn])
    OR ISNULL([transferred_in]) OR ISNULL([transferred_out]) THEN "Change incomplete"
ELSEIF [closing_count] <> [opening_count] + [added] - [withdrawn]
    + [transferred_in] - [transferred_out] THEN "Reconciliation difference"
ELSE "Complete"
END
```

Compare this field to the imported `data_status`; they should agree for all 432 records. Put `Check closing`, `quality_note`, and `reconciliation_delta` in tooltips. Show `quality_issues.csv` as a compact issue timeline or table beside the explorer; keep its counts labeled as **findings**, because the four April rows generate more than one finding each.

## Tell a short story, not just four charts

Create a three-point Tableau Story or use three clearly labeled dashboard sections. Tableau's story feature supports a sequence of interactive views; see [Stories](https://help.tableau.com/current/pro/desktop/en-us/stories.htm).

1. **What changed?** The observed network total moved from 262,466 in October to a provisional 264,019 in September. Let the reader explore additions and withdrawals, rather than implying the endpoint alone explains the movement.
2. **What can't we safely say?** Echo Meadow's April report is missing, so the network total has a gap. Cirrus Landing's February withdrawal log is unavailable despite a reported closing count.
3. **Where would we investigate?** Goldleaf Quay's September youth-print observed count is 19 above the count implied by the ledger's flows. Filter to that community and family and display the calculation beside the observed number.

End with the board-facing sentence: *The latest observed total is provisional until the 19-item difference is reconciled; no April network total is claimed.* All narrative pertains to fictional example data.

## Visual design and final QA

- Use the same restrained colors as the Matplotlib charts: navy/blue for holdings, teal for additions, coral for withdrawals, amber for warnings.
- Label measure units as **items**. Put exact counts in tooltips and avoid decorative maps: the fictional communities have no meaningful geographic coordinates.
- Keep the status strip visible during filtering. If a filter changes the meaning of the numerator, adjust the title accordingly.
- Test both desktop and narrow layouts; add explanatory alt text and readable color contrast.
- Validate the four numerical checks above after authoring and after publishing. Click the Goldleaf and Echo marks to confirm tooltips and gap behavior.
- Save a local workbook (`.twbx`) for review if using Desktop Public Edition. Add the Tableau Public URL to the main README and LinkedIn only after the published viz has been inspected.

This guide prepares the authoring work; the repository currently makes **no claim that a Tableau dashboard has already been built or published**.

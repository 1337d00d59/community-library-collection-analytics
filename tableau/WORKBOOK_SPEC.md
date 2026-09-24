# Tableau Public workbook specification

**Status:** Import-ready construction plan. A Tableau workbook has not been authored or published. The four fictional CSVs are in `tableau/data/`; keep them as separate data sources because their row grains differ.

## Connect and check

Upload `network_monthly.csv` (12 rows), `community_family_monthly.csv` (432), `community_latest.csv` (9), and `quality_issues.csv` (10). Do not join or relate them. Set `period_date` to Date, counts/deltas to Number, and blank numeric cells to Null. Treat `is_latest` as Boolean, or filter its string value `TRUE` if Tableau imports it as text.

## Worksheets

| Sheet | Source | Build | Safeguard |
|---|---|---|---|
| Network trend | network_monthly | Continuous MONTH(period_date) on Columns; SUM(reported_total) on Rows; Line marks | For Null special values, **Hide and break the line**. Keep April 2026 visible in the date range. |
| Monthly flows | network_monthly | Discrete MONTH(period_date) on Columns; Measure Values with only SUM(added) and SUM(withdrawn) on Rows; Measure Names on Color; side-by-side Bars | Do not turn February withdrawals or April flows into zero. |
| Reporting status | network_monthly | Discrete MONTH(period_date) on Columns; reporting_status on Color and Label; Square marks | Add issue_count and missing_closings to tooltips. |
| Current communities | community_latest | community_name on Rows; SUM(current_total) on Columns; Bars; status on Color | Sort descending and show change in tooltip. |
| Family matrix | community_family_monthly | community_name on Rows; collection_family on Columns; SUM(closing_count) on Color and Label; Squares | Filter is_latest=TRUE **only on this sheet**. |
| Community history | community_family_monthly | Continuous MONTH(period_date) on Columns; SUM(closing_count) on Rows; collection_family on Color; Line marks | Restrict to one community using the parameter below; break lines at Null. |
| Quality findings | quality_issues | period, community_id, collection_family on Rows; kind and detail on Text | Label the ten rows **validation findings**, not independent incidents. |

Format counts as whole **items** with thousands separators. Match the Matplotlib palette: holdings `#326CA0`, additions `#138B83`, withdrawals `#AD514D`, warnings `#D6A13B`, headings `#17324D`.

## Controls and independent calculation

Create a String parameter named **Community to inspect** with the nine distinct `community_name` values. Initial value: **Goldleaf Quay**. Create a Boolean calculation on the long data source called **Selected community**:

```tableau
[community_name] = [Community to inspect]
```

Filter **Community history** to Selected community=True, and show the parameter control on the explorer dashboard. This ensures the detail view contains one community, even before a click. Add `collection_family` as a visible filter scoped to Community history; initially select all four. Do not apply the September `is_latest` filter to the 12-month history.

Create another row-level calculation named **Check closing**:

```tableau
IF ISNULL([closing_count]) THEN "Missing closing"
ELSEIF ISNULL([opening_count]) OR ISNULL([added]) OR ISNULL([withdrawn])
    OR ISNULL([transferred_in]) OR ISNULL([transferred_out]) THEN "Change incomplete"
ELSEIF [closing_count] <> [opening_count] + [added] - [withdrawn]
    + [transferred_in] - [transferred_out] THEN "Reconciliation difference"
ELSE "Complete"
END
```

Place Check closing, data_status, expected_closing, and reconciliation_delta in relevant tooltips. The calculation should agree with data_status on all 432 rows. A metric selector for the Network trend is optional; the aggregate calculation is in [BUILD_GUIDE.md](BUILD_GUIDE.md#1-network-overview--the-board-entry-point).

## Dashboards and story

**Network overview:** title and “fictional example” subtitle; large Network trend; Reporting status immediately below; Monthly flows below; compact Quality findings table. Keep the status strip visible if a parameter changes measures. Visible caption: **April 2026 has no complete network total; September's 264,019 observed items are provisional.**

**Community explorer:** Current communities ranking at left, Family matrix at upper right, Community history below. Show Community to inspect and the family filter next to history. Caption that the matrix is September only while history spans 12 months. Never sum the long table across all communities to represent the network.

Create a three-point Tableau Story if Story sheets are available in the authoring surface; otherwise use three labeled dashboard sections:

1. **What changed?** Network overview: 262,466 observed items in October 2025; 264,019 in September 2026, provisional. Invite inspection of flows.
2. **What is missing?** Highlight the April network gap and Quality findings: four Echo Meadow closing counts are absent; February's Cirrus Landing withdrawal log is unavailable.
3. **What needs investigation?** Community explorer with Goldleaf Quay selected and youth_print highlighted: observed 11,770, flow-derived 11,751, difference +19.

End with: **The latest observed total is provisional until the 19-item difference is reconciled; no April network total is claimed.**

## Acceptance checks

- April network reported_total is Null; it is neither zero nor a partial sum. February withdrawn is Null while its separately observed total is 263,604, provisional.
- September network total is 264,019, provisional; the Goldleaf youth_print discrepancy is +19.
- A true zero exists in October 2025 at INDI/community_kits. It remains visually distinct from Echo Meadow's four missing April closings.
- Test the community selector for Goldleaf Quay and Echo Meadow, tooltips, keyboard interaction, narrow layout, and readable contrast. The captions must make the story understandable without hovering.
- Save, reopen, and inspect the actual Tableau Public workbook before adding its URL to the README. Tableau Public does not automatically refresh CSV sources.

Official references: [web authoring](https://help.tableau.com/current/pro/desktop/en-us/getstarted_web_authoring.htm), [null formatting](https://help.tableau.com/current/pro/desktop/en-us/formatting_specific_numbers.htm), [dashboard actions](https://help.tableau.com/current/pro/desktop/en-us/actions_dashboards.htm), [stories](https://help.tableau.com/current/pro/desktop/en-us/stories.htm), and [Tableau Public FAQ](https://help.tableau.com/current/pro/desktop/en-us/public_faq.htm).

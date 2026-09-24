#!/usr/bin/env python3
"""Turn a generic monthly event ledger into a documented board-view example."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from charts import render
from ledger import Analysis, analyze, load_records


def write_table(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: int | None) -> str:
    return f"{value:,}" if value is not None else "Unavailable"


def write_brief(analysis: Analysis, path: Path) -> None:
    current, previous = analysis.monthly[-1], analysis.monthly[-2]
    diff = current.reported_total - previous.reported_total if (
        current.reported_total is not None and previous.reported_total is not None) else None
    gap_months = [m.period for m in analysis.monthly if m.reported_total is None]
    mismatches = [i for i in analysis.issues if i.kind == "reconciliation_mismatch"]
    unknown_flows = [i for i in analysis.issues if i.kind == "incomplete_change_data" and i.period not in gap_months]

    lines = [
        "# Fictional collection-change brief", "",
        f"**Period:** {analysis.periods[0]} through {analysis.periods[-1]}  ",
        f"**Scope:** {len(analysis.communities)} fictional communities and {len(analysis.families)} collection families  ",
        "**Status:** Demonstration data, not actual library statistics", "",
        "## What the latest records show", "",
        f"- Latest observed holdings: **{fmt(current.reported_total)}** ({current.status}).",
        f"- Previous month: **{fmt(previous.reported_total)}**; change: **{f'{diff:+,}' if diff is not None else 'unavailable'}** items.",
        f"- Months without a defensible system total: **{', '.join(gap_months) if gap_months else 'none'}**.",
        "- These are inventory counts, not circulation, demand, use, or collection quality measures.", "",
        "## Data quality for a board reader", "",
    ]
    if gap_months:
        for month in gap_months:
            missing = sorted({i.community_id for i in analysis.issues
                              if i.period == month and i.kind in ("missing_closing", "missing_row")})
            lines.append(f"- **{month}:** no system total is plotted because {', '.join(missing)} has missing closing counts.")
    if unknown_flows:
        for issue in unknown_flows:
            lines.append(f"- **{issue.period}, {issue.community_id}/{issue.collection_family}:** a change field is missing ({issue.detail}); the observed closing count remains available.")
    if mismatches:
        for issue in mismatches:
            lines.append(f"- **{issue.period}, {issue.community_id}/{issue.collection_family}:** reconciliation pending. {issue.detail}.")
    if not (gap_months or unknown_flows or mismatches):
        lines.append("- No gaps or reconciliation issues found in the supplied period.")
    lines += ["", "The latest system total includes all observed closing counts, including any provisional count identified above. Investigate discrepancies before treating it as final.", "",
              "## Charts", "",
              "![Monthly observed system holdings](images/system-trend.png)", "",
              "![Latest holdings by community](images/community-holdings.png)", "",
              "![Monthly additions and withdrawals](images/monthly-flows.png)", "",
              "![Collection mix by community](images/collection-mix.png)", "",
              "## Reading the files", "",
              "`monthly_system.csv` includes blanks for totals that cannot be calculated. `quality_issues.csv` lists each validation finding. `current_communities.csv` supplies observed community totals and status. A blank CSV cell means **unknown**, while `0` means a reported zero.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(analysis: Analysis, out_dir: Path) -> None:
    if analysis.monthly[-1].reported_total is None:
        raise ValueError("Latest system total is incomplete; a current board view would omit a community count")
    out_dir.mkdir(parents=True, exist_ok=True)
    monthly_fields = ("period", "reported_total", "added", "withdrawn", "transferred_in",
                      "transferred_out", "missing_closings", "issue_count", "status")
    write_table(out_dir / "monthly_system.csv", monthly_fields,
                [{name: getattr(row, name) for name in monthly_fields} for row in analysis.monthly])
    community_fields = ("community_id", "community_name", "current_total", "previous_total", "change", "status")
    write_table(out_dir / "current_communities.csv", community_fields,
                [{name: getattr(row, name) for name in community_fields} for row in analysis.communities])
    issue_fields = ("period", "community_id", "collection_family", "kind", "detail")
    write_table(out_dir / "quality_issues.csv", issue_fields,
                [{name: getattr(row, name) for name in issue_fields} for row in analysis.issues])
    chart_paths = render(analysis, out_dir / "images")
    write_brief(analysis, out_dir / "board_brief.md")
    print(f"Analyzed {len(analysis.records)} records across {len(analysis.periods)} months")
    print(f"Wrote {len(analysis.issues)} validation findings and {len(chart_paths)} charts to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a fictional collection-change ledger and chart the results.")
    parser.add_argument("--ledger", type=Path, required=True, help="Monthly collection-change CSV")
    parser.add_argument("--start", required=True, help="First month, YYYY-MM")
    parser.add_argument("--months", type=int, required=True, help="Number of monthly periods")
    parser.add_argument("--out", type=Path, required=True, help="Directory for analysis, brief, and PNGs")
    args = parser.parse_args()
    write_outputs(analyze(load_records(args.ledger), start=args.start, months=args.months), args.out)


if __name__ == "__main__":
    main()

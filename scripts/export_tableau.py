#!/usr/bin/env python3
"""Export validated, Tableau-friendly CSV views of the synthetic ledger."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ledger import analyze, load_records  # noqa: E402


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export(ledger_path: Path, out_dir: Path, *, start: str, months: int) -> dict[str, Path]:
    analysis = analyze(load_records(ledger_path), start=start, months=months)
    if analysis.monthly[-1].reported_total is None:
        raise ValueError("Latest month has no complete system total; do not export a partial current dashboard")

    network = []
    for i, row in enumerate(analysis.monthly):
        previous = analysis.monthly[i-1].reported_total if i else None
        change = row.reported_total - previous if previous is not None and row.reported_total is not None else None
        network.append({
            "period_date": f"{row.period}-01", "period": row.period,
            "reported_total": row.reported_total,
            "change_from_previous": change,
            "added": row.added, "withdrawn": row.withdrawn,
            "missing_closings": row.missing_closings, "issue_count": row.issue_count,
            "reporting_status": row.status,
        })

    detail = []
    for row in analysis.records:
        flows = (row.opening_count, row.added, row.withdrawn, row.transferred_in, row.transferred_out)
        expected = (row.opening_count + row.added - row.withdrawn + row.transferred_in - row.transferred_out
                    if all(value is not None for value in flows) else None)
        difference = row.closing_count - expected if expected is not None and row.closing_count is not None else None
        status = ("Missing closing" if row.closing_count is None
                  else "Reconciliation difference" if difference else "Change incomplete" if expected is None
                  else "Complete")
        detail.append({
            "period_date": f"{row.period}-01", "period": row.period,
            "community_id": row.community_id, "community_name": row.community_name,
            "collection_family": row.collection_family,
            "opening_count": row.opening_count, "added": row.added, "withdrawn": row.withdrawn,
            "transferred_in": row.transferred_in, "transferred_out": row.transferred_out,
            "closing_count": row.closing_count, "expected_closing": expected,
            "reconciliation_delta": difference, "data_status": status,
            "quality_note": row.quality_note,
            "is_latest": "TRUE" if row.period == analysis.periods[-1] else "FALSE",
        })

    latest = [{
        "period_date": f"{analysis.periods[-1]}-01", "community_id": row.community_id,
        "community_name": row.community_name, "current_total": row.current_total,
        "previous_total": row.previous_total, "change": row.change, "status": row.status,
    } for row in analysis.communities]

    exceptions = [{
        "period_date": f"{issue.period}-01", "period": issue.period,
        "community_id": issue.community_id, "collection_family": issue.collection_family,
        "kind": issue.kind, "detail": issue.detail,
    } for issue in analysis.issues]

    specs = {
        "network_monthly.csv": (tuple(network[0]), network),
        "community_family_monthly.csv": (tuple(detail[0]), detail),
        "community_latest.csv": (tuple(latest[0]), latest),
        "quality_issues.csv": (tuple(exceptions[0]), exceptions),
    }
    paths = {}
    for filename, (fields, rows) in specs.items():
        path = out_dir / filename
        write_csv(path, fields, rows)
        paths[filename] = path
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Export validated CSVs for Tableau Public authoring.")
    parser.add_argument("--ledger", type=Path, default=ROOT / "data/sample_ledger.csv")
    parser.add_argument("--start", default="2025-10")
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--out", type=Path, default=ROOT / "tableau/data")
    args = parser.parse_args()
    for name, path in export(args.ledger, args.out, start=args.start, months=args.months).items():
        print(f"[TABLEAU] {name}: {path}")


if __name__ == "__main__":
    main()

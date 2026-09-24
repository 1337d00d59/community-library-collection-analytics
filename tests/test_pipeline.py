from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_sample import build_rows, write_sample  # noqa: E402
from export_tableau import export  # noqa: E402
from ledger import analyze, load_records  # noqa: E402
from run_analysis import write_outputs  # noqa: E402


class PipelineTests(unittest.TestCase):
    def sample(self):
        return analyze(load_records(ROOT / "data" / "sample_ledger.csv"), start="2025-10", months=12)

    def test_fixture_reproducible_and_contains_real_zero_and_missing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "sample.csv"
            write_sample(output)
            self.assertEqual(output.read_bytes(), (ROOT / "data" / "sample_ledger.csv").read_bytes())
        self.assertEqual(len(build_rows()), 432)
        analysis = self.sample()
        zero = next(r for r in analysis.records if r.period == "2025-10" and
                    r.community_id == "INDI" and r.collection_family == "community_kits")
        self.assertEqual(zero.closing_count, 0)
        missing = [r for r in analysis.records if r.period == "2026-04" and r.community_id == "ECHO"]
        self.assertEqual(len(missing), 4)
        self.assertTrue(all(r.closing_count is None for r in missing))

    def test_reporting_gaps_and_reconciliation_are_explicit(self):
        analysis = self.sample()
        months = {row.period: row for row in analysis.monthly}
        self.assertIsNone(months["2026-04"].reported_total)
        self.assertEqual(months["2026-04"].status, "incomplete")
        self.assertEqual(months["2026-02"].status, "provisional")
        self.assertIsNone(months["2026-02"].withdrawn)
        self.assertIsNotNone(months["2026-02"].reported_total)
        self.assertEqual(months["2026-09"].reported_total, 264019)
        self.assertEqual(months["2026-09"].status, "provisional")
        mismatch = [i for i in analysis.issues if i.kind == "reconciliation_mismatch"]
        self.assertEqual(len(mismatch), 1)
        self.assertIn("difference +19", mismatch[0].detail)
        for row in analysis.monthly:
            if row.transferred_in is not None:
                self.assertEqual(row.transferred_in, row.transferred_out)

    def test_missing_row_and_duplicate_key_are_detected(self):
        records = load_records(ROOT / "data" / "sample_ledger.csv")
        with self.assertRaisesRegex(ValueError, "Duplicate ledger key"):
            analyze(records + [records[0]], start="2025-10", months=12)
        incomplete = analyze(records[1:], start="2025-10", months=12)
        self.assertTrue(any(i.kind == "missing_row" for i in incomplete.issues))
        self.assertIsNone(incomplete.monthly[0].reported_total)

    def test_latest_missing_closing_refuses_a_partial_board_view(self):
        records = load_records(ROOT / "data" / "sample_ledger.csv")
        latest = next(i for i, r in enumerate(records) if r.period == "2026-09")
        incomplete = analyze(records[:latest] + [replace(records[latest], closing_count=None)] + records[latest+1:],
                             start="2025-10", months=12)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "output"
            with self.assertRaisesRegex(ValueError, "Latest system total is incomplete"):
                write_outputs(incomplete, out)
            self.assertFalse(out.exists())

    def test_output_preserves_blank_instead_of_zero_and_renders_charts(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            write_outputs(self.sample(), folder)
            with (folder / "monthly_system.csv").open(newline="", encoding="utf-8") as file:
                rows = {r["period"]: r for r in csv.DictReader(file)}
            self.assertEqual(rows["2026-04"]["reported_total"], "")
            self.assertEqual(rows["2026-04"]["status"], "incomplete")
            self.assertEqual(rows["2026-09"]["reported_total"], "264019")
            brief = (folder / "board_brief.md").read_text(encoding="utf-8")
            self.assertIn("not actual library statistics", brief)
            self.assertIn("2026-04", brief)
            self.assertIn("difference +19", brief)
            charts = list((folder / "images").glob("*.png"))
            self.assertEqual(len(charts), 4)
            self.assertTrue(all(p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in charts))

    def test_invalid_counts_do_not_turn_into_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.csv"
            with (ROOT / "data" / "sample_ledger.csv").open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            rows[0]["closing_count"] = "NULL"
            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "nonnegative integer or blank"):
                load_records(path)

    def test_tableau_exports_preserve_safe_totals_and_issue_grain(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = export(ROOT / "data" / "sample_ledger.csv", Path(temp), start="2025-10", months=12)
            def read(name):
                with paths[name].open(newline="", encoding="utf-8") as handle:
                    return list(csv.DictReader(handle))
            months = {r["period"]: r for r in read("network_monthly.csv")}
            self.assertEqual(len(months), 12)
            self.assertEqual(months["2026-04"]["reported_total"], "")
            self.assertEqual(months["2026-04"]["reporting_status"], "incomplete")
            self.assertEqual(months["2026-09"]["reported_total"], "264019")
            self.assertEqual(months["2026-09"]["reporting_status"], "provisional")
            detail = read("community_family_monthly.csv")
            self.assertEqual(len(detail), 432)
            self.assertEqual(sum(r["closing_count"] == "" for r in detail), 4)
            self.assertEqual(sum(r["reconciliation_delta"] == "19" for r in detail), 1)
            self.assertEqual(len(read("community_latest.csv")), 9)
            self.assertEqual(len(read("quality_issues.csv")), 10)


if __name__ == "__main__":
    unittest.main()

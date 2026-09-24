"""Validate and summarize monthly collection-change records.

The input is a generic event ledger. A blank numeric field is unknown (None),
while a literal 0 is a known zero. Reports never fill missing values with zero.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

NUMERIC = ("opening_count", "added", "withdrawn", "transferred_in", "transferred_out", "closing_count")
REQUIRED = ("period", "community_id", "community_name", "collection_family", *NUMERIC, "quality_note")


@dataclass(frozen=True)
class Record:
    period: str
    community_id: str
    community_name: str
    collection_family: str
    opening_count: int | None
    added: int | None
    withdrawn: int | None
    transferred_in: int | None
    transferred_out: int | None
    closing_count: int | None
    quality_note: str

    @property
    def key(self) -> tuple[str, str, str]:
        return self.period, self.community_id, self.collection_family


@dataclass(frozen=True)
class Issue:
    period: str
    community_id: str
    collection_family: str
    kind: str
    detail: str


@dataclass(frozen=True)
class Monthly:
    period: str
    reported_total: int | None
    added: int | None
    withdrawn: int | None
    transferred_in: int | None
    transferred_out: int | None
    missing_closings: int
    issue_count: int
    status: str


@dataclass(frozen=True)
class Community:
    community_id: str
    community_name: str
    current_total: int | None
    previous_total: int | None
    change: int | None
    status: str
    mix: dict[str, int | None]


@dataclass(frozen=True)
class Analysis:
    periods: tuple[str, ...]
    families: tuple[str, ...]
    communities: tuple[Community, ...]
    monthly: tuple[Monthly, ...]
    issues: tuple[Issue, ...]
    records: tuple[Record, ...]


def month_number(period: str) -> int:
    try:
        year_text, month_text = period.split("-")
        year, month = int(year_text), int(month_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid YYYY-MM period: {period!r}") from exc
    if len(period) != 7 or not 1 <= month <= 12 or year < 1900:
        raise ValueError(f"Invalid YYYY-MM period: {period!r}")
    return year * 12 + month - 1


def month_label(number: int) -> str:
    return f"{number // 12:04d}-{number % 12 + 1:02d}"


def parse_count(raw: str | None, column: str, row_number: int) -> int | None:
    if raw is None or not raw.strip():
        return None
    if not raw.isdecimal():
        raise ValueError(f"Row {row_number}: {column} must be a nonnegative integer or blank; got {raw!r}")
    return int(raw)


def load_records(path: Path) -> list[Record]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(REQUIRED) <= set(reader.fieldnames):
            raise ValueError(f"Ledger must contain: {', '.join(REQUIRED)}")
        records = []
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Row {line}: unexpected extra CSV fields")
            period = (row["period"] or "").strip()
            month_number(period)
            values = {key: parse_count(row[key], key, line) for key in NUMERIC}
            code = (row["community_id"] or "").strip().upper()
            name = (row["community_name"] or "").strip()
            family = (row["collection_family"] or "").strip()
            if not code or not name or not family:
                raise ValueError(f"Row {line}: community ID, name, and collection family are required")
            records.append(Record(period, code, name, family,
                                  *(values[key] for key in NUMERIC), (row["quality_note"] or "").strip()))
    if not records:
        raise ValueError("Ledger contains no records")
    return records


def analyze(records: list[Record], *, start: str, months: int) -> Analysis:
    if months < 2:
        raise ValueError("At least two monthly periods are required")
    first = month_number(start)
    periods = tuple(month_label(first + i) for i in range(months))
    lookup: dict[tuple[str, str, str], Record] = {}
    names: dict[str, str] = {}
    for record in records:
        if record.period not in periods:
            raise ValueError(f"Record {record.key} is outside the requested reporting window")
        if record.key in lookup:
            raise ValueError(f"Duplicate ledger key: {record.key}")
        if record.community_id in names and names[record.community_id] != record.community_name:
            raise ValueError(f"Inconsistent community name for {record.community_id}")
        lookup[record.key] = record
        names[record.community_id] = record.community_name
    ids = tuple(sorted(names))
    families = tuple(sorted({record.collection_family for record in records}))
    issues: list[Issue] = []
    for period in periods:
        for cid in ids:
            for family in families:
                r = lookup.get((period, cid, family))
                if r is None:
                    issues.append(Issue(period, cid, family, "missing_row", "Expected community-family row is absent"))
                    continue
                if r.closing_count is None:
                    issues.append(Issue(period, cid, family, "missing_closing", r.quality_note or "Closing count was not reported"))
                if any(getattr(r, field) is None for field in NUMERIC[:-1]):
                    issues.append(Issue(period, cid, family, "incomplete_change_data", r.quality_note or "Opening or change field is missing"))
                else:
                    expected = r.opening_count + r.added - r.withdrawn + r.transferred_in - r.transferred_out
                    if r.closing_count is not None and expected != r.closing_count:
                        issues.append(Issue(period, cid, family, "reconciliation_mismatch",
                                            f"Observed {r.closing_count:,}; expected {expected:,}; difference {r.closing_count - expected:+,}"))
                if period != periods[0]:
                    previous = lookup.get((month_label(month_number(period) - 1), cid, family))
                    if previous and previous.closing_count is not None and r.opening_count is not None:
                        if previous.closing_count != r.opening_count:
                            issues.append(Issue(period, cid, family, "continuity_mismatch",
                                                f"Opening {r.opening_count:,} differs from previous closing {previous.closing_count:,}"))

    monthly = []
    for period in periods:
        rows = [lookup.get((period, cid, family)) for cid in ids for family in families]
        missing = sum(r is None or r.closing_count is None for r in rows)
        def total(column: str) -> int | None:
            if any(r is None or getattr(r, column) is None for r in rows):
                return None
            return sum(getattr(r, column) for r in rows)
        period_issues = [i for i in issues if i.period == period]
        added, withdrawn = total("added"), total("withdrawn")
        incoming, outgoing = total("transferred_in"), total("transferred_out")
        if incoming is not None and outgoing is not None and incoming != outgoing:
            period_issues.append(Issue(period, "SYSTEM", "all", "transfer_imbalance",
                                       f"Transfers in {incoming:,} differ from transfers out {outgoing:,}"))
            issues.append(period_issues[-1])
        monthly.append(Monthly(period, total("closing_count"), added, withdrawn, incoming,
                               outgoing, missing, len(period_issues),
                               "incomplete" if missing else "provisional" if period_issues else "complete"))

    communities = []
    for cid in ids:
        by_family = {family: lookup.get((periods[-1], cid, family)) for family in families}
        prev_rows = [lookup.get((periods[-2], cid, family)) for family in families]
        current_values = [r.closing_count if r else None for r in by_family.values()]
        previous_values = [r.closing_count if r else None for r in prev_rows]
        current = sum(current_values) if all(v is not None for v in current_values) else None
        previous = sum(previous_values) if all(v is not None for v in previous_values) else None
        current_issues = [i for i in issues if i.period == periods[-1] and i.community_id == cid]
        status = "incomplete" if current is None else "provisional" if current_issues else "complete"
        communities.append(Community(cid, names[cid], current, previous,
                                     current - previous if current is not None and previous is not None else None,
                                     status, dict(zip(families, current_values))))
    return Analysis(periods, families, tuple(communities), tuple(monthly), tuple(issues), tuple(records))

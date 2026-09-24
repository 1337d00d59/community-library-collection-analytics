#!/usr/bin/env python3
"""Generate a reproducible, entirely fictional collection-change ledger."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

COMMUNITIES = (
    ("ASTR", "Aster Hollow", 0.82),
    ("BRYK", "Bryn Creek", 1.16),
    ("CIRR", "Cirrus Landing", 0.94),
    ("DRFT", "Driftwood Vale", 1.36),
    ("ECHO", "Echo Meadow", 0.76),
    ("FERN", "Fernhaven", 1.09),
    ("GOLD", "Goldleaf Quay", 1.26),
    ("HUSH", "Hush River", 0.88),
    ("INDI", "Indigo Point", 1.03),
)
FAMILIES = (
    ("adult_print", 14500),
    ("youth_print", 9500),
    ("audio_video", 3800),
    ("community_kits", 520),
)
FIELDS = (
    "period", "community_id", "community_name", "collection_family",
    "opening_count", "added", "withdrawn", "transferred_in", "transferred_out",
    "closing_count", "quality_note",
)
PERIODS = tuple(f"{year}-{month:02d}" for year, months in ((2025, range(10, 13)), (2026, range(1, 10))) for month in months)


def build_rows(seed: int = 27021) -> list[dict[str, str]]:
    rng = random.Random(seed)
    state = {}
    for community_id, _name, scale in COMMUNITIES:
        for family, base in FAMILIES:
            variation = rng.uniform(.92, 1.08)
            state[community_id, family] = round(base * scale * variation)
    # A genuine observed zero is distinct from missing. A small collection
    # launches in a later month, so its initial zero is meaningful.
    state["INDI", "community_kits"] = 0

    rows: list[dict[str, str]] = []
    ids = [community_id for community_id, _, _ in COMMUNITIES]
    for period in PERIODS:
        transfers: dict[tuple[str, str], list[int]] = {(cid, family): [0, 0] for cid in ids for family, _ in FAMILIES}
        for family, _ in FAMILIES:
            for _ in range(2):
                donor, recipient = rng.sample(ids, 2)
                available = state[donor, family] - transfers[donor, family][1]
                amount = min(rng.randint(2, 17), max(0, available))
                transfers[donor, family][1] += amount
                transfers[recipient, family][0] += amount

        for community_id, community_name, _scale in COMMUNITIES:
            for family, _base in FAMILIES:
                opening = state[community_id, family]
                incoming, outgoing = transfers[community_id, family]
                added = rng.randint(0, max(3, round(opening * .014)))
                withdrawn = rng.randint(0, max(3, round(opening * .013)))
                if period == "2026-01" and (community_id, family) == ("ASTR", "adult_print"):
                    added += 280  # Fictional gift accession.
                if period == "2026-06" and (community_id, family) == ("GOLD", "youth_print"):
                    withdrawn += 340  # Fictional collection review.
                if period == "2025-11" and (community_id, family) == ("INDI", "community_kits"):
                    added += 72  # First kits arrive after an initial true zero.
                withdrawn = min(withdrawn, opening + added + incoming - outgoing)
                true_closing = opening + added - withdrawn + incoming - outgoing
                state[community_id, family] = true_closing

                quality_note = ""
                observed: int | str = true_closing
                if (period, community_id) == ("2026-04", "ECHO"):
                    # The report is absent. Latent state continues so the next
                    # month's independently observed opening can still exist.
                    opening = added = withdrawn = incoming = outgoing = observed = ""
                    quality_note = "report_not_received"
                elif (period, community_id, family) == ("2026-02", "CIRR", "audio_video"):
                    withdrawn = ""  # Closing is observed; one flow is unknown.
                    quality_note = "withdrawal_log_unavailable"
                elif (period, community_id, family) == ("2026-09", "GOLD", "youth_print"):
                    observed = true_closing + 19  # Deliberate reconciliation issue.
                    quality_note = "inventory_adjustment_pending"

                rows.append(dict(zip(FIELDS, (
                    period, community_id, community_name, family, opening, added, withdrawn,
                    incoming, outgoing, observed, quality_note,
                ))))
    return rows


def write_sample(path: Path, seed: int = 27021) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(build_rows(seed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an entirely fictional monthly event ledger.")
    parser.add_argument("--out", type=Path, default=Path("data/sample_ledger.csv"))
    parser.add_argument("--seed", type=int, default=27021)
    args = parser.parse_args()
    write_sample(args.out, args.seed)
    print(f"Wrote {len(PERIODS) * len(COMMUNITIES) * len(FAMILIES)} fictional records to {args.out}")

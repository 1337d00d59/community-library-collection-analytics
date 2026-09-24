"""Accessible static charts for a fictional collection-change ledger."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from ledger import Analysis

NAVY = "#17324D"
BLUE = "#326CA0"
TEAL = "#138B83"
AMBER = "#D6A13B"
CORAL = "#AD514D"
MUTED = "#526477"
GRID = "#E0E7ED"
FAMILY_COLORS = {"adult_print": BLUE, "youth_print": TEAL,
                 "audio_video": AMBER, "community_kits": CORAL}
FAMILY_LABELS = {"adult_print": "Adult print", "youth_print": "Youth print",
                 "audio_video": "Audio & video", "community_kits": "Community kits"}


def canvas(title: str, subtitle: str, *, size=(11.2, 6.0)):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.suptitle(title, x=.075, y=.98, ha="left", fontsize=18, fontweight="bold", color=NAVY)
    fig.text(.075, .91, subtitle, ha="left", fontsize=9.5, color=MUTED)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(length=0, labelcolor=NAVY, labelsize=9.5)
    ax.set_axisbelow(True)
    return fig, ax


def finish(fig, path: Path, *, left=.11, right=.96, bottom=.13, top=.84) -> None:
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top)
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def month_short(period: str) -> str:
    year, month = period.split("-")
    return f"{('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')[int(month)-1]} {year[-2:]}"


def render(analysis: Analysis, out_dir: Path) -> tuple[Path, ...]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = tuple(out_dir / name for name in (
        "system-trend.png", "community-holdings.png", "monthly-flows.png", "collection-mix.png"
    ))
    months = analysis.monthly
    labels = [month_short(m.period) for m in months]
    values = [m.reported_total for m in months]
    missing = [i for i, value in enumerate(values) if value is None]

    fig, ax = canvas("Observed holdings across the network",
                     "Fictional records  •  Shaded months have incomplete counts  •  Vertical axis starts above zero")
    for i in missing:
        ax.axvspan(i - .38, i + .38, color="#FDEAD4", zorder=0)
    ax.plot(range(len(values)), values, color=BLUE, linewidth=2.6, marker="o", markersize=5)
    valid = [value for value in values if value is not None]
    spread = max(valid) - min(valid)
    margin = max(spread * .35, max(valid) * .002)
    ax.set_ylim(min(valid) - margin, max(valid) + margin)
    ax.set_xticks(range(len(labels)), labels, rotation=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:,.1f}k"))
    ax.yaxis.grid(True, color=GRID)
    ax.set_ylabel("Observed items", color=NAVY, fontsize=9)
    for i in missing:
        ax.text(i, .93, "no total", transform=ax.get_xaxis_transform(), ha="center", fontsize=8, color="#814B1C")
    if months[-1].status != "complete" and values[-1] is not None:
        ax.scatter([len(values)-1], [values[-1]], s=105, facecolors="white", edgecolors=AMBER,
                   linewidths=2, zorder=4)
        ax.annotate("provisional", (len(values)-1, values[-1]), xytext=(-8, 13),
                    textcoords="offset points", ha="right", fontsize=8, color="#8B661E")
    finish(fig, paths[0])

    known = [c for c in analysis.communities if c.current_total is not None]
    ranked = sorted(known, key=lambda c: c.current_total)
    fig, ax = canvas("Current holdings by community",
                     f"{month_short(months[-1].period)}  •  Asterisk marks a provisional closing count")
    names = [f"{c.community_name} ({c.community_id})" + (" *" if c.status != "complete" else "") for c in ranked]
    bars = ax.barh(names, [c.current_total for c in ranked], color=BLUE, height=.67)
    ax.set_xlim(0, max(c.current_total for c in ranked) * 1.18)
    ax.bar_label(bars, labels=[f"{c.current_total:,}" for c in ranked], padding=5, fontsize=9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f}k"))
    ax.xaxis.grid(True, color=GRID)
    ax.set_xlabel("Observed items", fontsize=9)
    finish(fig, paths[1], left=.31)

    fig, ax = canvas("Items added and withdrawn",
                     "Fictional monthly flows  •  An absent bar means that flow was not reported")
    xs = list(range(len(months)))
    ax.bar([x - .19 for x in xs], [m.added if m.added is not None else float("nan") for m in months], width=.36, label="Added",
           color=TEAL, alpha=.96)
    ax.bar([x + .19 for x in xs], [m.withdrawn if m.withdrawn is not None else float("nan") for m in months], width=.36, label="Withdrawn",
           color=CORAL, alpha=.92)
    for i, m in enumerate(months):
        for offset, count in ((-.19, m.added), (.19, m.withdrawn)):
            if count is None:
                ax.text(i + offset, 30, "n/a", ha="center", va="bottom", rotation=90,
                        fontsize=8, color="#744A1E")
    ax.set_xticks(xs, labels)
    ax.yaxis.grid(True, color=GRID)
    ax.set_ylabel("Items recorded", fontsize=9)
    ax.legend(frameon=False, ncol=2, loc="upper left", fontsize=9)
    finish(fig, paths[2])

    fig, ax = canvas("Collection mix by community",
                     f"{month_short(months[-1].period)}  •  Four distinct categories, no subtotal overlap")
    left = [0] * len(ranked)
    family_order = tuple(f for f in ("adult_print", "youth_print", "audio_video", "community_kits") if f in analysis.families)
    family_order += tuple(f for f in analysis.families if f not in family_order)
    for family in family_order:
        counts = [c.mix[family] for c in ranked]
        if any(value is None for value in counts):
            raise ValueError("Collection mix requires a complete current count for each community")
        ax.barh(names, counts, left=left, color=FAMILY_COLORS.get(family, MUTED),
                label=FAMILY_LABELS.get(family, family.replace("_", " ").title()), height=.67)
        left = [a + b for a, b in zip(left, counts)]
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f}k"))
    ax.xaxis.grid(True, color=GRID)
    ax.set_xlabel("Observed items", fontsize=9)
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(.5, -.12), fontsize=8.5)
    finish(fig, paths[3], left=.31, bottom=.2)
    return paths

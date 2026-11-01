"""Draw the paper's figures and tables from the forecast outputs."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrocouncils import backtest, model
from metrocouncils.constants import METROS, PROCESSED_DIR, REPO_ROOT

FIGURES_DIR = REPO_ROOT / "reports" / "figures"
TABLES_DIR = REPO_ROOT / "reports" / "tables"
FORECAST_DIR = PROCESSED_DIR / "forecast"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
ANC = "#008300"
DA = "#2a78d6"
PARTY_COLOURS = {"ANC": ANC, "DA": DA}
PARTY_LABELS = {"ASA": "ActionSA", "FFP": "FF+", "OTHER": "Others"}
PARTY_ORDER = ("ANC", "DA", "EFF", "MK", "ASA", "PA", "FFP", "OTHER")
# Fundamentals and polls sit either side of the forecast line, so no marker hides another.
MARKER_OFFSET = 0.24
SCENARIO_LABELS = {
    "buf_no_borrowing": "No borrowing",
    "base": "Borrows Nelson Mandela Bay's shift (base)",
    "buf_borrows_all_metros": "Borrows all four polled metros' shift",
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.size": 9,
            "text.color": INK,
            "axes.labelcolor": SECONDARY,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.edgecolor": AXIS,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": SECONDARY,
            "ytick.color": SECONDARY,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.frameon": False,
        }
    )


def save(figure: plt.Figure, name: str, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        figure.savefig(folder / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(figure)


def probability_label(value: float) -> str:
    """Format a probability, never rounding a near-certainty to 100% or 0%."""
    if value > 0.99:
        return ">99%"
    return "<1%" if value < 0.01 else f"{value * 100:.0f}%"


def party_label(party: str) -> str:
    return PARTY_LABELS.get(party, party)


def seat_ranges(parties: pd.DataFrame, folder: Path) -> None:
    """Show each party's seats as a share of the council, against the majority line."""
    base = parties[parties["scenario"] == "base"]
    figure, grid = plt.subplots(2, 3, figsize=(7.6, 4.6), sharey=True, sharex=True)
    axes = grid.flatten()
    axes[-1].set_visible(False)
    rows = list(reversed(PARTY_ORDER))
    for axis, (metro, details) in zip(axes, METROS.items(), strict=False):
        table = base[base["metro"] == metro].set_index("party")
        scale = 100 / details["seats"]
        for row, party in enumerate(rows):
            colour = PARTY_COLOURS.get(party, MUTED)
            low, high = table.loc[party, ["seats_low", "seats_high"]] * scale
            axis.plot([low, high], [row, row], color=colour, linewidth=2, solid_capstyle="round")
            axis.plot(
                table.loc[party, "seats_median"] * scale,
                row,
                "o",
                color=colour,
                markersize=6,
                markeredgecolor=SURFACE,
                markeredgewidth=1.2,
            )
        needed = details["seats"] // 2 + 1
        axis.axvline(needed * scale, color=INK, linewidth=0.9)
        axis.set_title(details["name"], fontsize=9.5)
        axis.text(
            needed * scale + 1.5,
            0,
            f"Majority: {needed}",
            fontsize=7.5,
            color=SECONDARY,
            va="center",
        )
        axis.set_xlim(0, 80)
        axis.set_xticks([0, 25, 50, 75])
        axis.grid(axis="y", visible=False)
        axis.spines["left"].set_visible(False)
    for axis in grid[:, 0]:
        axis.set_yticks(range(len(rows)), [party_label(party) for party in rows])
    grid[0, 2].tick_params(labelbottom=True)
    figure.supxlabel("Share of council seats (%)", fontsize=9, color=SECONDARY)
    figure.tight_layout()
    save(figure, "figure_1_seat_ranges", folder)


def largest_party(parties: pd.DataFrame, councils: pd.DataFrame, folder: Path) -> None:
    """Show the probability that each party finishes as the single largest."""
    base = parties[parties["scenario"] == "base"]
    tied = councils[councils["scenario"] == "base"].set_index("metro")["p_tied_largest"]
    metros = list(reversed(list(METROS)))
    figure, axis = plt.subplots(figsize=(7.5, 2.9))
    for row, metro in enumerate(metros):
        table = base[base["metro"] == metro].set_index("party")["p_largest"]
        left = 0.0
        for name, value, colour in (
            ("ANC", table["ANC"], ANC),
            ("Tied for largest", tied[metro], MUTED),
            ("DA", table["DA"], DA),
        ):
            width = value * 100
            axis.barh(row, width - 0.4, left=left + 0.2, color=colour, height=0.55, label=name)
            if width >= 8:
                axis.text(
                    left + width / 2,
                    row,
                    probability_label(value),
                    ha="center",
                    va="center",
                    color="#ffffff",
                    fontsize=8.5,
                    fontweight="bold",
                )
            left += width
    axis.set_yticks(range(len(metros)), [METROS[metro]["name"] for metro in metros])
    axis.set_xlim(0, 100)
    axis.set_xlabel("Probability of finishing as the single largest party (%)")
    axis.grid(axis="y", visible=False)
    axis.spines["left"].set_visible(False)
    handles, labels = axis.get_legend_handles_labels()
    axis.legend(handles[:3], labels[:3], ncol=3, loc="lower center", bbox_to_anchor=(0.45, 1.0))
    figure.tight_layout()
    save(figure, "figure_2_largest_party", folder)


def polls_and_fundamentals(parties: pd.DataFrame, folder: Path) -> None:
    """Show where fundamentals, the polls and the forecast put the ANC and the DA."""
    summary = json.loads((PROCESSED_DIR / "backtest_2021.json").read_text(encoding="utf-8"))
    inputs = backtest.load_inputs()
    prior = model.fundamentals(inputs["local_2021"], inputs["national_2024"], summary["weight"])
    polls = model.clean_polls(pd.read_csv(REPO_ROOT / "data" / "external" / "polls.csv"))
    poll_means = np.exp(model.poll_summary(polls)[0])
    base = parties[parties["scenario"] == "base"]
    metros = list(reversed(list(METROS)))
    figure, axes = plt.subplots(1, 2, figsize=(8.5, 3.1), sharey=True, sharex=True)
    for axis, party in zip(axes, ("ANC", "DA"), strict=True):
        colour = PARTY_COLOURS[party]
        table = base[base["party"] == party].set_index("metro")
        for row, metro in enumerate(metros):
            low, high, median = table.loc[metro, ["share_low", "share_high", "share_median"]]
            axis.plot([low, high], [row, row], color=colour, linewidth=2, solid_capstyle="round")
            axis.plot(
                median,
                row,
                "o",
                color=colour,
                markersize=7,
                markeredgecolor=SURFACE,
                markeredgewidth=1.2,
                label="Forecast and 90% range",
            )
            axis.plot(
                prior.loc[metro, party] * 100,
                row + MARKER_OFFSET,
                "o",
                markerfacecolor=SURFACE,
                markeredgecolor=INK,
                markeredgewidth=1.1,
                markersize=6,
                linestyle="none",
                label="Fundamentals",
            )
            if metro in poll_means.index:
                axis.plot(
                    poll_means.loc[metro, party] * 100,
                    row - MARKER_OFFSET,
                    "D",
                    color=INK,
                    markersize=4.5,
                    linestyle="none",
                    label="Poll average",
                )
        axis.set_title(party)
        axis.set_xlabel("Share of votes (%)")
        axis.set_xlim(0, 70)
        axis.grid(axis="y", visible=False)
        axis.spines["left"].set_visible(False)
    axes[0].set_yticks(range(len(metros)), [METROS[metro]["name"] for metro in metros])
    handles, labels = axes[0].get_legend_handles_labels()
    unique = dict(zip(labels, handles, strict=True))
    figure.legend(
        unique.values(),
        unique.keys(),
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.55, -0.08),
    )
    figure.tight_layout()
    save(figure, "figure_3_polls_and_fundamentals", folder)


def backtest_scatter(folder: Path) -> None:
    """Plot the 2021 backtest: each dot is one party group in one metro."""
    table = pd.read_csv(PROCESSED_DIR / "backtest_2021_shares.csv", index_col="metro")
    groups = [group for group in model.GROUPS if table[f"{group}_actual"].sum() > 0]
    figure, axis = plt.subplots(figsize=(4.8, 4.5))
    axis.plot([0, 70], [0, 70], color=AXIS, linewidth=1)
    for group in groups:
        colour = PARTY_COLOURS.get(group, MUTED)
        axis.plot(
            table[f"{group}_predicted"],
            table[f"{group}_actual"],
            "o",
            color=colour,
            markersize=6,
            markeredgecolor=SURFACE,
            markeredgewidth=0.8,
            linestyle="none",
            clip_on=False,
            label=party_label(group) if group in PARTY_COLOURS else None,
        )
    others = [line for line in axis.lines if line.get_color() == MUTED]
    others[0].set_label("Other groups")
    worst = (table["ANC_predicted"] - table["ANC_actual"]).idxmax()
    axis.annotate(
        f"ANC, {METROS[worst]['name']}",
        (table.loc[worst, "ANC_predicted"], table.loc[worst, "ANC_actual"]),
        xytext=(0, -13),
        textcoords="offset points",
        ha="center",
        fontsize=8,
        color=SECONDARY,
    )
    miss = table["ASA_actual"].idxmax()
    axis.annotate(
        "ActionSA, Johannesburg: new party, not predicted",
        (table.loc[miss, "ASA_predicted"], table.loc[miss, "ASA_actual"]),
        xytext=(9, 4),
        textcoords="offset points",
        fontsize=8,
        color=SECONDARY,
    )
    axis.set_xlim(0, 70)
    axis.set_ylim(0, 70)
    axis.set_aspect("equal")
    axis.set_xlabel("Predicted 2021 share (%)")
    axis.set_ylabel("Actual 2021 share (%)")
    axis.legend(loc="upper left")
    figure.tight_layout()
    save(figure, "figure_4_backtest", folder)


def write_tables(
    parties: pd.DataFrame, councils: pd.DataFrame, coalitions: pd.DataFrame, folder: Path
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    base = parties[parties["scenario"] == "base"].copy()
    base["metro"] = base["metro"].map(lambda code: METROS[code]["name"])
    base["party"] = base["party"].map(party_label)
    base.drop(columns=["scenario"]).round(2).to_csv(
        folder / "table_forecast_by_party.csv", index=False, lineterminator="\n"
    )
    buffalo = councils[councils["metro"] == "BUF"].set_index("scenario")["p_hung"]
    sensitivity = pd.DataFrame(
        {
            "assumption": list(SCENARIO_LABELS.values()),
            "probability_no_majority": [buffalo[name] for name in SCENARIO_LABELS],
        }
    )
    sensitivity.round(3).to_csv(
        folder / "table_buffalo_city_sensitivity.csv", index=False, lineterminator="\n"
    )
    hung = councils.pivot(index="scenario", columns="metro", values="p_hung")[list(METROS)]
    hung.round(3).to_csv(folder / "table_hung_by_scenario.csv", lineterminator="\n")
    pairs = coalitions[(coalitions["scenario"] == "base") & (coalitions["size"] == 2)]
    pairs.drop(columns=["scenario", "size"]).sort_values(
        ["metro", "p_reaches_majority"], ascending=[True, False]
    ).round(3).to_csv(folder / "table_two_party_coalitions.csv", index=False, lineterminator="\n")


def run(figures: Path = FIGURES_DIR, tables: Path = TABLES_DIR) -> None:
    apply_style()
    parties = pd.read_csv(FORECAST_DIR / "parties.csv")
    councils = pd.read_csv(FORECAST_DIR / "councils.csv")
    coalitions = pd.read_csv(FORECAST_DIR / "coalitions.csv")
    seat_ranges(parties, figures)
    largest_party(parties, councils, figures)
    polls_and_fundamentals(parties, figures)
    backtest_scatter(figures)
    write_tables(parties, councils, coalitions, tables)


if __name__ == "__main__":
    run()

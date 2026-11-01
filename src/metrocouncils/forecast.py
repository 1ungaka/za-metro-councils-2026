"""Simulate the 2026 councils and summarise the outcomes."""

import itertools
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from metrocouncils import backtest, model
from metrocouncils.constants import METROS, PROCESSED_DIR, REPO_ROOT
from metrocouncils.seats import allocate_many, majority_threshold

SEED = 20261104
DRAWS = 200_000
VOTES_PER_DRAW = 1_000_000
SMALL_PARTY_CONCENTRATION = 50
COALITION_PARTIES = ("ANC", "DA", "EFF", "MK", "PA", "ASA", "FFP")
REPORT_THRESHOLD = 0.01
TIED = -1


@dataclass(frozen=True)
class Scenario:
    name: str
    use_polls: bool = True
    common_error: float = model.COMMON_POLL_ERROR
    # How Buffalo City, which has no poll, borrows from the polled metros.
    borrow_from: tuple[str, ...] = ("NMA",)


SCENARIOS = (
    Scenario("base"),
    Scenario("fundamentals_only", use_polls=False),
    Scenario("polls_trusted_more", common_error=0.05),
    Scenario("polls_trusted_less", common_error=0.20),
    Scenario("buf_no_borrowing", borrow_from=()),
    Scenario("buf_borrows_all_metros", borrow_from=("JHB", "TSH", "EKU", "NMA")),
)


def sole_largest(seats: np.ndarray) -> np.ndarray:
    """Return the column of each draw's single largest group, or TIED if the top seats tie."""
    leader = seats.argmax(axis=1)
    top_two = np.sort(seats, axis=1)[:, -2:]
    return np.where(top_two[:, 0] == top_two[:, 1], TIED, leader)


def small_party_mix(metro: str) -> pd.Series:
    """Return how OTHER splits between small parties, averaging 2021 and 2024 shares."""
    local = pd.read_csv(PROCESSED_DIR / "lge_party_votes.csv")
    national = pd.read_csv(PROCESSED_DIR / "npe_party_votes.csv")
    local = local[(local["year"] == 2021) & (local["metro"] == metro)]
    national = national[(national["year"] == 2024) & (national["metro"] == metro)]
    parts = []
    for frame, column in ((local, "combined_votes"), (national, "votes")):
        small = frame[frame["party"].map(model.group_of) == "OTHER"]
        values = small.groupby("party")[column].sum()
        parts.append(values / values.sum())
    mix = pd.concat(parts, axis=1).fillna(0).mean(axis=1)
    return mix[mix > 0]


def simulate_seats(
    shares: np.ndarray, metro: str, generator: np.random.Generator
) -> tuple[np.ndarray, list[str]]:
    """Split OTHER into its small parties and allocate seats for every draw.

    Returns seats by group, with all small parties summed in OTHER.
    """
    mix = small_party_mix(metro)
    split = generator.dirichlet(mix.to_numpy() * SMALL_PARTY_CONCENTRATION, size=len(shares))
    other_index = model.GROUPS.index("OTHER")
    named = np.delete(shares, other_index, axis=1)
    small = shares[:, [other_index]] * split
    votes = np.hstack([named, small]) * VOTES_PER_DRAW
    seats = allocate_many(votes, METROS[metro]["seats"])
    named_seats = seats[:, : named.shape[1]]
    other_seats = seats[:, named.shape[1] :].sum(axis=1, keepdims=True)
    return np.hstack([named_seats, other_seats]), [*model.GROUPS[:other_index], "OTHER"]


def run_scenario(scenario: Scenario, inputs: dict, summary: dict) -> tuple[list, list, list]:
    generator = np.random.default_rng(SEED)
    weight = summary["weight"]
    scales = summary["prior_scales"]
    prior = model.fundamentals(inputs["local_2021"], inputs["national_2024"], weight)
    prior_logs = np.log(prior.clip(lower=model.SHARE_FLOOR))

    polls = model.clean_polls(pd.read_csv(REPO_ROOT / "data" / "external" / "polls.csv"))
    means, counts, spread = model.poll_summary(polls)
    shift = (means - prior_logs.loc[means.index, list(model.GROUPS)]).reindex(columns=model.GROUPS)

    council_rows, party_rows, coalition_rows = [], [], []
    for metro, details in METROS.items():
        prior_mean = prior_logs.loc[metro, list(model.GROUPS)]
        has_poll = scenario.use_polls and metro in means.index
        if metro == "BUF" and scenario.use_polls and scenario.borrow_from:
            prior_mean = prior_mean + shift.loc[list(scenario.borrow_from)].mean().fillna(0)
        mean, scale = model.posterior(
            prior_mean,
            scales,
            means.loc[metro] if has_poll else None,
            counts.loc[metro] if has_poll else None,
            spread,
            scenario.common_error,
        )
        shares = model.draw_shares(mean, scale, DRAWS, generator)
        seats, groups = simulate_seats(shares, metro, generator)
        need = majority_threshold(details["seats"])
        leader = sole_largest(seats)
        council_rows.append(
            {
                "scenario": scenario.name,
                "metro": metro,
                "seats": details["seats"],
                "majority_needed": need,
                "p_hung": float((seats.max(axis=1) < need).mean()),
                "p_tied_largest": float((leader == TIED).mean()),
            }
        )
        for index, group in enumerate(groups):
            party_rows.append(
                {
                    "scenario": scenario.name,
                    "metro": metro,
                    "party": group,
                    "share_median": float(np.median(shares[:, index]) * 100),
                    "share_low": float(np.quantile(shares[:, index], 0.05) * 100),
                    "share_high": float(np.quantile(shares[:, index], 0.95) * 100),
                    "seats_median": float(np.median(seats[:, index])),
                    "seats_low": float(np.quantile(seats[:, index], 0.05)),
                    "seats_high": float(np.quantile(seats[:, index], 0.95)),
                    "p_largest": float((leader == index).mean()) if group != "OTHER" else 0.0,
                    "p_majority": float((seats[:, index] >= need).mean()),
                }
            )
        positions = {group: groups.index(group) for group in COALITION_PARTIES}
        for size in (2, 3):
            for members in itertools.combinations(COALITION_PARTIES, size):
                total = seats[:, [positions[member] for member in members]].sum(axis=1)
                probability = float((total >= need).mean())
                if probability >= REPORT_THRESHOLD:
                    coalition_rows.append(
                        {
                            "scenario": scenario.name,
                            "metro": metro,
                            "coalition": "+".join(members),
                            "size": size,
                            "p_reaches_majority": probability,
                        }
                    )
    return council_rows, party_rows, coalition_rows


def run() -> None:
    inputs = backtest.load_inputs()
    summary = json.loads((PROCESSED_DIR / "backtest_2021.json").read_text(encoding="utf-8"))
    results = [run_scenario(scenario, inputs, summary) for scenario in SCENARIOS]
    outputs = PROCESSED_DIR / "forecast"
    outputs.mkdir(parents=True, exist_ok=True)
    for position, name in enumerate(("councils", "parties", "coalitions")):
        rows = [row for result in results for row in result[position]]
        pd.DataFrame(rows).round(4).to_csv(
            outputs / f"{name}.csv", index=False, lineterminator="\n"
        )


if __name__ == "__main__":
    run()

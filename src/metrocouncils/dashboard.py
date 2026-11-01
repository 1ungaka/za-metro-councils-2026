"""Export the current numbers as the small tables behind the stats dashboard."""

import json

import numpy as np
import pandas as pd

from metrocouncils import backtest, model
from metrocouncils.constants import METROS, PROCESSED_DIR, REPO_ROOT
from metrocouncils.figures import FORECAST_DIR, SCENARIO_LABELS, party_label, probability_label

OUTPUT_DIR = REPO_ROOT / "reports" / "dashboard"
METHOD_LABELS = {
    "mae_blend": "Blend of local and national results",
    "mae_national_2019_only": "National result only",
    "mae_no_change_from_2016": "Last local result only",
}


def write(frame: pd.DataFrame, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT_DIR / f"{name}.csv", index=False, lineterminator="\n")


def metro_table(parties: pd.DataFrame, councils: pd.DataFrame) -> pd.DataFrame:
    base = parties[parties["scenario"] == "base"].set_index(["metro", "party"])
    council = councils[councils["scenario"] == "base"].set_index("metro")
    rows = []
    for code, details in METROS.items():
        no_majority = council.loc[code, "p_hung"]
        anc = base.loc[(code, "ANC"), "p_largest"]
        da = base.loc[(code, "DA"), "p_largest"]
        tied = council.loc[code, "p_tied_largest"]
        rows.append(
            {
                "metro": details["name"],
                "seats": details["seats"],
                "majority_needed": council.loc[code, "majority_needed"],
                "p_no_majority": no_majority,
                "p_anc_largest": anc,
                "p_da_largest": da,
                "p_tied": tied,
                "no_majority_label": probability_label(no_majority),
                "anc_largest_label": probability_label(anc),
                "da_largest_label": probability_label(da),
                "tied_label": probability_label(tied),
            }
        )
    return pd.DataFrame(rows)


def party_table(parties: pd.DataFrame) -> pd.DataFrame:
    base = parties[parties["scenario"] == "base"].copy()
    base["metro"] = base["metro"].map(lambda code: METROS[code]["name"])
    base["party"] = base["party"].map(party_label)
    columns = ["metro", "party", "share_median", "share_low", "share_high"]
    columns += ["seats_median", "seats_low", "seats_high"]
    table = base[columns].round(1)
    seats = ["seats_median", "seats_low", "seats_high"]
    table[seats] = table[seats].round().astype(int)
    return table


def source_comparison(parties: pd.DataFrame, summary: dict) -> pd.DataFrame:
    inputs = backtest.load_inputs()
    prior = model.fundamentals(inputs["local_2021"], inputs["national_2024"], summary["weight"])
    polls = model.clean_polls(pd.read_csv(REPO_ROOT / "data" / "external" / "polls.csv"))
    poll_means = np.exp(model.poll_summary(polls)[0])
    base = parties[parties["scenario"] == "base"].set_index(["metro", "party"])
    rows = []
    for code, details in METROS.items():
        for party in ("ANC", "DA"):
            forecast = base.loc[(code, party)]
            has_poll = code in poll_means.index
            rows.append(
                {
                    "metro": details["name"],
                    "party": party,
                    "fundamentals": round(prior.loc[code, party] * 100, 1),
                    "poll_average": round(poll_means.loc[code, party] * 100, 1)
                    if has_poll
                    else None,
                    "forecast": round(forecast["share_median"], 1),
                    "low": round(forecast["share_low"], 1),
                    "high": round(forecast["share_high"], 1),
                }
            )
    return pd.DataFrame(rows)


def buffalo_table(councils: pd.DataFrame) -> pd.DataFrame:
    buffalo = councils[councils["metro"] == "BUF"].set_index("scenario")["p_hung"]
    return pd.DataFrame(
        {
            "assumption": list(SCENARIO_LABELS.values()),
            "probability": [round(buffalo[name] * 100, 1) for name in SCENARIO_LABELS],
        }
    )


def coalition_table(coalitions: pd.DataFrame) -> pd.DataFrame:
    base = coalitions[(coalitions["scenario"] == "base") & (coalitions["size"] == 2)].copy()
    base["metro"] = base["metro"].map(lambda code: METROS[code]["name"])
    base["coalition"] = base["coalition"].map(
        lambda text: " + ".join(party_label(part) for part in text.split("+"))
    )
    base["chance"] = base["p_reaches_majority"].map(probability_label)
    base = base.sort_values(["metro", "p_reaches_majority"], ascending=[True, False])
    return base[["metro", "coalition", "chance"]]


def backtest_table(summary: dict) -> pd.DataFrame:
    rows = [
        {"kind": "method", "label": label, "mae": round(summary[key], 2)}
        for key, label in METHOD_LABELS.items()
    ]
    rows += [
        {"kind": "metro", "label": METROS[code]["name"], "mae": round(value, 2)}
        for code, value in summary["mae_by_metro"].items()
    ]
    rows += [
        {"kind": "party", "label": party_label(group), "mae": round(value, 2)}
        for group, value in summary["mae_by_group"].items()
        if group != "MK"
    ]
    return pd.DataFrame(rows)


def validation_table() -> pd.DataFrame:
    record = pd.read_csv(PROCESSED_DIR / "seat_validation.csv")
    record["metro"] = record["metro"].map(lambda code: METROS[code]["name"])
    record["result"] = record["passed"].map({True: "Exact match", False: "Differs"})
    record["council"] = record["metro"] + " " + record["year"].astype(str)
    return record[["council", "metro", "year", "result"]]


def fieldwork_label(period: str) -> str:
    """Turn 2026-08-25/09-17 into 25 Aug to 17 Sep."""
    start, end = period.split("/")
    first = pd.Timestamp(start)
    last = pd.Timestamp(f"{first.year}-{end}")
    return f"{first.day} {first:%b} to {last.day} {last:%b}"


def poll_table() -> pd.DataFrame:
    polls = pd.read_csv(REPO_ROOT / "data" / "external" / "polls.csv")
    polls["metro"] = polls["metro"].map(lambda code: METROS[code]["name"])
    polls["poll"] = polls["metro"] + ", " + polls["pollster"]
    polls["fieldwork"] = polls["fieldwork"].map(fieldwork_label)
    columns = ["poll", "metro", "pollster", "fieldwork", "sample", "voter_base"]
    return polls[[*columns, "ANC", "DA", "MK", "EFF", "ASA"]]


def run() -> None:
    parties = pd.read_csv(FORECAST_DIR / "parties.csv")
    councils = pd.read_csv(FORECAST_DIR / "councils.csv")
    coalitions = pd.read_csv(FORECAST_DIR / "coalitions.csv")
    summary = json.loads((PROCESSED_DIR / "backtest_2021.json").read_text(encoding="utf-8"))
    write(metro_table(parties, councils), "metro_forecast")
    write(party_table(parties), "party_forecast")
    write(source_comparison(parties, summary), "source_comparison")
    write(buffalo_table(councils), "buffalo_sensitivity")
    write(coalition_table(coalitions), "coalitions")
    write(backtest_table(summary), "backtest")
    write(validation_table(), "seat_validation")
    write(poll_table(), "polls")


if __name__ == "__main__":
    run()

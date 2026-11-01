"""Build the metro vote tables and check them against the IEC's seat reports."""

import pandas as pd

from metrocouncils.constants import (
    INDEPENDENT,
    METROS,
    PR_BALLOT,
    PROCESSED_DIR,
    RAW_DIR,
    WARD_BALLOT,
)
from metrocouncils.parse import read_lge, read_npe, read_seat_report
from metrocouncils.seats import allocate

LGE_YEARS = (2016, 2021)
NPE_YEARS = (2019, 2024)


def iec_folder(name: str):
    return RAW_DIR / "iec" / name


def load_lge(year: int) -> pd.DataFrame:
    codes = tuple(METROS)
    frames = [
        read_lge(iec_folder(f"lge{year}") / f"{province}.csv", codes)
        for province in sorted({metro["province"] for metro in METROS.values()})
    ]
    return pd.concat(frames, ignore_index=True)


def ward_winners(detailed: pd.DataFrame) -> pd.DataFrame:
    """Count ward wins per metro and party.

    The IEC's file labels every independent candidate INDEPENDENT, so several candidates in a
    ward cannot be told apart. Adding them up could invent a winner, as it would in Buffalo City
    ward 44 in 2021, so independents are left out. The seat reports show none won in these metros.
    """
    ward = detailed[(detailed["ballot"] == WARD_BALLOT) & (detailed["party"] != INDEPENDENT)]
    totals = ward.groupby(["metro", "ward", "party"], as_index=False)["votes"].sum()
    winners = totals.sort_values("votes").groupby(["metro", "ward"]).tail(1)
    counts = winners.groupby(["metro", "party"]).size()
    return counts.rename("ward_wins").reset_index()


def party_votes(detailed: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return PR, ward and combined votes for each party with a PR list.

    Independents and parties that stood only in wards are left out, as they are from the IEC's
    seat calculation: its total of valid votes counts only parties on the PR ballot.
    """
    listed = detailed.loc[detailed["ballot"] == PR_BALLOT, ["metro", "party"]].drop_duplicates()
    parties = detailed[detailed["party"] != INDEPENDENT].merge(listed, on=["metro", "party"])
    wide = parties.pivot_table(
        index=["metro", "party"], columns="ballot", values="votes", aggfunc="sum", fill_value=0
    ).reset_index()
    table = pd.DataFrame(
        {
            "year": year,
            "metro": wide["metro"],
            "party": wide["party"],
            "pr_votes": wide[PR_BALLOT].astype(int),
            "ward_votes": wide[WARD_BALLOT].astype(int),
        }
    )
    table["combined_votes"] = table["pr_votes"] + table["ward_votes"]
    wins = ward_winners(detailed)
    table = table.merge(wins, on=["metro", "party"], how="left")
    table["ward_wins"] = table["ward_wins"].fillna(0).astype(int)
    return table


def turnout_inputs(detailed: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return registered voters and valid PR votes for each metro."""
    pr_rows = detailed[detailed["ballot"] == PR_BALLOT]
    districts = pr_rows.drop_duplicates(["metro", "ward", "voting_district"])
    frame = pd.DataFrame(
        {
            "registered": districts.groupby("metro")["registered"].sum(),
            "pr_valid_votes": pr_rows.groupby("metro")["votes"].sum(),
        }
    )
    return frame.reset_index().assign(year=year)


def check_against_report(table: pd.DataFrame, year: int, metro: str) -> list[str]:
    """Rebuild a council from the votes and return every difference from the IEC's report."""
    header, report = read_seat_report(iec_folder(f"lge{year}") / f"seats_{metro}.xls")
    report = report.set_index("party")
    ours = table[(table["year"] == year) & (table["metro"] == metro)].set_index("party")
    problems = []

    total = int(ours["combined_votes"].sum())
    if total != header["total_votes"]:
        problems.append(f"total votes {total} against {header['total_votes']}")
    joined = report.join(ours["combined_votes"], how="outer").fillna(0)
    differing = joined[joined["votes"] != joined["combined_votes"]]
    if not differing.empty:
        problems.append(f"{len(differing)} parties differ on votes, e.g. {differing.index[0]}")

    aligned = report.sort_index()
    result = allocate(
        aligned["votes"].to_numpy(),
        header["seats"],
        header["independents"],
        header["no_list_seats"],
    )
    if result.quota != header["quota"]:
        problems.append(f"quota {result.quota} against {header['quota']}")
    for name, values in (
        ("round one", result.round_one),
        ("round two", result.round_two),
        ("seats", result.seats),
    ):
        column = name.replace(" ", "_")
        wrong = aligned.index[values != aligned[column].to_numpy()]
        if len(wrong):
            problems.append(f"{name} differs for {len(wrong)} parties, e.g. {wrong[0]}")
    return problems


def build() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    lge, turnout = [], []
    for year in LGE_YEARS:
        detailed = load_lge(year)
        lge.append(party_votes(detailed, year))
        turnout.append(turnout_inputs(detailed, year))
    table = pd.concat(lge, ignore_index=True)
    table.to_csv(PROCESSED_DIR / "lge_party_votes.csv", index=False, lineterminator="\n")
    pd.concat(turnout, ignore_index=True).to_csv(
        PROCESSED_DIR / "lge_turnout_inputs.csv", index=False, lineterminator="\n"
    )

    national = [
        read_npe(iec_folder(f"npe{year}") / "National.zip", tuple(METROS)).assign(year=year)
        for year in NPE_YEARS
    ]
    pd.concat(national, ignore_index=True)[["year", "metro", "party", "votes"]].to_csv(
        PROCESSED_DIR / "npe_party_votes.csv", index=False, lineterminator="\n"
    )

    rows = []
    for year in LGE_YEARS:
        for metro in METROS:
            problems = check_against_report(table, year, metro)
            rows.append(
                {
                    "year": year,
                    "metro": metro,
                    "passed": not problems,
                    "problems": "; ".join(problems),
                }
            )
    record = pd.DataFrame(rows)
    record.to_csv(PROCESSED_DIR / "seat_validation.csv", index=False, lineterminator="\n")
    print(record.to_string(index=False))


if __name__ == "__main__":
    build()

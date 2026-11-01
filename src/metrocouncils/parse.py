"""Parse the IEC's detailed results files and its seat calculation reports."""

import io
import re
import zipfile
from pathlib import Path

import pandas as pd
import xlrd

LGE_COLUMNS = ["Municipality", "Ward", "VotingDistrict", "BallotType", "PartyName"]
LGE_NUMBERS = ["RegisteredVoters", "SpoiltVotes", "TotalValidVotes"]


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def municipality_code(label: str) -> str:
    return clean_text(label).split(" - ", 1)[0]


def read_lge(path: Path, codes: tuple[str, ...]) -> pd.DataFrame:
    """Read a local election file, keeping only the named municipalities."""
    raw = pd.read_csv(
        path, encoding="utf-8-sig", usecols=LGE_COLUMNS + LGE_NUMBERS, low_memory=False
    )
    raw["metro"] = raw["Municipality"].map(municipality_code)
    raw = raw[raw["metro"].isin(codes)]
    return pd.DataFrame(
        {
            "metro": raw["metro"],
            "ward": raw["Ward"],
            "voting_district": raw["VotingDistrict"],
            "ballot": raw["BallotType"],
            "party": raw["PartyName"].map(clean_text),
            "votes": raw["TotalValidVotes"],
            "registered": raw["RegisteredVoters"],
            "spoilt": raw["SpoiltVotes"],
        }
    )


def _rejoin_station_name(fields: list[str]) -> list[str]:
    """Repair a 2019 row whose voting station name holds unquoted commas.

    The name is the fourth field, and the six fields after it never hold commas.
    """
    return [*fields[:3], ",".join(fields[3:-6]), *fields[-6:]]


def read_npe(path: Path, codes: tuple[str, ...]) -> pd.DataFrame:
    """Read a national ballot file and total the votes per municipality and party."""
    with zipfile.ZipFile(path) as archive:
        name = next(item for item in archive.namelist() if item.lower().endswith(".csv"))
        try:
            with archive.open(name) as handle:
                raw = pd.read_csv(handle, encoding="utf-8-sig", low_memory=False)
        except pd.errors.ParserError:
            with archive.open(name) as handle:
                raw = pd.read_csv(
                    handle,
                    encoding="utf-8-sig",
                    encoding_errors="replace",
                    engine="python",
                    on_bad_lines=_rejoin_station_name,
                )
    # The 2019 and 2024 files spell these columns differently (sPartName, sPartyName).
    party_column = next(column for column in raw.columns if column.startswith("sPart"))
    votes_column = next(
        column for column in raw.columns if column.replace("_", " ") == "Party Votes"
    )
    raw["metro"] = raw["Municipality"].map(municipality_code)
    raw = raw[raw["metro"].isin(codes)]
    raw = raw.assign(party=raw[party_column].map(clean_text).str.upper(), votes=raw[votes_column])
    return raw.groupby(["metro", "party"], as_index=False)["votes"].sum()


def read_seat_report(path: Path) -> tuple[dict[str, int], pd.DataFrame]:
    """Read a Seat Calculation Detail report into its header values and its party table."""
    book = xlrd.open_workbook(path, logfile=io.StringIO())
    sheet = book.sheet_by_index(0)
    rows = [sheet.row_values(index) for index in range(sheet.nrows)]

    labels = {
        "quota": "Quota - (Q)",
        "total_votes": "Total Valid Votes Cast for All Parties - (A)",
        "seats": "Total Seats Available in Municipality - (B)",
        "independents": "Independent Ward Councillors Elected - (C)",
        "no_list_seats": "Ward Councillors Seats from Parties with no PR List - (D)",
    }
    header_values = {}
    for row in rows:
        text = [cell for cell in row if cell != ""]
        for key, label in labels.items():
            if text and clean_text(text[0]) == label:
                header_values[key] = int(text[1])

    start = next(
        index
        for index, row in enumerate(rows)
        if any(clean_text(cell) == "Party Name" for cell in row)
    )
    names = {clean_text(cell): index for index, cell in enumerate(rows[start]) if cell != ""}
    columns = {
        "party": names["Party Name"],
        "votes": names["Total Valid Votes"],
        "round_one": names["Round 1 Allocation"],
        "surplus": names["Remainder"],
        "round_two": names["Round 2 Allocation"],
        "seats": names["Total Party Seats"],
    }
    records = []
    for row in rows[start + 1 :]:
        party = clean_text(row[columns["party"]])
        if not party or party == "Total" or party.startswith(("Page", "Printed")):
            continue
        records.append(
            {
                "party": party,
                "votes": int(row[columns["votes"]]),
                "round_one": int(row[columns["round_one"]] or 0),
                "surplus": float(row[columns["surplus"]] or 0),
                "round_two": int(row[columns["round_two"]] or 0),
                "seats": int(row[columns["seats"]] or 0),
            }
        )
    return header_values, pd.DataFrame(records)

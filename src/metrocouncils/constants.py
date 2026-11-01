"""Fixed facts about the metros, the elections and the file layout."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "MANIFEST.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# Ward counts for 2021 and 2026 were read from the IEC's own results page, and they match.
# Seats are read from the IEC's 2021 seat reports, and are double the ward count.
METROS = {
    "JHB": {"name": "Johannesburg", "province": "GP", "wards": 135, "seats": 270},
    "TSH": {"name": "Tshwane", "province": "GP", "wards": 107, "seats": 214},
    "EKU": {"name": "Ekurhuleni", "province": "GP", "wards": 112, "seats": 224},
    "NMA": {"name": "Nelson Mandela Bay", "province": "EC", "wards": 60, "seats": 120},
    "BUF": {"name": "Buffalo City", "province": "EC", "wards": 50, "seats": 100},
}

# The IEC's electoral event ids, from its results download pages.
LGE_EVENTS = {2016: 402, 2021: 1091, 2026: 1887}
NPE_EVENTS = {2019: 699, 2024: 1334}

PR_BALLOT = "PR"
WARD_BALLOT = "Ward"
INDEPENDENT = "INDEPENDENT"

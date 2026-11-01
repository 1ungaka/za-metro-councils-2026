"""Download the IEC files for the five metros.

Files are stored byte for byte in data/raw/iec and recorded in data/raw/MANIFEST.csv. If a
download fails, the error names the exact file and URL so it can be fetched by hand.
"""

import argparse
import csv
import hashlib
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests

from metrocouncils.constants import LGE_EVENTS, MANIFEST_PATH, METROS, NPE_EVENTS, RAW_DIR

BASE = "https://results.elections.org.za/home"
MAIN_SITE = "https://www.elections.org.za/content/NPEPublicReports"
USER_AGENT = "za-metro-councils-2026 research download"
MANIFEST_FIELDS = ("file", "url", "sha256", "bytes", "downloaded_utc")
RETRIES = 6
MINIMUM_BYTES = 1000


class MissingSourceError(RuntimeError):
    """A source file is not available. The message says what to fetch and where to put it."""


@dataclass(frozen=True)
class Source:
    relative_path: str
    url: str

    @property
    def destination(self) -> Path:
        return RAW_DIR / "iec" / self.relative_path


def _url(*parts: str) -> str:
    return "/".join([BASE, *(quote(str(part)) for part in parts)])


def lge_sources(year: int) -> list[Source]:
    event = LGE_EVENTS[year]
    root = ("LGEPublicReports", event)
    sources = [
        Source(
            f"lge{year}/{province}.csv",
            _url(*root, "Downloadable Party Results", f"{province}.csv"),
        )
        for province in sorted({metro["province"] for metro in METROS.values()})
    ]
    sources += [
        Source(
            f"lge{year}/seats_{code}.xls",
            _url(*root, "Seat Calculation Detail", metro["province"], f"{code}.xls"),
        )
        for code, metro in METROS.items()
    ]
    return sources


def npe_sources(year: int) -> list[Source]:
    event = NPE_EVENTS[year]
    if year == 2019:
        # The results page links the 2019 archive from the IEC's main site.
        url = f"{MAIN_SITE}/{event}/Downloadable%20Results/National.zip"
    else:
        url = _url("NPEPublicReports", event, "National Ballot", "Downloadable Results")
        url += "/National.zip"
    return [Source(f"npe{year}/National.zip", url)]


def all_sources() -> list[Source]:
    return [
        *lge_sources(2016),
        *lge_sources(2021),
        *npe_sources(2019),
        *npe_sources(2024),
    ]


def looks_complete(path: Path) -> bool:
    """Reject a missing file, or an error page saved under a data file's name."""
    if not path.exists():
        return False
    if path.suffix == ".zip":
        return zipfile.is_zipfile(path)
    return path.stat().st_size > MINIMUM_BYTES


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["file"]: row for row in csv.DictReader(handle)}


def save_manifest(rows: dict[str, dict[str, str]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows[key] for key in sorted(rows))


def fetch(source: Source, session: requests.Session, pause: float = 10.0) -> bytes:
    """Return a file's bytes, retrying the 5xx errors the IEC site gives under load."""
    failure = "no response"
    for attempt in range(RETRIES):
        try:
            response = session.get(source.url, timeout=300)
        except requests.RequestException as error:
            failure = str(error)
        else:
            kind = response.headers.get("content-type", "")
            if response.ok and "text/html" not in kind and "text/plain" not in kind:
                return response.content
            failure = f"HTTP {response.status_code} ({kind})"
            if response.status_code == 404:
                break
        time.sleep(pause * (attempt + 1))
    raise MissingSourceError(
        f"Could not download {source.relative_path}: {failure}.\n"
        f"  Source: {source.url}\n"
        f"  Save it by hand to: {source.destination}"
    )


def download_all(force: bool = False) -> list[str]:
    """Fetch every file and return any that no longer match the manifest."""
    manifest = load_manifest()
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    mismatches = []
    for source in all_sources():
        path = source.destination
        if force or not looks_complete(path):
            content = fetch(source, session)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        digest = sha256_of(path)
        known = manifest.get(source.relative_path)
        if known and known["sha256"] != digest:
            mismatches.append(source.relative_path)
        elif not known:
            manifest[source.relative_path] = {
                "file": source.relative_path,
                "url": source.url,
                "sha256": digest,
                "bytes": str(path.stat().st_size),
                "downloaded_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            save_manifest(manifest)
    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        mismatches = download_all(force=args.force)
    except MissingSourceError as error:
        print(error, file=sys.stderr)
        return 1
    if mismatches:
        print("These files differ from the manifest:", *mismatches, file=sys.stderr)
        return 1
    print("All files present and matching the manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

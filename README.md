# Hung Councils in Five South African Metros, 2026

A probabilistic forecast of council outcomes in Johannesburg, Tshwane, Ekurhuleni, Nelson Mandela
Bay and Buffalo City for the 4 November 2026 Local Government Elections.

**Status: working forecast, not yet frozen.**

## What it does

1. Applies South Africa's exact council seat rule, which rebuilds all ten official IEC seat reports
   for these metros in 2016 and 2021.
2. Models vote shares as compositional data, combining past results with published polls.
3. Simulates 200,000 elections per metro to estimate the chance of no majority, the likely largest
   party, and which coalitions could reach a majority.

## Reproduce

Requires Python 3.11 or later and `make`.

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
make setup
```

```bash
make all
```

This downloads the IEC files, rebuilds the tables, reruns the backtest and forecast, and redraws
the figures. Raw IEC files are not redistributed, because of the IEC's copyright notice.

## Where things are

| Path | Contents |
| --- | --- |
| `docs/PAPER.pdf` and `docs/PAPER.md` | The paper |
| `docs/DECISIONS.md` | Every modelling judgement, and known weaknesses |
| `docs/HAND_CHECK.md` | Worked examples of the seat rule and model |
| `docs/FREEZE_CHECKLIST.md` | Steps to freeze the forecast |
| `data/external/polls.csv` | The polls used, with sources |
| `reports/figures` and `reports/tables` | Figures and tables |
| `src/metrocouncils` | The code |

## Data sources

- Electoral Commission of South Africa, results for the 2016 and 2021 local elections and the 2019
  and 2024 national elections.
- Local Government: Municipal Structures Act 117 of 1998, Schedule 1.
- Published polls, listed in `data/external/polls.csv`.

## Author

Lunga Ngaka, University of Fort Hare.

## Licence

Code is under the [MIT licence](LICENSE). Source data remains the property of its publishers.

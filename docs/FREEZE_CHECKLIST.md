# Freeze Checklist

Do this on Tuesday 3 November 2026, and finish before polls open on 4 November. After step 6, the
forecast does not change.

1. Check for polls published since the last update. Add any new ones to `data/external/polls.csv`,
   with their sample and source.
2. Rerun everything: `make backtest forecast figures dashboard test`.
3. Update the numbers in `docs/PAPER.md`, change its status line, and rebuild it with `make paper`.
4. Refresh the dashboard from `reports/dashboard/`.
5. Record the final choices in `docs/DECISIONS.md`.
6. Commit, then tag: `git tag -a v1.0-forecast -m "Forecast frozen before polls open"`.
7. Push the commit and the tag.
8. Make the record public and timestamped. A private repo cannot prove the date. Either upload the
   paper and a zip of the tagged code to Zenodo, or make the repo public, or both.
9. Open the public link while logged out, and confirm the forecast and the date are visible.

After the results are declared, do not edit the frozen files. Score the forecast using Section 9 of
the paper, in new files.

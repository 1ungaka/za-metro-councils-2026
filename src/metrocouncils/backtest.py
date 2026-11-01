"""Backtest the fundamentals on 2021, using only the 2016 local and 2019 national results."""

import json

import numpy as np
import pandas as pd

from metrocouncils import model
from metrocouncils.constants import METROS, PROCESSED_DIR

WEIGHT_GRID = np.round(np.arange(0, 1.01, 0.05), 2)


def load_inputs() -> dict[str, pd.DataFrame]:
    local = pd.read_csv(PROCESSED_DIR / "lge_party_votes.csv")
    national = pd.read_csv(PROCESSED_DIR / "npe_party_votes.csv")
    return {
        "local_2016": model.group_shares(local[local["year"] == 2016], "combined_votes"),
        "local_2021": model.group_shares(local[local["year"] == 2021], "combined_votes"),
        "national_2019": model.group_shares(national[national["year"] == 2019], "votes"),
        "national_2024": model.group_shares(national[national["year"] == 2024], "votes"),
    }


def run() -> dict:
    inputs = load_inputs()
    earlier, national, actual = (
        inputs["local_2016"],
        inputs["national_2019"],
        inputs["local_2021"],
    )
    weight = model.choose_weight(earlier, national, actual, WEIGHT_GRID)
    predicted = model.fundamentals(earlier, national, weight)
    errors = model.log_errors(predicted, actual)
    cross_validated, metro_weights = model.leave_one_metro_out(
        earlier, national, actual, WEIGHT_GRID
    )
    scales = model.prior_scales(errors)

    present = (predicted.sum() > 0) | (actual.sum() > 0)
    by_metro = (predicted - actual).loc[:, present].abs().mean(axis=1) * 100
    results = {
        "weight": weight,
        "mae_blend": model.share_mae(predicted, actual),
        "mae_blend_leave_one_metro_out": cross_validated,
        "weights_leave_one_metro_out": metro_weights,
        "mae_no_change_from_2016": model.share_mae(earlier, actual),
        "mae_national_2019_only": model.share_mae(national, actual),
        "mae_by_metro": by_metro.reindex(list(METROS)).to_dict(),
        "mae_by_group": ((predicted - actual).abs().mean() * 100).to_dict(),
        "prior_scales": scales,
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "backtest_2021.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    columns = {f"{group}_predicted": predicted[group] * 100 for group in model.GROUPS}
    columns |= {f"{group}_actual": actual[group] * 100 for group in model.GROUPS}
    pd.DataFrame(columns).round(3).to_csv(
        PROCESSED_DIR / "backtest_2021_shares.csv", lineterminator="\n"
    )
    return results


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

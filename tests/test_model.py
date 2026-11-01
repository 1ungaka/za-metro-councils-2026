"""Model tests. Expected values are worked by hand or follow from the formulas."""

import numpy as np
import pandas as pd
import pytest

from metrocouncils import model


def frame(rows: dict[str, dict[str, float]]) -> pd.DataFrame:
    table = pd.DataFrame(rows).T.reindex(columns=list(model.GROUPS)).fillna(0.0)
    return table.rename_axis("metro")


def test_group_of_maps_names_and_sends_the_rest_to_other():
    assert model.group_of("African National Congress") == "ANC"
    assert model.group_of("uMkhonto weSizwe") == "MK"
    assert model.group_of("AL JAMA-AH") == "OTHER"


def test_fundamentals_blend_and_close():
    local = frame({"A": {"ANC": 0.6, "DA": 0.4}})
    national = frame({"A": {"ANC": 0.4, "DA": 0.6}})
    result = model.fundamentals(local, national, 0.5)
    assert result.loc["A", "ANC"] == pytest.approx(0.5)
    assert result.loc["A", "DA"] == pytest.approx(0.5)


def test_new_party_keeps_its_share_rather_than_being_halved():
    local = frame({"A": {"ANC": 0.6, "DA": 0.4}})
    national = frame({"A": {"ANC": 0.5, "DA": 0.3, "MK": 0.2}})
    raw = model.fundamentals(local, national, 0.5)
    # Before closing: ANC 0.55, DA 0.35, MK 0.20, which sum to 1.10.
    assert raw.loc["A", "MK"] == pytest.approx(0.20 / 1.10)
    assert raw.loc["A", "ANC"] == pytest.approx(0.55 / 1.10)


def test_share_mae_ignores_empty_groups():
    predicted = frame({"A": {"ANC": 0.5, "DA": 0.5}})
    actual = frame({"A": {"ANC": 0.4, "DA": 0.6}})
    assert model.share_mae(predicted, actual) == pytest.approx(10.0)


def test_choose_weight_finds_the_exact_blend():
    local = frame({"A": {"ANC": 0.8, "DA": 0.2}})
    national = frame({"A": {"ANC": 0.4, "DA": 0.6}})
    actual = model.fundamentals(local, national, 0.25)
    assert model.choose_weight(local, national, actual, np.arange(0, 1.01, 0.25)) == 0.25


def test_clean_polls_rebases_a_complete_poll_without_dont_knows():
    poll = pd.DataFrame(
        [
            {
                "metro": "A",
                "pollster": "X",
                "ANC": 40,
                "DA": 30,
                "MK": 5,
                "EFF": 5,
                "PA": 3,
                "ASA": 3,
                "FFP": 2,
                "IFP": 2,
                "OTHERS": 0,
                "DK": 10,
            }
        ]
    )
    result = model.clean_polls(poll).iloc[0]
    assert result["ANC"] == pytest.approx(40 / 90)
    assert result["OTHER"] == pytest.approx(2 / 90)


def test_clean_polls_leaves_a_partial_poll_as_published():
    poll = pd.DataFrame(
        [
            {
                "metro": "A",
                "pollster": "X",
                "ANC": 22,
                "DA": 36,
                "MK": 11,
                "EFF": 6,
                "PA": np.nan,
                "ASA": 9,
                "FFP": np.nan,
                "IFP": np.nan,
                "OTHERS": np.nan,
                "DK": np.nan,
            }
        ]
    )
    result = model.clean_polls(poll).iloc[0]
    assert result["ANC"] == pytest.approx(0.22)
    assert np.isnan(result["PA"])
    assert np.isnan(result["OTHER"])


def test_posterior_is_the_precision_weighted_mean():
    groups = list(model.GROUPS)
    prior = pd.Series(np.log(0.4), index=groups)
    poll = pd.Series(np.log(0.2), index=groups)
    scales = dict.fromkeys(groups, 0.3)
    counts = pd.Series(1.0, index=groups)
    spread = pd.Series(0.3, index=groups)
    mean, scale = model.posterior(prior, scales, poll, counts, spread, common_error=0.0)
    # Equal variances, so the mean is halfway and the variance halves.
    assert mean["ANC"] == pytest.approx((np.log(0.4) + np.log(0.2)) / 2)
    assert scale["ANC"] == pytest.approx(0.3 / np.sqrt(2))


def test_posterior_without_polls_returns_the_prior():
    groups = list(model.GROUPS)
    prior = pd.Series(np.log(0.1), index=groups)
    mean, scale = model.posterior(
        prior, dict.fromkeys(groups, 0.25), None, None, pd.Series(0.1, index=groups)
    )
    assert mean["DA"] == pytest.approx(np.log(0.1))
    assert scale["DA"] == pytest.approx(0.25)


def test_group_missing_from_a_poll_stays_at_its_prior():
    groups = list(model.GROUPS)
    prior = pd.Series(np.log(0.1), index=groups)
    poll = pd.Series(np.log(0.5), index=groups)
    counts = pd.Series(1.0, index=groups)
    counts["PA"] = 0
    mean, scale = model.posterior(
        prior, dict.fromkeys(groups, 0.25), poll, counts, pd.Series(0.1, index=groups), 0.1
    )
    assert mean["PA"] == pytest.approx(np.log(0.1))
    assert scale["PA"] == pytest.approx(0.25)


def test_draws_stay_on_the_simplex():
    groups = list(model.GROUPS)
    mean = pd.Series(np.log(1 / len(groups)), index=groups)
    scale = pd.Series(0.5, index=groups)
    shares = model.draw_shares(mean, scale, 1000, np.random.default_rng(3))
    assert (shares > 0).all()
    assert shares.sum(axis=1) == pytest.approx(np.ones(1000))

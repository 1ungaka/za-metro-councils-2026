"""The vote model: fundamentals, poll update and simulation.

Each step works on party vote shares s_j, which are compositional: they are positive and sum to
one. Errors are therefore added to log s_j, and each draw is closed back to the simplex by
dividing by its sum. This is a logistic-normal model.

1. Fundamentals. With y the last local result and z the latest national result,
       f_j = w y_j + (1 - w) z_j
   A party absent from one of the two elections takes its share from the other.
2. Poll update. With m_j = log f_j and prior variance a_j^2, and a poll average with log share
   p_j and variance b_j^2, the posterior is normal with
       precision = 1/a_j^2 + 1/b_j^2
       mean = (m_j/a_j^2 + p_j/b_j^2) / precision
3. Simulation. Draw log shares from the posterior, close, and apply the exact seat rule.
"""

import numpy as np
import pandas as pd

GROUPS = ("ANC", "DA", "EFF", "MK", "PA", "ASA", "FFP", "OTHER")
ESTABLISHED = ("ANC", "DA", "EFF", "FFP")
PARTY_NAMES = {
    "AFRICAN NATIONAL CONGRESS": "ANC",
    "DEMOCRATIC ALLIANCE": "DA",
    "ECONOMIC FREEDOM FIGHTERS": "EFF",
    "UMKHONTO WESIZWE": "MK",
    "PATRIOTIC ALLIANCE": "PA",
    "ACTIONSA": "ASA",
    "VRYHEIDSFRONT PLUS": "FFP",
}
# Shares are floored here before taking logs, as a party can have zero votes.
SHARE_FLOOR = 0.001
# Polling error common to all pollsters, which their spread cannot reveal. This is an assumption.
COMMON_POLL_ERROR = 0.10
COMPLETE_POLL_MINIMUM = 95


def group_of(party: str) -> str:
    return PARTY_NAMES.get(party.upper(), "OTHER")


def group_shares(table: pd.DataFrame, votes_column: str) -> pd.DataFrame:
    """Return each metro's vote share by group, one row per metro and one column per group."""
    grouped = table.assign(group=table["party"].map(group_of))
    wide = grouped.pivot_table(
        index="metro", columns="group", values=votes_column, aggfunc="sum", fill_value=0
    ).reindex(columns=list(GROUPS), fill_value=0)
    return wide.div(wide.sum(axis=1), axis=0)


def close(frame: pd.DataFrame) -> pd.DataFrame:
    """Rescale each row to sum to one."""
    return frame.div(frame.sum(axis=1), axis=0)


def fundamentals(local: pd.DataFrame, national: pd.DataFrame, weight: float) -> pd.DataFrame:
    """Blend the last local and latest national results, keeping any new party's share."""
    blended = weight * local + (1 - weight) * national
    blended = blended.where((local > 0) & (national > 0), local + national)
    return close(blended)


def share_mae(predicted: pd.DataFrame, actual: pd.DataFrame) -> float:
    """Return the mean absolute error in percentage points.

    Groups absent from both tables are left out, so an empty column cannot flatter the score.
    """
    present = (predicted.sum() > 0) | (actual.sum() > 0)
    return float((predicted - actual).loc[:, present].abs().to_numpy().mean() * 100)


def log_errors(predicted: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    return np.log(actual.clip(lower=SHARE_FLOOR)) - np.log(predicted.clip(lower=SHARE_FLOOR))


def choose_weight(
    local: pd.DataFrame, national: pd.DataFrame, actual: pd.DataFrame, grid: np.ndarray
) -> float:
    """Return the weight with the smallest share error."""
    scores = [share_mae(fundamentals(local, national, value), actual) for value in grid]
    return float(grid[int(np.argmin(scores))])


def leave_one_metro_out(
    local: pd.DataFrame, national: pd.DataFrame, actual: pd.DataFrame, grid: np.ndarray
) -> tuple[float, dict[str, float]]:
    """Choose the weight without each metro, then score that metro. Returns MAE and weights."""
    errors, weights = [], {}
    for metro in actual.index:
        others = actual.index != metro
        weight = choose_weight(local[others], national[others], actual[others], grid)
        weights[metro] = weight
        predicted = fundamentals(local[~others], national[~others], weight)
        present = (actual.sum() > 0) | (predicted.sum() > 0)
        errors.append((predicted - actual[~others]).loc[:, present].abs().to_numpy())
    return float(np.mean(errors) * 100), weights


def prior_scales(errors: pd.DataFrame) -> dict[str, float]:
    """Set the prior spread of each group's log share from the backtest.

    Parties present in the backtest use their pooled root mean square log error. New and small
    parties use the error of OTHER, the group that held the backtest's surprise new entrant.
    """
    established = errors[list(ESTABLISHED)].to_numpy()
    established_scale = float(np.sqrt(np.mean(established**2)))
    other_scale = float(np.sqrt(np.mean(errors["OTHER"].to_numpy() ** 2)))
    return {
        group: established_scale if group in ESTABLISHED else max(other_scale, established_scale)
        for group in GROUPS
    }


def clean_polls(polls: pd.DataFrame) -> pd.DataFrame:
    """Convert polls to group shares, one row per poll.

    Polls covering nearly all voters are rebased to exclude don't-knows. Others list only the
    main parties, so their figures stand as published and unlisted groups stay missing.
    """
    parts = polls[["ANC", "DA", "MK", "EFF", "PA", "ASA", "FFP", "IFP", "OTHERS"]]
    listed = parts.sum(axis=1)
    complete = listed >= COMPLETE_POLL_MINIMUM - polls["DK"].fillna(0)
    out = polls[["metro", "pollster", "sample"]].copy()
    other = parts["OTHERS"].fillna(0) + parts["IFP"].fillna(0)
    shares = parts.drop(columns=["IFP", "OTHERS"]).assign(OTHER=other.where(other > 0))
    base = listed.where(complete, 100)
    shares = shares.div(base, axis=0)
    return pd.concat([out, shares], axis=1)


def poll_summary(polls: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Summarise the polls by metro, weighting each poll by its sample size.

    Returns the weighted mean log shares, the effective number of polls and the
    between-pollster spread per group. With weights w, the effective number is
    (sum w)^2 / sum w^2, so one large poll beside a small one counts for little more than one.
    """
    groups = list(GROUPS)
    logs = polls.copy()
    logs[groups] = np.log(polls[groups].clip(lower=SHARE_FLOOR))
    weights = logs[groups].notna().mul(polls["sample"], axis=0)
    total = weights.groupby(logs["metro"]).sum()
    squares = (weights**2).groupby(logs["metro"]).sum()
    means = (logs[groups] * weights).groupby(logs["metro"]).sum() / total.replace(0, np.nan)
    effective = (total**2 / squares.replace(0, np.nan)).fillna(0)

    counts = logs.groupby("metro")[groups].count()
    variance = logs.groupby("metro")[groups].var(ddof=1)
    freedom = (counts - 1).clip(lower=0)
    pooled = (variance.fillna(0) * freedom).sum() / freedom.sum().replace(0, np.nan)
    spread = np.sqrt(pooled).fillna(np.sqrt(pooled).mean())
    return means, effective, spread


def posterior(
    prior_mean: pd.Series,
    prior_scale: dict[str, float],
    poll_mean: pd.Series | None,
    poll_count: pd.Series | None,
    spread: pd.Series,
    common_error: float = COMMON_POLL_ERROR,
) -> tuple[pd.Series, pd.Series]:
    """Combine the prior and the polls, returning the mean and sd of each group's log share."""
    prior_precision = pd.Series({group: prior_scale[group] ** -2 for group in GROUPS})
    if poll_mean is None:
        return prior_mean, prior_precision**-0.5
    count = poll_count.reindex(GROUPS).fillna(0)
    variance = spread.reindex(GROUPS) ** 2 / count.clip(lower=1) + common_error**2
    poll_precision = (1 / variance).where(count > 0, 0.0)
    precision = prior_precision + poll_precision
    mean = prior_mean * prior_precision + poll_mean.reindex(GROUPS).fillna(0) * poll_precision
    return mean / precision, precision**-0.5


def draw_shares(
    mean: pd.Series, scale: pd.Series, draws: int, generator: np.random.Generator
) -> np.ndarray:
    """Draw from the logistic-normal posterior. Each row is one simulated election."""
    logs = generator.normal(mean.to_numpy(), scale.to_numpy(), size=(draws, len(mean)))
    shares = np.exp(logs)
    return shares / shares.sum(axis=1, keepdims=True)

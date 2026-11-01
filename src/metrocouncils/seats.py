"""Seat allocation for a metro council, following Schedule 1 of the Municipal Structures Act.

Items 12 and 13 work from each party's combined votes on the PR and ward ballots. With A the
combined votes for all parties, B the council seats, C the independent ward councillors and D
the ward seats of parties with no PR list, the IEC's quota is

    Q = floor(A / (B - C - D)) + 1

Each party gets floor(votes / Q) seats. Remaining seats go to the largest surpluses, and an
equal surplus goes to the party with more votes. Term D comes from the IEC's published seat
reports. It is not in the 2009 text of the Act, so an amendment must have added it.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Allocation:
    quota: int
    round_one: np.ndarray
    surplus: np.ndarray
    round_two: np.ndarray
    seats: np.ndarray


def quota(total_votes: int, seats: int, independents: int = 0, no_list_seats: int = 0) -> int:
    """Return the votes needed for a seat. Python's // is exact, so no rounding error enters."""
    available = seats - independents - no_list_seats
    if available <= 0:
        raise ValueError("No seats are left to allocate")
    return total_votes // available + 1


def allocate(
    votes: list[int] | np.ndarray,
    seats: int,
    independents: int = 0,
    no_list_seats: int = 0,
) -> Allocation:
    """Allocate seats from each party's whole-number combined votes."""
    counts = np.asarray(votes, dtype=np.int64)
    if (counts < 0).any():
        raise ValueError("Votes cannot be negative")
    available = seats - independents - no_list_seats
    seat_quota = quota(int(counts.sum()), seats, independents, no_list_seats)
    round_one = counts // seat_quota
    whole_remainder = counts % seat_quota
    left = available - int(round_one.sum())
    # Sort by surplus, then votes, both descending. Whole remainders avoid float comparison.
    order = np.lexsort((-counts, -whole_remainder))
    round_two = np.zeros_like(counts)
    round_two[order[:left]] = 1
    return Allocation(
        quota=seat_quota,
        round_one=round_one,
        surplus=whole_remainder / seat_quota,
        round_two=round_two,
        seats=round_one + round_two,
    )


def allocate_many(votes: np.ndarray, seats: int) -> np.ndarray:
    """Allocate seats for many simulated elections at once.

    `votes` has one row per simulation and one column per party. Simulated votes are fractional,
    so exact ties do not arise and the tie-break on votes is not needed here.
    """
    totals = votes.sum(axis=1, keepdims=True)
    seat_quota = np.floor(totals / seats) + 1
    entitlement = votes / seat_quota
    whole = np.floor(entitlement).astype(np.int64)
    left = seats - whole.sum(axis=1)
    surplus_rank = np.argsort(np.argsort(-(entitlement - whole), axis=1), axis=1)
    return whole + (surplus_rank < left[:, None]).astype(np.int64)


def list_seats(total_seats: np.ndarray, ward_wins: np.ndarray) -> np.ndarray:
    """Return each party's PR list seats. Under item 16 a list share is never negative."""
    return np.maximum(np.asarray(total_seats) - np.asarray(ward_wins), 0)


def majority_threshold(seats: int) -> int:
    """Return the seats needed for an outright majority of the council."""
    return seats // 2 + 1

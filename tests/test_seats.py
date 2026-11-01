"""Seat allocation tests. Every expected value here was worked out by hand."""

import numpy as np
import pytest

from metrocouncils.seats import allocate, allocate_many, list_seats, majority_threshold, quota


def test_quota_disregards_fractions_then_adds_one():
    assert quota(1000, 10) == 101
    assert quota(1005, 10) == 101
    assert quota(1009, 10) == 101


def test_quota_of_an_exact_division_still_adds_one():
    assert quota(100, 4) == 26


def test_quota_removes_independent_and_no_list_seats():
    # 900 / (10 - 1 - 2) = 128.57, so 129.
    assert quota(900, 10, independents=1, no_list_seats=2) == 129


def test_quota_rejects_a_council_with_no_seats_left():
    with pytest.raises(ValueError):
        quota(100, 2, independents=2)


def test_worked_example():
    # Q = 1000 // 10 + 1 = 101.
    # 480/101 = 4 r 76, 350/101 = 3 r 47, 120/101 = 1 r 19, 50/101 = 0 r 50.
    # Eight seats are placed, so two go to the largest remainders, 76 and 50.
    result = allocate([480, 350, 120, 50], 10)
    assert result.quota == 101
    assert result.round_one.tolist() == [4, 3, 1, 0]
    assert result.round_two.tolist() == [1, 0, 0, 1]
    assert result.seats.tolist() == [5, 3, 1, 1]


def test_small_party_wins_a_seat_on_its_remainder_alone():
    assert allocate([960, 40], 2).seats.tolist() == [2, 0]
    # Q = 301. 700 gets 2 r 98, and 200 gets 0 r 200, so the one seat left goes to the 200.
    assert allocate([700, 200], 3).seats.tolist() == [2, 1]


def test_equal_surplus_goes_to_the_party_with_more_votes():
    # Q = 601 // 3 + 1 = 201. Remainders: 351 is 1 r 150, 150 is 0 r 150, 100 is 0 r 100.
    # One seat is placed and two remain. The 351 and the 150 share the top remainder.
    result = allocate([150, 351, 100], 3)
    assert result.round_one.tolist() == [0, 1, 0]
    assert result.seats.tolist() == [1, 2, 0]


def test_tie_break_order_does_not_depend_on_party_position():
    # Q = 601 // 2 + 1 = 301. Remainders are 200 and 200 after one seat for the 501.
    # 501 has more votes, so it takes the last seat whichever column it sits in.
    assert allocate([501, 100], 2).seats.tolist() == [2, 0]
    assert allocate([100, 501], 2).seats.tolist() == [0, 2]


def test_all_seats_are_always_filled():
    generator = np.random.default_rng(1)
    for _ in range(200):
        seats = int(generator.integers(5, 300))
        votes = generator.integers(0, 50_000, size=int(generator.integers(2, 30)))
        if votes.sum() == 0:
            continue
        assert allocate(votes, seats).seats.sum() == seats


def test_independents_reduce_the_seats_allocated_to_parties():
    assert allocate([500, 500], 10, independents=2).seats.sum() == 8


def test_negative_votes_are_rejected():
    with pytest.raises(ValueError):
        allocate([10, -1], 3)


def test_list_seats_subtract_ward_wins():
    assert list_seats([5, 3], [2, 3]).tolist() == [3, 0]


def test_item_16_a_party_with_excess_wards_gets_no_list_seats():
    assert list_seats([2], [4]).tolist() == [0]


@pytest.mark.parametrize(("seats", "needed"), [(120, 61), (100, 51), (270, 136), (214, 108)])
def test_majority_threshold(seats, needed):
    assert majority_threshold(seats) == needed


def test_simulated_allocation_agrees_with_the_exact_rule():
    generator = np.random.default_rng(2)
    votes = generator.integers(1, 200_000, size=(500, 12)).astype(float)
    fast = allocate_many(votes, 120)
    for index in range(len(votes)):
        exact = allocate(votes[index].astype(np.int64), 120).seats
        assert fast[index].tolist() == exact.tolist()

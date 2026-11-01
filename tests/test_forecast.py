import numpy as np

from metrocouncils.forecast import TIED, sole_largest


def test_sole_largest_finds_a_clear_leader():
    assert sole_largest(np.array([[10, 40, 5]])).tolist() == [1]


def test_a_tie_for_first_is_not_given_to_either_party():
    assert sole_largest(np.array([[45, 45, 30], [30, 45, 45]])).tolist() == [TIED, TIED]


def test_a_tie_below_first_does_not_matter():
    assert sole_largest(np.array([[50, 20, 20]])).tolist() == [0]

"""Tests for the shared helpers."""
import random

import numpy as np

from src import utils


def test_set_seed_makes_python_and_numpy_repeatable():
    """The same seed gives the same random numbers from both libraries."""
    utils.set_seed(42)
    first = (random.random(), float(np.random.rand()))
    utils.set_seed(42)
    assert (random.random(), float(np.random.rand())) == first

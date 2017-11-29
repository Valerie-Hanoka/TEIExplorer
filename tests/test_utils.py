#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_utils.py is part of the project TEIExplorer
Author: Valérie Hanoka

"""

from nose.tools import *

from teiexplorer.utils.utils import(
    merge_two_dicts,
    merge_and_append_dicts,
    sum_dicts
)

def test_utils_merge_two_dicts():
    """Merge two dict values: Should pass"""

    x = {'both': 'both_x', 'only_x': 'only_x'}
    y = {'both': 'both_y', 'only_y': 'only_y'}
    merged = merge_two_dicts(x, y)
    truth = {
        'both': 'both_x',
        'only_x': 'only_x',
        'only_y': 'only_y'
    }
    assert cmp(merged, truth) == 0


def test_utils_merge_and_append_dicts():
    """Merge & append dict values: Should pass"""

    x = {'both1': 'botha1x', 'both2': 'botha2x', 'only_x': 'only_x'}
    y = {'both1': 'botha1y', 'both2': 'botha2y', 'only_y': 'only_y'}
    merged = merge_and_append_dicts(x, y)
    truth = {
        'both1': ['botha1x', 'botha1y'],
        'both2': ['botha2x', 'botha2y'],
        'only_x': ['only_x'],
        'only_y': ['only_y']
    }

    assert cmp(merged, truth) == 0


def test_utils_sum_dicts():
    """
    Merge and sum a list of dict values: Should pass .
    """

    x = {'both1': 1, 'both2': 2, 'only_x': 100}
    y = {'both1': 10, 'both2': 20, 'only_y': 200}
    summed = sum_dicts(x, y)
    truth = {
        'both1': 11,
        'both2': 22,
        'only_x': 100,
        'only_y': 200
    }

    assert cmp(summed, truth) == 0

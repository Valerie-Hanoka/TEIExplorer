#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_utils.py is part of the project TEIExplorer
Author: Valérie Hanoka

"""

from nose.tools import *

from teiexplorer.utils.utils import(
    merge_two_dicts,
    sum_dicts,
    flatten_nested_dict_to_pairs
)

def test_utils_merge_two_dicts1():
    """Recursive merge & append dict values: Should pass"""

    dic_y = {'both': {'both_y_diff': 'bar', 'both_same': 'same_y'}, 'only_y': 'only_y'}
    dic_x = {'both': {'both_x_diff': 'foo', 'both_same': 'same_x'}, 'only_x': {'only_x': 'baz'}}
    merged = merge_two_dicts(dic_x, dic_y)

    truth = {
        'both': {'both_same': ['same_x', 'same_y'],
                 'both_x_diff': 'foo',
                 'both_y_diff': 'bar'},
        'only_x': {'only_x': 'baz'},
        'only_y': 'only_y'
    }
    assert cmp(merged, truth) == 0


def test_utils_merge_two_dicts2():
    """Recursive merge & append dict values: Should pass"""

    x = {'both1': 'botha1x', 'both2': 'botha2x', 'only_x': 'only_x'}
    y = {'both1': 'botha1y', 'both2': 'botha2y', 'only_y': 'only_y'}
    merged = merge_two_dicts(x, y)
    truth = {
        'both1': ['botha1x', 'botha1y'],
        'both2': ['botha2x', 'botha2y'],
        'only_x': 'only_x',
        'only_y': 'only_y'
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


def test_utils_flatten_nested_dict_to_pairs():
    """
    Flatten the path of a nested dict for all the dict values: Should pass
    """
    nested_dict = {'k1': {'ka' : 'v1', 'kb': {u'kα': 'v2'}}, 'k2': 'v3'}
    flattened = flatten_nested_dict_to_pairs(nested_dict)
    truth = [(u'k2', 'v3'), (u'k1_kb_kα', 'v2'), (u'k1_ka', 'v1')]

    assert flattened == truth

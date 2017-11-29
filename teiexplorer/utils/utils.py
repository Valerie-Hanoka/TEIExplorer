#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict


def merge_two_dicts(x, y):
    """Given two dicts (with string keys),
    merge them into a new dict as a shallow copy.
    x values override y values in cases of duplicate keys.
    Ex.:
    >>> x = {'both': 'both_x', 'only_x': 'only_x'}
    >>> y = {'both': 'both_y', 'only_y': 'only_y'}
    >>> merge_two_dicts(x, y)
    >>> {'both': 'both_x', 'only_x': 'only_x', 'only_y': 'only_y'}
    :param x: First dictionary (master)
    :param y: Second dictionary (slave)
    :return: The merge of x and y, keeping x values in case of conflicts."""
    return dict(y, **x)

def merge_and_append_dicts(*dicts):
    """
    Merge a list of dictionaries by appending values with common keys
    in a list .
    Ex:
    >>> x = {'both1':'botha1x', 'both2':'botha2x', 'only_x': 'only_x'  }
    >>> y = {'both1':'botha1y', 'both2': 'botha2y', 'only_y': 'only_y' }
    >>> merge_and_append_dicts(x, y)
    >>> {'both1': ['botha1x', 'botha1y'], 'both2': ['botha2x', 'botha2y'], 'only_x': ['only_x'], 'only_y': ['only_y']}
    :param dicts: The list of dict to be merged with append function
    :return: A merged dictionary with append function
    """
    merged = {}
    for d in dicts:
        for k, v in d.items():
            if not type(v) is list:
                v = [v]
            merged[k] = merged.get(k, [])+v
    return merged


def sum_dicts(*dicts):
    """
    Merge a list of dictionaries by summing their values.
    Ex:
    >>> x = {'both1': 1, 'both2': 2, 'only_x': 100}
    >>> y = {'both1': 10, 'both2': 20, 'only_y':200}
    >>> sum_dicts(x, y)
    >>> {'both1': 11, 'both2': 22, 'only_x': 100, 'only_y': 200}
    :param dicts: The list of dict to be summed
    :return: A summed dictionary
    """
    summed = defaultdict(int)  # default value of int is 0
    for d in dicts:
        for k, v in d.items():
            summed[k] += v
    return dict(summed)



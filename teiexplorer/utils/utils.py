#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict


def merge_two_dicts(x, y):
    """Given two dicts (with string keys),
    merge them into a new dict as a shallow copy.
    x values override y values in cases of duplicate keys.
    :param x: First dictionary (master)
    :param y: Second dictionary (slave)
    :return: The merge of x and y, keeping x values in case of conflicts."""
    return dict(y, **x)


def sum_dicts(dicts):
    """
    Merge and sum a list of dictionaries.
    Ex:
    >>> x = {'both1':1, 'both2':2, 'only_x': 100 }
    >>> y = {'both1':10, 'both2': 20, 'only_y':200 }
    >>> sum_dicts(x, y)
    >>> {'both1': 11, 'both2': 22, 'only_x': 100, 'only_y': 200}
    :param dicts: The list of dict to be summed
    :return:
    """
    summed = defaultdict(int)  # default value of int is 0
    for d in dicts:
        for k, v in d.items():
            summed[k] += v
    return dict(summed)

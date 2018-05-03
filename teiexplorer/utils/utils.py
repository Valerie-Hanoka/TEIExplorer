#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from copy import deepcopy

def merge_two_dicts(x, y):
    """Given two dicts (with string keys),
    merge them into a new dict as a deep copy.
    In cases of duplicate keys, values are appended in lists.
    Ex.:
    >>> dic_y = {'both': {'both_y_diff' : 'bar', 'both_same': 'same_y'}, 'only_y': 'only_y'}
    >>> dic_x = {'both': {'both_x_diff' : 'foo', 'both_same': 'same_x'}, 'only_x': {'only_x' : 'baz'}}
    >>> merge_two_dicts(dic_x, dic_y)
    >>> {'both': {
    >>>      'both_same': ['same_x', 'same_y'],
    >>>      'both_x_diff': 'foo',
    >>>      'both_y_diff': 'bar'},
    >>>  'only_x': {'only_x': 'baz'},
    >>>  'only_y': 'only_y'}
    :param x: First dictionary
    :param y: Second dictionary
    :return: The recursive merge of x and y, appending values in list in case of duplicate keys."""
    if not isinstance(y, dict):
        return y
    result = deepcopy(x)
    for k, v in y.items():
        if k in result and isinstance(result[k], dict):
                result[k] = merge_two_dicts(result[k], v)
        else:
            if isinstance(v, dict):
                result[k] = deepcopy(v)
            else:
                v = deepcopy(v)
                existing_v = deepcopy(result.get(k, []))
                if existing_v:
                    v = v if isinstance(v, list) else [v]
                    existing_v = existing_v if isinstance(existing_v, list) else [existing_v]
                    result[k] = existing_v+v
                else:
                    result[k] = v
    return result


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


def flatten_nested_dict_to_pairs(nested_dict):
    """
    Given a nested dict of arbitrary depth, this function returns a
    list of pairs (nested_key, final value).

    :Example:
    >>> nested_dict = {'k1': {'ka' : 'v1', 'kb': {'kα': 'v2'}}, 'k2': 'v3'}
    >>> flatten_nested_dict_to_pairs(nested_dict)
    >>> [('k2','v3'), ('k1_kb_kα','v2'), ('k1_ka', 'v1')]
    :param nested_dict: A dictionary
    :return:
    """
    pairs = []
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            nested_pairs = flatten_nested_dict_to_pairs(value)
            for nested_pair in nested_pairs:
                k, v = nested_pair
                pairs.append((u'%s_%s' % (key, k), v))
        else:
            pairs.append((u'%s' % key,  value))
                
    return pairs


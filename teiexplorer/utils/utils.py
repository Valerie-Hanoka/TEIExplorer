#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from copy import deepcopy
import re

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
    for k, v in y.iteritems():
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


COLON_NOT_FOLLOWED_BY_SPACE_RE = re.compile(':([^\s])')


def prepare_sql_text(text):
    """
    TODO: change this quickfix into a documented version of it
    Some characters of a query may raise issues when used in SQL queries.
    This function transforms the query text in a text that won't be a problem.
    :param text:
    :return: the SQLite compatible version of the text
    """
    if isinstance(text, unicode) or isinstance(text, str):
        text = text.replace("'", "''")
        text = re.sub(COLON_NOT_FOLLOWED_BY_SPACE_RE, "\:\g<1>", text)

    return text

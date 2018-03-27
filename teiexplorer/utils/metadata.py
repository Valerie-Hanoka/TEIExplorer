#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
metadata is part of the project TEIExplorer
Author: Valérie Hanoka

"""

import io

def load_tsv_dewey(dewey_filepath):

    deweys = None
    with io.open(dewey_filepath, mode='r', encoding="utf-8") as dewey_file:
        deweys_lines = [row.split('\t') for row in dewey_file.readlines()]
        deweys = {row[0]: row[1:] for row in deweys_lines}

    return deweys


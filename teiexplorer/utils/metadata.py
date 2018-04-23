#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
metadata is part of the project TEIExplorer
Author: Valérie Hanoka

"""

import io

def load_tsv_dewey(dewey_filepath):
    """
    Parses a correspondance files between documents' Ark ids and Dewey codes.
    This file must contain at least 2 columns: Ark id and Dewey numeric class code and/or Dewey class text.

    :Exemple: of a TSV Dewey mapping file:

    cb41526125z\t090\tManuscrits et livres rares
    cb300188043\t190\tPhilosophie occidentale moderne
    cb34153359b\t900\tGéographie, histoire, sciences auxiliaires de l'histoire

    :param dewey_filepath:
    :return:
    """

    deweys = None
    with io.open(dewey_filepath, mode='r', encoding="utf-8") as dewey_file:
        deweys_lines = [row.split('\t') for row in dewey_file.readlines()]
        deweys = {row[0]: row[1:] for row in deweys_lines}

    return deweys


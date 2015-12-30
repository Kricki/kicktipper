# -*- coding: utf-8 -*-
from difflib import SequenceMatcher

""" This file contains some helper tools.

"""

__author__ = 'Kricki (https://github.com/Kricki)'


def similar(a, b):
    """ Compute "similarity" between two objects a and b.

    See http://stackoverflow.com/questions/17388213/python-string-similarity-with-probability

    :return: Similarity (number between 0 and 1)

    Example:
    similar("Apple","Appel") => 0.8
    similar("Apple","Mango") => 0.0
    """
    return SequenceMatcher(None, a, b).ratio()

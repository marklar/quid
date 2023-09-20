""" class inheritance: parents & children
"""

from typing import Dict, List


def child_parents_dict(classes: List[type]) -> Dict[type, List[type]]:
    """
    child => parents
    """
    return {c: c.__bases__ for c in classes}


def parent_children_dict(classes: List[type]) -> Dict[type, List[type]]:
    """
    parent => children
    """
    d = {}
    for child in classes:
        for parent in child.__bases__:
            d.setdefault(parent, []).append(child)
    return d

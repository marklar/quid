""" Base classes for the new types we create.
Also, a function for finding a common ancestor of an iterable of types.
"""

import enum
import functools
from typing import Optional, List, NamedTuple


class CollectionType:
    pass


class UnknownDictPair(CollectionType):
    pass


class Unknown:
    pass


def nearest_common_ancestor(types: List[type]) -> Optional[type]:
    return functools.reduce(_nearest_ancestor_for_pair, types)


# ----------------
# private


_TOO_COMMON_BASES = frozenset([None, type(None), enum.Enum, object, CollectionType])


class Node(NamedTuple):
    cls: type
    distance: int  # distance traveled up the hierarchy to get there


def _nearest_ancestor_for_pair(type_a: type, type_b: type) -> Optional[type]:
    """Traverse upwards in the class hierarchy to find the nearest common ancestor."""

    def go(a: Node, b: Node) -> Optional[Node]:

        if {a.cls, b.cls} & _TOO_COMMON_BASES:
            return None

        # they're the same class
        if a.cls == b.cls:
            return min([a, b], key=lambda node: node.distance)

        # one class is a parent of the other
        if a.cls in b.cls.__bases__:
            return a
        if b.cls in a.cls.__bases__:
            return b

        # traverse up the hierarchy tree
        b_ancestors = [go(a, Node(p, b.distance + 1)) for p in b.cls.__bases__]
        a_ancestors = [go(b, Node(p, a.distance + 1)) for p in a.cls.__bases__]
        common_nodes = [
            node for node in a_ancestors + b_ancestors if node is not None
        ]

        if not common_nodes:
            return None
        else:
            return min(common_nodes, key=lambda node: node.distance)

    res = go(Node(type_a, 0), Node(type_b, 0))
    return res.cls if res else None

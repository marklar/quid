""" For getting all live Python objects.
"""

import collections
import enum
import gc
from typing import Set


def get_all_objects(classes: Set[type] = None) -> list:
    """Fetch all in-memory objects whose types are provided,
    not including the result list itself.

    (This can take a while.)

    Args:
        classes : The types of objects we want to fetch.
    """
    queue = collections.deque(gc.get_objects())
    res_objs = []
    seen = set(map(id, [res_objs, queue]))
    seen.add(id(seen))

    # pylint: disable=unidiomatic-typecheck

    while queue:
        o = queue.popleft()
        if id(o) in seen:
            continue
        seen.add(id(o))
        if not classes or type(o) in classes:
            res_objs.append(o)
        queue.extend(gc.get_referents(o))

    return res_objs


def is_enum(ty: type) -> bool:
    if enum.Enum in ty.__bases__:
        return True
    else:
        return any(is_enum(t) for t in ty.__bases__)

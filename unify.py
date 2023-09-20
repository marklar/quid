""" For combining multiple covariant types w/ a single, narrower one.
"""

from typing import List, Set, Optional
from Groq.quid.composition import ancestor, coltypes


## TODO: Make unify_types return Optional[type].
## None means "couldn't unify".
## Otherwise, that's our new type.


def unify_types(types: Set[type]) -> Set[type]:
    """Given a set of types that might be unifiable w/ some common ancestor,
    attempt to reduce that set to a common ancestor.

    Return either just the original set of types, or a singleton set
    with the unified type.
    """
    if not types:
        raise ValueError("'types' set should not be empty.")

    nca = ancestor.nearest_common_ancestor(list(types))
    if nca:
        return {nca}
    elif not all(map(lambda t: ancestor.CollectionType in t.__bases__, types)):
        # not all subclasses of CollectionType
        return types
    else:
        return _all_collection_types(types)


def _all_collection_types(types: Set[type]) -> Set[type]:
    """They're all collection types. Maybe we can reduce them.  Need to be
    of the same type of collection (but w/ different element types).
    """
    collection_types = set(t.collection_type for t in types)
    if len(collection_types) > 1:
        # This might seem strange, but it's okay.
        # Might have >1 list-like thing ('list' and 'ndarray'), for example.
        return types
    else:
        col_type = next(iter(collection_types))
        if col_type == tuple:
            return _multiple_tuples(col_type, types)
        else:
            return _multiple_non_tuples(col_type, types)


def _multiple_tuples(col_type: type, types: Set[type]) -> Set[type]:
    """The .collection_type for each is 'tuple'.  That means each of
    'types' has a '.element_types': a _tuple_ of types.
    """
    try:
        element_type_tuples = [t.element_types for t in types]
    except AttributeError:
        # In exactly _one_ case, the type doesn't have 'element_types'
        # as expected, but rather just 'element_type'.  This means
        # there must be some strange bug on 'coltypes' somewhere.
        # This hack allows us to handle that for now and move on.
        return _weird_singleton_tuple(col_type, types)

    # Are the tuples of types even of the same length (shape)?
    tuple_len = _common_len(element_type_tuples)
    if not tuple_len:
        # If not of the same shape, we can't unify them.
        return types
    else:
        # They _are_ all the same shape.
        # We'll want to compare 1sts w/ 1sts, 2nds w/ 2nds...
        nearest_common_ancestors = []
        for i in range(tuple_len):
            common_pos_types = _filter_out_unknowns(t[i] for t in element_type_tuples)
            common_pos_types = unify_types(common_pos_types)
            nca = ancestor.nearest_common_ancestor(common_pos_types)
            if nca is None:
                return types
            else:
                nearest_common_ancestors.append(nca)
        # Here, we have a list of ncas. Create a tuple type for it.
        ncas_type_tuple = coltypes.mk_tuple_class(tuple(nearest_common_ancestors))
        return {_mk_col_type(col_type, ncas_type_tuple)}


def _weird_singleton_tuple(col_type: type, types: Set[type]) -> Set[type]:
    """I don't know why there's this weird, singular example of a
    singleton tuple.
    """
    element_types = _filter_out_unknowns(t.element_type for t in types)
    element_types = unify_types(element_types)
    if len(element_types) == 1:
        elem_type = next(iter(element_types))
        return {_mk_col_type(col_type, elem_type)}
    else:
        return types


def _multiple_non_tuples(col_type: type, types: Set[type]) -> Set[type]:
    """All the same collection type...
    Remove 'Unknown's from the element types.
    If there's >1 element type, we want to skip those.
    """
    element_types = _filter_out_unknowns(t.element_type for t in types)
    element_types = unify_types(element_types)
    nca = ancestor.nearest_common_ancestor(element_types)
    if nca is None:
        return types
    else:
        return {_mk_col_type(col_type, nca)}


def _mk_col_type(col_type, elem_type) -> type:
    cts = coltypes.CollectionTypesInternTable()
    t = cts.mk_collection_type(col_type, elem_type)
    return t


# or perhaps just an iterable?
def _filter_out_unknowns(types: List[type]) -> List[type]:
    return [t for t in types if t not in (ancestor.Unknown, ancestor.UnknownDictPair)]


def _common_len(xs: list) -> Optional[int]:
    if not xs:
        raise ValueError("Must have at least one item to determine common length.")
    return len(xs[0]) if _same_len(xs) else None


def _same_len(xs: list) -> bool:
    len0 = len(xs[0])
    return all(len(x) == len0 for x in xs[1:])

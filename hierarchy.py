""" For displaying the observations of the TypeTracker.

'show_hierarchy' produces and outline.
    Common base class
        subclasses, in alpha order
            attrs, in alpha order, w/ types
"""

import collections
from enum import Enum
from typing import Dict, List, Set
from Groq.quid.composition import mangler, unify


def show_hierarchy(
    field_types: Dict[type, Dict[str, type]],
    qualify_hint: mangler.HintModule = mangler.HintModule.FULL,
) -> str:
    """Show each class, with its data fields and their inferred types.
    'Inferred' here really means the enumeration of all types we see.

    Outline format.
    Common base class
        subclasses, in alpha order
            attrs, in alpha order, w/ types
    """
    return "\n".join(_show_hierarchy(field_types, qualify_hint))


def _show_hierarchy(
    field_types: Dict[type, Dict[str, type]], qualify_hint: mangler.HintModule
) -> List[str]:
    """Generate an outline view of the classes and their fields.
    Start at "tops" of class hierarchy, with classes 'object' and 'Enum'.
    """
    base_to_subs = _base_to_subs(field_types)
    visited = set()
    indent = 4 * " "
    lns = []

    def from_node(cls: type, depth: int):
        if cls in visited:
            return
        visited.add(cls)
        lns.append(depth * indent + cls.__name__)

        if cls in field_types:
            max_name_len = max(len(name) for name in field_types[cls].keys())
            for name, types in sorted(field_types[cls].items(), key=lambda p: p[0]):
                # `types` is already a set, so there won't be duplicates.
                s = "{pre}{name:{ln}} : {types_str}".format(
                    pre=(depth + 1) * indent,
                    name=name,
                    ln=max_name_len,
                    types_str=_type_signature_of_types(types, qualify_hint),
                )
                lns.append(s)

        if cls in base_to_subs:
            for child in sorted(base_to_subs[cls], key=lambda c: c.__name__):
                from_node(child, depth + 1)

    from_node(Enum, 0)
    print()
    from_node(object, 0)
    return lns


def _base_to_subs(field_types: Dict[type, Dict[str, type]]) -> Dict[type, List[type]]:
    """From all the observed classes, map their base classes to them.
    Dict: base_class => child_classes.
    """
    d = collections.defaultdict(list)

    def one_cls(cls: type) -> None:
        if cls not in [object, Enum]:
            for b in cls.__bases__:
                d[b].append(cls)
                one_cls(b)

    for cls in field_types.keys():
        one_cls(cls)
    return d


def _type_signature_of_types(
    types: Set[type], qualify_hint: mangler.HintModule
) -> str:
    """Given all the types that we see for a field, create an aggregate
    type hint.

    Look at all the types and determine whether they're of
    ancestor.CollectionType, and if so whether they have the same
    .collection_type...

    If the .collection_type is tuple, then compare the entries side by
    side.

    If it's not tuple, then it might be list or set or something.  If
    it's one of coltypes.COLLECTION_TYPES, then we can recursively do
    the same check.

    Then, find the nearest_common_ancestor of the .element_types.

    """
    dm = lambda t: mangler.demangle(t, qualify_hint)

    if len(types) == 1:
        return dm(next(iter(types)))

    # Use 'Option'?
    # pylint: disable=unidiomatic-typecheck
    opt = True
    if None in types:
        types.remove(None)
    elif type(None) in types:
        types.remove(type(None))
    else:
        opt = False

    # Use 'Union'?
    if len(types) == 1:
        res = dm(next(iter(types)))
    else:
        unified_types = unify.unify_types(types)
        if len(unified_types) == 1:
            res = dm(next(iter(unified_types)))
        else:
            res = "Union[" + ", ".join(sorted(dm(t) for t in types)) + "]"

    return f"Optional[{res}]" if opt else res

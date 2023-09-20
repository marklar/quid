"""Utilities for determining the compositional relationships among
objects.

"""

import collections
from typing import Tuple, Iterable
import numpy as np
from Groq.quid.composition import mangler
from Groq.quid.composition import ancestor


_FLAT_COL_TYPES = (list, np.ndarray, set, frozenset)
_ASSOC_COL_TYPES = (dict, collections.defaultdict)
COLLECTION_TYPES = (tuple,) + _FLAT_COL_TYPES + _ASSOC_COL_TYPES


class CollectionTypesInternTable:
    """Creates new classes, as necessary, to correspond to collection
    types we see.

    Remembers which we've seen already, so we don't recreate classes.
    """

    def __init__(self, max_elements: int = None):
        # We store two different kinds of new classes.
        # 1. non-tuple collections / sequences:
        #       Dict[collection_type, Dict[element_type, new_type]]
        #    We could make this instead:
        #       Dict[Tuple[collection_type, element_type], new_type]
        #    In which case, we wouldn't need two different dicts for this.
        self._non_tuples = collections.defaultdict(dict)
        # 2. for tuples
        #       Dict[Tuple[element_type, ...], new_type]
        self._tuple_classes = {}
        self._max_elements = max_elements

    def collection_type_for(self, col) -> type:
        """Determine the type of the elements of collection 'col'.
        Create a new class to represent collections of that type, if necessary.
        Add to mapping of:
          { collection_type => { element_type => collection_of_types_type } }
        """
        col_type = type(col)
        if col_type not in COLLECTION_TYPES:
            raise ValueError(f"Object {col} ({col_type}) not a collection type")

        elem_type = self._element_type(col)
        if elem_type not in self._non_tuples[col_type]:
            self._non_tuples[col_type][elem_type] = self.mk_collection_type(
                col_type, elem_type
            )
        return self._non_tuples[col_type][elem_type]

    def mk_collection_type(self, col_type: type, elem_type: type) -> type:
        """Define a new class to represent a type-specific collection.
        Uses a 'mangled' name, compatible with Python symbols.
        """
        class_hint = f"{col_type.__name__}[{_new_class_name(elem_type)}]"
        attrs = {
            "type_hint": class_hint,  # this isn't quite the final type hint
            "collection_type": col_type,
            "element_type": elem_type,
        }
        return type(mangler.mangle(class_hint), (ancestor.CollectionType,), attrs)

    def _element_type(self, col) -> type:
        """Attempt to infer the type of the elements of collection 'col'.
        (_How_ we do this depends on self._max_elements.)
        """
        if isinstance(col, _FLAT_COL_TYPES):
            return self._flat_collection_elem_type(col)

        elif isinstance(col, _ASSOC_COL_TYPES):
            return self._associative_collection_elem_type(col)

        elif isinstance(col, tuple):
            return self._get_or_mk_tuple_type(col)

        else:
            # Don't expect this to happen, as the input arg was already validated.
            raise Exception(f"col should be one of {COLLECTION_TYPES}")

    def _flat_collection_elem_type(self, col) -> type:
        """lists and sets are easy to handle. We look at either every
        element or just self._max_elements of them, and attempt to
        find a common ancestor of all the types we find. If we fail
        to find a common type, we revert to using the type of just
        the _first_ element.
        """
        if not isinstance(col, _FLAT_COL_TYPES):
            raise ValueError(f"{col} ({type(col)}) is not a flat collection.")

        if len(col) == 0:  # 'if not col:' does not work w/ 'ndarray's
            return ancestor.Unknown
        else:
            # How many elements are we going to look at?
            if not self._max_elements:
                elems = col
            else:
                elems = take(self._max_elements, col)

            # Get a single type.
            elem_types = list({self._type_of_elem(e) for e in iter(elems)})
            if not elem_types:
                elem_type = None
            else:
                elem_type = ancestor.nearest_common_ancestor(elem_types)
                if elem_type is None:
                    elem_type = elem_types[0]
            return elem_type

    def _associative_collection_elem_type(self, col) -> type:
        """dicts are essentially composed of 2-tuples. There's a pair of types
        -- for its keys and its values.

        We look at either all the 'items()' in the dict or just
        self._max_elements of them, attempting to find a common type
        for all keys and a common type for all values. If we fail to
        find common ancestors, we fall back on just the first 2-tuple
        from 'items()'.

        We create (as necessary) a new class to represent that product
        of types and use that as the dict's element type.
        """
        if not isinstance(col, _ASSOC_COL_TYPES):
            raise ValueError(f"{col} ({type(col)}) is not an associative collection.")

        if not col:
            # If the dict is empty, we can't know its mapping types.
            return ancestor.UnknownDictPair
        else:
            # How many pairs are we going to look at?

            if not self._max_elements:
                pairs = col.items()
            else:
                pairs = take(self._max_elements, col.items())

            # Get a single type for keys.
            key_types = list({self._type_of_elem(k) for k, _ in pairs})
            key_type = ancestor.nearest_common_ancestor(key_types)
            if key_type is None:
                key_type = key_types[0]

            # Get a single type for vals.
            val_types = list({self._type_of_elem(v) for _, v in pairs})
            val_type = ancestor.nearest_common_ancestor(val_types)
            if val_type is None:
                val_type = val_types[0]

            # Get or create the composite type and return it.
            tuple_of_types = (key_type, val_type)
            if tuple_of_types not in self._tuple_classes:
                self._tuple_classes[tuple_of_types] = mk_tuple_class(tuple_of_types)
            return self._tuple_classes[tuple_of_types]

    def _type_of_elem(self, e: object) -> type:
        if isinstance(e, COLLECTION_TYPES):
            return self.collection_type_for(e)
        else:
            return type(e)

    # -------------
    # tuple types

    def _get_or_mk_tuple_type(self, tpl: tuple) -> type:
        """Given a tuple, look at the types of its elements.

        If we've seen this particular product of types before, just
        return it.  If we haven't seen it before, create a new type to
        represent it and return that.
        """
        tuple_of_types = tuple(
            self.collection_type_for(e)
            if isinstance(e, COLLECTION_TYPES)
            else type(e)
            for e in tpl
        )
        if tuple_of_types not in self._tuple_classes:
            self._tuple_classes[tuple_of_types] = mk_tuple_class(tuple_of_types)
        return self._tuple_classes[tuple_of_types]


# -----------------------
# stand-alone functions


def take(n: int, xs: Iterable) -> list:
    """Like xs[:n], but only force the first `n` elements if it's a generator."""
    if isinstance(xs, list):
        return xs[:n]
    else:
        return [x for (_, x) in zip(range(n), xs)]


def mk_tuple_class(tuple_of_types: Tuple[type, ...]) -> type:
    """Define a new class to represent a specific product of types.
    The new class derives 'tuple'.
    """
    type_hint = _tuple_type_name(tuple_of_types)
    attrs = {
        "type_hint": type_hint,
        "collection_type": tuple,
        "element_types": tuple_of_types,
    }
    return type(mangler.mangle(type_hint), (ancestor.CollectionType,), attrs)


def _new_class_name(elem_type: type) -> str:
    """Attempt to determine the type of the elements of a collection.
    We currently simply look at the initial element of the collection
    and make wild assumptions based on that.

    Return a type-hint name.
    """
    if elem_type is ancestor.UnknownDictPair:
        return "Unknown, Unknown"

    elif elem_type is tuple:
        tuple_of_types = tuple(type(i) for i in elem_type)
        type_hint = _tuple_type_name(tuple_of_types)
        return f"Tuple[{type_hint}]"

    elif elem_type is None:
        return "Unknown"

    else:
        return mangler.demangle(elem_type, mangler.HintModule.NONE)


def _tuple_type_name(tuple_of_types: Tuple[type, ...]) -> str:
    """Return a pre-mangled, type-hint-looking thing."""
    return ", ".join(t.__name__ for t in tuple_of_types)

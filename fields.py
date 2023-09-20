""" Utilities for determining the compositional relationships among
objects.
"""

import collections
import inspect
from typing import Callable, Dict, List, Set
from Groq.quid.composition import coltypes, hierarchy, mangler, objects


class TypeTracker:
    """Keeps type info about the data fields of classes.

    { class => { field_name => type(val) } }

    For any class, we can infer the types of its fields by looking at
    many instances of that class and simply recording which types we
    encounter.

    Instantiate a TypeTracker, and then simply add as many
    observations as you like.
    """

    def __init__(self, max_elements: int = None):
        """The function 'type_hint_for_class' provides a way of
        customizing how a class is presented in type signatures.
        """
        self._field_types: Dict[type, Dict[str, Set[type]]] = collections.defaultdict(
            lambda: collections.defaultdict(set)
        )
        self._collection_types = coltypes.CollectionTypesInternTable(
            max_elements=max_elements
        )

    # --------------------------------------
    # viewing results - classes and fields

    def write(
        self,
        file_name: str,
        qualify_hint: mangler.HintModule = mangler.HintModule.FULL,
    ) -> None:
        """Commit the results of `show` to a file."""
        with open(file_name, "w") as f:
            f.write(
                hierarchy.show_hierarchy(self._field_types, qualify_hint=qualify_hint)
            )
            print(f"wrote: {file_name}")

    # -----------------------------
    # viewing results, just types

    def all_type_hints(
        self, qualify_hint: mangler.HintModule = mangler.HintModule.FULL
    ) -> List[str]:
        """A list of type hints for all the field types observed.
        Useful for debugging.
        """
        all_types = set(
            ty
            for fields in self._field_types.values()
            for types in fields.values()
            for ty in types
        )
        return sorted(mangler.demangle(t, qualify_hint) for t in all_types)

    # -----------------
    # collecting data

    def observe_instances_of(self, classes: Set[type]) -> None:
        """For all objects in memory whose types are in 'classes',
        collect information about the types of its data fields.
        """
        for o in objects.get_all_objects(classes):
            self.observe(o)

    def observe(self, obj) -> None:
        """Collect information about this object's type and that
        of the values of its data fields.
        """
        if obj is not None:
            skip_name = _skip_name_predicate(obj)
            for n, v in inspect.getmembers(obj, lambda v: not _is_function_like(v)):
                if not skip_name(n):
                    self._observe_field(obj, n, v)

    # -------------------------------
    # for observe (data collection)

    def _observe_field(self, obj, field_name: str, val) -> None:
        """For this object's field 'field_name',
        add val's type into the set seen for this field.
        """
        if not type(val).__name__.startswith("sys."):
            self._field_types[type(obj)][field_name].add(self._get_val_type(val))

    def _get_val_type(self, val) -> type:
        """If val's type is 'simple', just return it.
        If it's a collection/sequence, we want to know _of_what_.
        Python doesn't have types for, say, List[str], so we'll
        dynamically create classes as necessary and use those.
        """
        if isinstance(val, coltypes.COLLECTION_TYPES):
            return self._collection_types.collection_type_for(val)
        else:
            return type(val)


# -----------------
# funcs


def _skip_name_predicate(obj: object) -> Callable[[str], bool]:
    """We use information about an object's type (class)
    to determine which of its fields we care about and which not.

    Specifically, which are function-like things?
    """
    # for properties & functions
    cls = type(obj)
    func_names = [k for k, v in inspect.getmembers(cls, _is_function_like)]

    # In case we want to filter for only endemic data members.
    # endemic_funcs = [f for f in cls.__dict__.keys() if not f.startswith("__")]
    # inherited_funcs = [f for f in func_names if f not in endemic_funcs]

    return lambda name: name.startswith("__") or name in func_names


def _is_function_like(v) -> bool:
    """Keep function-like things. (Not data fields.)"""
    return any(
        (
            inspect.isfunction(v),
            inspect.ismethod(v),
            inspect.isbuiltin(v),
            isinstance(v, property),
        )
    )

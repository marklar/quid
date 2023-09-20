"""Utilities for exploring a package structure.
What modules are there, and what classes in those modules.

Here, a 'Package' is a set of modules (`Set[ModuleType]`).

`quid.modules_in_package` gives one a way to gather up some modules to
explore.

Once you have a set of modules, you can use those to explore their
contents.

"""

import importlib
import inspect
from typing import Set, Dict, List, Optional
from types import ModuleType


# --------------------
# modules in package


def modules_in_package(
    root_module: ModuleType,
    keep: Optional[List[str]] = None,
    skip: Optional[List[str]] = None,
) -> Set[type]:
    """Gather up modules imported directly or indirectly from
    root_module.

    Optionally, one may trim its search. Keep any module whose
    fully-qualified name includes any of the 'keep' strings. Reject
    any module whose fully-qualified name includes any of the 'skip'
    strings.

    Args:
      required:
        root_module : Module to import first.
                      Serves as the basis of the package.
      optional:
        keep        : Strings that each module name must contain.
                      Default: None.
        skip        : Strings that each module name must not contain.
                      Default: None.

    """

    def keep_module(mod: ModuleType) -> bool:
        def any_match(strs: List[str]) -> bool:
            return any(map(lambda s: s in mod.__name__, strs))

        good = keep is None or any_match(keep)
        return good and (skip is None or not any_match(skip))

    def go(mod: ModuleType, accum: Set[ModuleType]) -> set:
        # get all modules
        try:
            name_mod_pairs = inspect.getmembers(mod, inspect.ismodule)
        except ModuleNotFoundError:
            name_mod_pairs = []

        # filter them
        mods = set(m for _name, m in name_mod_pairs if keep_module(m))
        # recurse on novel ones
        for m in mods - accum:
            accum = go(m, accum | mods)
        return accum

    return go(root_module, set([root_module]))


# --------------------
# classes in package


# Remove this function?
# It's a very common use case, but maybe its arguments are confusing?
def classes_in_package(
    root_module: ModuleType,
    keep: Optional[List[str]] = None,
    skip: Optional[List[str]] = None,
) -> Set[type]:
    """Convenience wrapper for most common case.
    Return all classes defined in the package specified by root_module.
    """
    return classes_in_modules(modules_in_package(root_module, keep=keep, skip=skip))


def classes_in_modules(modules: Set[ModuleType]) -> Set[type]:
    """For provided modules, gather up all classes defined therein."""
    out = set()
    for m in modules:
        out |= classes_in_module(m)
    return out


def classes_in_module(module: ModuleType) -> Set[type]:
    """All classes defined in the provided module."""
    try:
        return set(
            obj
            for _name, obj in inspect.getmembers(module, inspect.isclass)
            if obj.__module__ == module.__name__
        )
    except ModuleNotFoundError:
        return set()


# -------------------------
# modules & their classes


def class_module_dict(classes: Set[type]) -> Dict[type, ModuleType]:
    """For any class, where was it defined?"""
    return {c: importlib.import_module(c.__module__) for c in classes}


def module_classes_dict(modules: Set[ModuleType]) -> Dict[ModuleType, List[type]]:
    """For any module, what classes are defined in it?"""
    d = {}
    for m in modules:
        for c in classes_in_module(m):
            d.setdefault(m, []).append(c)
    return d

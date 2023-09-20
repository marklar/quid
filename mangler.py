"""Utilities for mangling/demangling newly-created class names.

When creating a new class, don't use its eventual type hint for the
name, as type hints contain symbol-table-unfriendly characters
(i.e. '[', ']', ',', and ' ').

So, mangle them, using identifier-friendly characters:
  + "_of_" instead of "["
  + "_fo_" instead of "]"
  + "_and_" instead of ", "

Then when displaying the names of classes, unmangle them.
"""

import enum
import re
from typing import Tuple, Pattern
from Groq.quid.composition import ancestor


class HintModule(enum.Enum):
    """ How much of the module name to display in type hint.
    """

    FULL = enum.auto()  # e.g. first.middle.last.MyClass
    FINAL = enum.auto()  # e.g. last.MyClass
    NONE = enum.auto()  # e.g. MyClass


# TODO?: make these the _type_, rather than the name of it.
_SIMPLE_BUILTIN_TYPES = frozenset(
    "range bool int float complex str bytes bytearray memoryview".split()
)


_DEMANGLE_SUBSTITUTIONS: Tuple[Tuple[Pattern[str], str]] = (
    (re.compile("^frozenset_"), "FrozenSet_"),
    (re.compile("_frozenset_"), "_FrozenSet_"),
    (re.compile("^set_"), "Set_"),
    (re.compile("_set_"), "_Set_"),
    (re.compile("^tuple_"), "Tuple_"),
    (re.compile("_tuple_"), "_Tuple_"),
    (re.compile("^list_"), "List_"),
    (re.compile("_list_"), "_List_"),
    (re.compile("^defaultdict_"), "DefaultDict_"),
    (re.compile("_defaultdict_"), "_DefaultDict_"),
    (re.compile("^dict_"), "Dict_"),
    (re.compile("_dict_"), "_Dict_"),
    (re.compile("^function_"), "Callable_"),
    (re.compile("_function_"), "_Callable_"),
    (re.compile("_of_"), "["),
    (re.compile("_fo_"), "]"),
    (re.compile("_and_"), ", "),
)


def demangle(t: type, qualify_hint: HintModule) -> str:
    """Pretty-up the display of a single type, making it look like a mypy
    type hint.
    """
    # None
    if t is type(None):
        return "None"

    # CollectionType
    elif ancestor.CollectionType in t.__bases__:
        return _ordered_subs(t.__name__, _DEMANGLE_SUBSTITUTIONS)

    # builtins
    elif t.__name__ in _SIMPLE_BUILTIN_TYPES:
        return t.__name__

    else:
        # all else
        prefix = {
            HintModule.FULL: f"{t.__module__}.",
            HintModule.FINAL: f'{t.__module__.split(".")[-1]}.',
            HintModule.NONE: "",
        }
        return prefix.get(qualify_hint) + f"{t.__name__}"


# ----------------


_MANGLE_SUBSTITUTIONS: Tuple[Tuple[Pattern[str], str]] = (
    (re.compile(", "), "_and_"),
    (re.compile("\]"), "_fo_"),
    (re.compile("\["), "_of_"),
    (re.compile("^Callable_"), "function_"),
    (re.compile("_Callable_"), "_function_"),
    (re.compile("^Dict_"), "dict_"),
    (re.compile("_Dict_"), "_dict_"),
    (re.compile("^DefaultDict_"), "defaultdict_"),
    (re.compile("_DefaultDict_"), "_defaultdict_"),
    (re.compile("^List_"), "list_"),
    (re.compile("_List_"), "_list_"),
    (re.compile("^Tuple_"), "tuple_"),
    (re.compile("_Tuple_"), "_tuple_"),
    (re.compile("^Set_"), "set_"),
    (re.compile("_Set_"), "_set_"),
    (re.compile("^FrozenSet_"), "frozenset_"),
    (re.compile("_FrozenSet_"), "_frozenset_"),
)


def mangle(hint: str) -> str:
    """ Given the desired name (type hint) for a class,
    return the actual name to give the class.
    """
    return _ordered_subs(hint, _MANGLE_SUBSTITUTIONS)


# ----------------
# private


def _ordered_subs(s, pairs: Tuple[Tuple[Pattern[str], str]]) -> str:
    for pat, rep in pairs:
        s = re.sub(pat, rep, s)
    return s

""" Functions for producing textual / graphical output.
"""

import os
import subprocess
from types import ModuleType
from typing import Callable, List, Dict, Set
from Groq.quid import dot, inheritance, pkg


def class_hierarchy_image(
    classes: Set[type],
    img_file_root: str,
    group_by_module: bool = True,
    cls_color: Callable[[type], str] = None,
    ranksep: float = 3.0,
) -> None:
    """Creates a class hierarchy diagram.

    Creates a PNG file (with root 'img_file_root') for the provided classes.

    Args:
        required:
            classes         : The classes to display.

            img_file_root   : A filepath, but without extension.
                              e.g. "path/to/my/image" (no '.png')

        optional:
            group_by_module : Whether to cluster classes by the module in which
                              they're defined.

            cls_color       : A configuration function. Arbitrary logic for
                              determining the color of the text label for a class.
                              Default: None (== lambda _c: return "black")

            ranksep         : Dot-language attribute setting.
                              How much vertical distance to put between "ranks"
                              (rows) of nodes in the diagram.

    """
    img_ext = "png"
    img_file_name = img_file_root + "." + img_ext
    dot_file_name = img_file_root + ".dot"

    # create dot file
    dot_str = dot.hierarchy_diagram_dot(
        classes, group_by_module=group_by_module, cls_color=cls_color, ranksep=ranksep
    )
    _ensure_path(img_file_root)
    with open(dot_file_name, "w") as f:
        f.write(dot_str)

    # generate image
    args = ["dot", f"-T{img_ext}", dot_file_name, "-o", img_file_name]
    print(f"Running subprocess: `{' '.join(args)}` ...")
    subprocess.run(args, check=False)
    print(f"Generated file: {img_file_name}.")


def _ensure_path(path: str) -> None:
    path_dir = os.path.dirname(path)
    if path_dir:
        os.makedirs(path_dir, exist_ok=True)


# ------------------


def print_class_hierarchy(classes: Set[type]) -> None:
    """Print textual outline showing class inheritance.

    In the case of multple inheritance...
    Classes which inherit from >1 parent will appear >1 time.

    Args:
        classes : Which classes to display.
                  Can be obtained from functions in pkg.
    """
    # Dicts with class names.
    names_parent_to_children: Dict[str, List[str]] = _names_dict(
        inheritance.parent_children_dict(classes)
    )
    names_child_to_parents: Dict[str, List[str]] = _names_dict(
        inheritance.child_parents_dict(classes)
    )

    displayed_children = set()

    def show_children(p: type, depth: int) -> None:
        displayed_children.add(p)
        for c in sorted(names_parent_to_children.get(p, [])):
            print(("    " * depth) + f"{c}")
            if c not in displayed_children:
                show_children(c, depth + 1)

    for p in sorted(names_parent_to_children.keys()):
        if p not in names_child_to_parents:
            print(p)
            show_children(p, 1)


def _names_dict(d: Dict[type, List[type]]) -> Dict[str, List[str]]:
    """Map over the dict, replacing each element w/ its name."""
    return {k.__name__: [v.__name__ for v in vs] for k, vs in d.items()}


# ------------------


def print_classes_by_module(modules: Set[ModuleType]) -> None:
    """Show where classes live in module hierarchy.

    Args:
        modules : Modules whose classes we'd like to see.
                  Can be obtained from functions in pkg.
    """
    name = lambda o: o.__name__
    for m in sorted(modules, key=name):
        classes = sorted(pkg.classes_in_module(m), key=name)
        if classes:
            print(m.__name__)
            for c in classes:
                print(f"    {c.__name__}")

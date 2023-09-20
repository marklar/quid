""" Given a module at the root of a package,
create a diagram (image) of the class hierarchy.


https://graphviz.gitlab.io/_pages/doc/info/lang.html
https://graphviz.gitlab.io/_pages/doc/info/attrs.html
"""

from types import ModuleType
import re
from typing import List, Callable, Set, Dict

from Groq.quid import inheritance, pkg


def hierarchy_diagram_dot(
    classes: Set[type],
    group_by_module: bool = True,
    cls_color: Callable[[type], str] = None,
    ranksep: float = 3.0,
) -> str:
    """ Create .dot text. (One big string.)
    """
    lines = [
        f"digraph {{",
        '  node [shape=box, fontname="Arial"];',
        f"  ranksep = {ranksep};",
        '  fontname = "Arial";',
    ]
    if group_by_module:
        for lns in _clusters(classes, cls_color):
            lines.extend(lns)
    lines.extend(_edge_lines(classes, cls_color))
    lines.append("}")
    return "\n".join(lines)


# -----------


_CLASS_NAMES_TO_OMIT = frozenset("object Enum".split())


def _edge_lines(classes: Set[type], cls_color: Callable[[type], str]) -> List[str]:
    """ Add arrows from parents to children.
    Elide arrows from 'object' or 'Enum', as there are too many.
    """
    parent_to_children = inheritance.parent_children_dict(classes)

    def mk_line(parent: type, children: List[type]):
        children_str = " ".join(_dot_safe_name(c) for c in children)
        parent_name = _dot_safe_name(parent)

        # If the parent class isn't from this package, display both:
        #   + its class name, and
        #   + its module name in parens (on a separate line).
        # Wrap the whole thing in quotes because of the whitespace.
        if parent not in classes:
            parent_name = f'"{parent_name}\n({parent.__module__})"'

        return f"  {parent_name} -> {{ {children_str} }};"

    def node_line(cls: type) -> str:
        clr = "" if cls_color is None else f" [fontcolor={cls_color(cls)}]"
        return f"    {_dot_safe_name(cls)}{clr};"

    edges = [
        mk_line(p, cs)
        for p, cs in parent_to_children.items()
        if p.__name__ not in _CLASS_NAMES_TO_OMIT
    ]
    nodes = [
        node_line(c)
        for p, cs in parent_to_children.items()
        if p.__name__ not in _CLASS_NAMES_TO_OMIT
        for c in cs
    ]

    return nodes + edges


def _clusters(
    classes: Set[type], cls_color: Callable[[type], str]
) -> List[List[str]]:
    """ Make one cluster per module.
    The cluster contains only nodes. (No edges.)
    """
    # group classes by module
    m2cs = {}
    for c, m in pkg.class_module_dict(classes).items():
        m2cs.setdefault(m, []).append(c)

    # One cluster per module in package.
    return [_one_cluster(m, cs, cls_color) for m, cs in m2cs.items()]


def _one_cluster(
    module: ModuleType, classes: List[type], cls_color: Callable[[type], str]
) -> List[str]:
    """ Create a cluster subgraph containing the 'classes' of 'module'.
    """
    lines = []
    # The cluster 'header'.
    module_name = module.__name__
    mod_name_under = re.sub("\.", "_", module_name)
    lines.extend(
        [
            f"  subgraph cluster_{mod_name_under} {{",
            f'    label="{module_name}";',
            "    style=filled;",
            "    color=lightgrey;",
            "    node [style=filled, fillcolor=white];",
        ]
    )
    # The nodes themselves - w/ logic for label text and color.
    child_to_parents = inheritance.child_parents_dict(classes)
    for c in classes:
        lines.append(_node_line(c, child_to_parents, cls_color))
    # End of cluster.
    lines.append("  }")
    return lines


def _node_line(
    cls: type,
    child_to_parents: Dict[type, List[type]],
    cls_color: Callable[[type], str],
) -> str:
    """ Determine label text and color.
    """
    # If it's a child of Enum, then make it brown.
    if cls in child_to_parents:
        if "Enum" in child_to_parents[cls]:
            return f"    {_dot_safe_name(cls)} [fontcolor=brown];"

    # Not Enum
    clr = "" if cls_color is None else f" [fontcolor={cls_color(cls)}]"
    return f"    {_dot_safe_name(cls)}{clr};"


_DOT_KEYWORDS = frozenset("Digraph Graph SubgraphContext Dot".split())


def _dot_safe_name(cls: type) -> str:
    """If the name of the class is also a Dot-language keyword, then it
    must be wrapped in quotes (else cause a Dot parsing error).

    We wouldn't have to check. We could instead wrap all node names in
    quotes.  But the out files can be quite large, so fewer bytes is
    nice, and the lookup is fast.

    """
    n = cls.__name__
    return f'"{n}"' if n in _DOT_KEYWORDS else n

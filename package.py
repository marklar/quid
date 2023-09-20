""" Example program.

> hempy examples/package.py

"""

import numpy

from Groq import quid


def numpy_package():
    print("\n-----------\n-- numpy\n")
    modules = quid.modules_in_package(numpy, keep=["numpy"], skip=None)

    # this uses 'view'
    quid.print_classes_by_module(modules)


def numpy_inheritance():
    """Print the inheritance hierarchy for numpy."""
    classes = quid.classes_in_package(numpy, keep=["numpy"])
    quid.print_class_hierarchy(classes)


if __name__ == "__main__":
    numpy_package()

Table of Contents:

[[_TOC_]]

----

# Quid

Utilities for exploring a Python code base.

```
quid (noun):
  1. The inherent nature of something. Essence.
  2. gist; point; crux
```

We'll want to understand the code's structure:
+ *package* structure
  - _modules_: which modules are included
  - _classes_: which classes are defined in those modules
+ class *inheritance* structure
  - how the classes inherit structure and logic
+ *compositional* structure
  - _references_: how instances of classes refer to each other


## Package Structure

### A Package's Modules

Given any module -- perhaps the root module of a package --, `quid`
can discover the set of all modules it imports, directly or
indirectly.

You might think of this as a 'package', but that's something of a
misnomer. (Perhaps it should be called a `ModuleSet`.)

`quid.modules_in_package()` allows fetching a set of modules. Provide
a so-called "root" module -- a starting point for importing other
modules.

By default, it grabs _every_ module imported, directly or
transitively, regardless of where from. This likely isn't what you
want. To trim its search, you can provide lists of strings for
matching against the fully-qualified module names. `keep` strings are
whitelist-like: if any is contained in the fully-qualified module
name, keep that module. `skip` is blacklist-like; if any is contained
in the fully-qualified module name, skip that module.

Here's an example:

```python
from pkg.to.view import mymodule
from Groq import quid

modules = quid.modules_in_package(
    mymodule,
    keep=["pkg.to.view"],    # anything in the package is fair game, except...
    skip=["util", "debug"],  # ...modules containing these strings
)
```

#### Only top-level `import`s

There's an important caveat to be aware of. `quid` sees only top-level
`import` statements. If you have an `import` embedded somewhere -- in
a function, e.g. --, `quid` won't see that.

But you wouldn't embed an `import` statement inside a function, would
you? ;-)


### Modules' Classes

From a set of modules, `quid` can tell you what _classes_ are defined
in each. Something like:

```
my.module.a
    Bar
    Foo
my.module.b
    Baz
    Quux
```

(The modules are sorted alphabetically, as are the classes within each
module.)

To get output like that above, just do this:

```python
from Groq import quid
from pkg.to.view import mymodule

modules = quid.modules_in_package(mymodule, keep=["pkg.to.view"])
quid.print_classes_by_module(modules)
```


## Class Inheritance

Given a set of _classes_, `quid` can tell you their _inheritance_
relationships. It can generate a textual outline, something like this:

```
object
    Foo
        Bar
        Baz
    Fubar
        Quux
```

(In the case of multiple inheritance, child classes make multiple
appearances in the output.)

To get output like that above, just do this:

```python
from Groq import quid
from pkg.to.view import mymodule

classes = quid.classes_in_package(mymodule)
quid.print_class_hierarchy(classes)
```


## Package Structure & Inheritance Structure

`quid` can also _combine_ these two types of info -- class-module and
class-class relationships -- and display it in a diagram. Given a set
of classes (from all modules in some package, say), `quid` can show
you:

+ the classes defined therein,
+ how they inherit from each other, and
+ which module each is defined in


The following code generates an image file (`mymodule.png`):

```python
from Groq import quid
from pkg.to.view import mymodule

image_file_root = "mymodule"

quid.class_hierarchy_image(
    quid.classes_in_package(mymodule, keep=["pkg.to.view"]),
    image_file_root,
    group_by_module=True,   # includes module info
)
```

Try it!

### Diagram Display Options

Setting `group_by_module` to `True` provides additional information,
but sometimes it muddles up the diagram. It's probably a good idea to
first try it set to `True`, and should the resulting diagram be too
difficult to interpret, then rediagramming with it set to `False`.

`ranksep` is a Dot-language attribute, setting the number of inches
between "ranks" (or levels) in the hierarchy. The greater the
`ranksep`, the taller the diagram. If the `ranksep` is too short, the
lines between nodes in different ranks may get awfully messy. By
default `ranksep` is `3.0`; if the result looks like it would benefit
from a greater vertical spread, try a higher number.

`cls_color` is an advanced option. It's for setting the color of the
text of a class's node in the diagram. `cls_color` is a
`Callable[[type], str]`, where the return `str` is the name of a
color, e.g. `"black"` or `"red"`. Most probably, you'll want any
such function you provide to look at the `class`'s name
(`cls.__name__`) to determine what color to display, but perhaps
you'll want to know its parent classes (`cls.__bases__`) or some other
attribute of the `class`.


## Compositional Structure

Python uses duck typing, which means we cannot programmatically
determine a priori the types of objects in a program. Type hints (and
documenatation) provide good information, but they don't dictate well
typedness.

This lack of type information complicates the charting of
compositional interconnectness. How can we know whether, for example,
an instance of class `A` has a reference to an instance of class `B`?
Or a list of such instances? Or maybe they're actually `C`s? Or either
`B`s or `C`s?

Though we may never know all the possibilities, we can gain some
knowledge by running a program and observing it. If that execution of
our program is representative of its typical behavior, then the
references we see are a good guide.

That's what `quid` attempts to do. `quid` provides a utility called a
`TypeTracker`. Instantiate one, and then feed it objects whose
structure you wish to determine. Then when you're done, you can ask
the `TypeTracker` to generate a file with its results.


```python
from Groq import quid
from pkg.to.view import mymodule


# Create a `type_tracker` for gathering your observations about objects' types.
type_tracker = quid.TypeTracker()


#
# Run your program logic here, instantiating objects.
#
...


# Just before your program finishes, explicitly ask `type_tracker` to
# gather type information about particular classes.

classes = quid.classes_in_package(mymodule)
type_tracker.observe_all(classes)

# When you're done observing objects, have `type_tracker` output its results.
type_tracker.write("tracker.txt")

```

What are its results?
[Mypy type hints](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html).


It looks something like this:

```
object
    MyClass
        _bar : Option[int]
        baz  : Tuple[float, float]
        foos : Dict[str, List[MyOtherClass]]
    MyOtherClass
        _quuxes : Union[Set[str], List[str]]
```

For each of your classes (in this case `MyClass` and `MyOtherClass`),
it provides a list of data fields (e.g. `_foos`), each with a type hint
(e.g. `Dict[str, List[MyOtherClass]]`).

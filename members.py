import inspect

# from groq.instruction import instructions as ix
# from groq.instruction.units import mem
from groq.instruction.units import mem_agt


def keep(v) -> bool:
    """We're concerned only with data fields, not methods."""
    # return True
    return not any(
        inspect.isfunction(v),
        inspect.ismethod(v),
        inspect.isbuiltin(v),
        isinstance(v, property),
    )


def member_providence(cls: type) -> None:
    endemic_members = [m for m in cls.__dict__.keys() if not m.startswith("__")]

    all_members = [k for k, v in inspect.getmembers(cls) if not k.startswith("__")]

    inherited_members = [m for m in all_members if m not in endemic_members]

    print("class:", cls)
    print("    inherited members:")
    for m in sorted(inherited_members):
        print(f"        {m}")
    print("    endemic members:")
    for m in sorted(endemic_members):
        print(f"        {m}")


def inspect_class(cls: type) -> None:
    print(f"class: {cls}")
    pairs = inspect.getmembers(cls)  # , keep)

    print("  neither function/property:")
    for k, v in sorted(pairs, key=lambda p: p[0]):
        if not k.startswith("__"):
            if not (inspect.isfunction(v) or isinstance(v, property)):
                print(f"    {k} :: {v}")

    print("  -----------")

    print("  properties:")
    for k, v in sorted(pairs, key=lambda p: p[0]):
        if not k.startswith("__"):
            if isinstance(v, property):
                print(f"    {k}")

    print("  -----------")

    # pairs = cls.__dict__.items()
    print("  functions:")
    for k, v in sorted(pairs, key=lambda p: p[0]):
        if not k.startswith("__"):
            if inspect.isfunction(v):
                print(f"    {k}")

    print("")
    print("")


if __name__ == "__main__":
    Cls = mem_agt.AGTReadInsn

    # f = inspect_class
    f = member_providence

    parents = [c for c in Cls.__bases__ if c is not object]
    for p in parents:
        f(p)
    f(Cls)

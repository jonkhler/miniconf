from dataclasses import dataclass

from mlparams import from_yaml, to_yaml, update


def test_saving_and_loading():
    @dataclass
    class A:
        a: str
        b: dict[str, int]
        c: list[str]

    @dataclass
    class B:
        a: list[A]
        b: dict[str, A]

    @dataclass
    class D:
        a: dict[str, B]

    d = D(
        {
            "_": B(
                a=[A(a="b", b={"c": 2, "d": 3}, c=["e", "f"])],
                b={"g": A(a="h", b={"i": 2, "j": 3}, c=["k", "l"])},
            )
        }
    )
    yaml = to_yaml(d)
    d_ = from_yaml(D, yaml)

    assert d == d


def test_updating():
    @dataclass
    class A:
        a: str
        b: str

    @dataclass
    class B:
        a: A
        b: A

    b = B(
        a=A("foo", "bar"),
        b=A("asdf", "jkl;"),
    )

    delta_yaml = """
c:
    a: wurst
    b: kaese
"""
    delta = from_yaml(B, delta_yaml, strict=False)
    b_ = update(B, b, delta, strict=True)
    assert b_ == b

    delta_yaml = """
b:
    a: wurst
    b: kaese
"""
    delta = from_yaml(B, delta_yaml, strict=False)
    b_ = update(B, b, delta, strict=True)
    assert b_ == B(
        a=A("foo", "bar"),
        b=A("wurst", "kaese"),
    )

import typing as t

import pytest

from envier import En
from envier import validators as v


class Config(En):
    foo = En.v(str, "CHOICE", validator=v.choice(["a", "b", "c"]))
    bar = En.v(
        t.Optional[str], "OPT_CHOICE", default=None, validator=v.choice(["a", "b", "c"])
    )
    n = En.v(int, "SIZE", default=0, validator=v.range(0, 100))


def test_choice(monkeypatch):
    with pytest.raises(KeyError):
        Config()

    monkeypatch.setenv("CHOICE", "a")
    assert Config().foo == "a"

    monkeypatch.setenv("CHOICE", "d")
    with pytest.raises(ValueError) as excinfo:
        Config()

    assert (
        excinfo.value.args[0]
        == "Invalid value for environment variable CHOICE: value must be one of ['a', 'b', 'c']"
    )


def test_optional_choice(monkeypatch):
    monkeypatch.setenv("CHOICE", "a")

    assert Config().bar is None

    monkeypatch.setenv("OPT_CHOICE", "a")
    assert Config().bar == "a"

    monkeypatch.setenv("OPT_CHOICE", "d")
    with pytest.raises(ValueError) as excinfo:
        Config()

    assert (
        excinfo.value.args[0]
        == "Invalid value for environment variable OPT_CHOICE: value must be one of ['a', 'b', 'c']"
    )


def test_range(monkeypatch):
    monkeypatch.setenv("CHOICE", "a")

    assert Config().n == 0

    monkeypatch.setenv("SIZE", "-10")
    with pytest.raises(ValueError) as excinfo:
        Config()

    assert (
        excinfo.value.args[0]
        == "Invalid value for environment variable SIZE: value must be in range [0, 100]"
    )

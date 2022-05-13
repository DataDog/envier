import pytest

from envier import Env


def test_env_default():
    class Config(Env):
        foo = Env.var(int, "foo.bar", default=42)

    config = Config()

    assert config.foo == 42


def test_env(monkeypatch):
    monkeypatch.setenv("FOO_BAR", "24")

    class Config(Env):
        foobar = Env.var(int, "foo.bar", default=42)

    config = Config()

    assert config.foobar == 24


def test_env_missing_mandatory():
    class Config(Env):
        foo = Env.var(int, "FOO")

    with pytest.raises(KeyError):
        Config()


@pytest.mark.parametrize(
    "deprecations,match",
    [
        (
            [("OLD_FOO", "0.1", "1.0")],
            "OLD_FOO has been deprecated in version 0.1 and will be removed in version 1.0. Use FOO instead",
        ),
        (
            [("OLD_FOO", None, "1.0")],
            "OLD_FOO has been deprecated and will be removed in version 1.0. Use FOO instead",
        ),
        (
            [("OLD_FOO", "0.1", None)],
            "OLD_FOO has been deprecated in version 0.1. Use FOO instead",
        ),
        (
            [("OLD_FOO", None, None)],
            "OLD_FOO has been deprecated. Use FOO instead",
        ),
    ],
)
def test_env_deprecations(monkeypatch, deprecations, match):
    monkeypatch.setenv("OLD_FOO", "42")

    class Config(Env):
        foo = Env.var(int, "FOO", deprecations=deprecations)

    with pytest.warns(DeprecationWarning, match=match):
        assert Config().foo == 42


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1", True),
        ("True", True),
        ("On", True),
        ("yeS", True),
        ("0", False),
        ("faLse", False),
        ("whatever", False),
    ],
)
def test_env_parser(monkeypatch, value, expected):
    monkeypatch.setenv("FOO", value)

    def truthy(value):
        return value == "1" or value.lower() in {"true", "on", "yes"}

    class Config(Env):
        foo = Env.var(bool, "FOO", parser=truthy)

    assert Config().foo is expected


def test_env_derived():
    class Config(Env):
        foo = Env.var(int, "FOO", default=42)
        bar = Env.der(str, lambda _: str(_.foo * 2))

    config = Config()

    assert config.foo == 42
    assert config.bar == "84"


def test_env_spec():
    class Config(Env):
        foo = Env.var(int, "FOO", default=42)
        bar = Env.der(bool, lambda conf: conf.foo == conf.spec.foo.default)

    config = Config()

    assert config.foo == 42
    assert config.bar is True


def test_env_prefix(monkeypatch):
    monkeypatch.setenv("TEST_ME_FOO", "24")

    class Config(Env):
        __prefix__ = "test.me."

        foo = Env.var(int, "FOO", default=42)

    assert Config().foo == 24


def test_env_nested_config(monkeypatch):
    monkeypatch.setenv("MYAPP_SERVICE_PORT", "8080")

    class ServiceConfig(Env):
        __prefix__ = "service"

        host = Env.var(str, "host", default="localhost")
        port = Env.var(int, "port", default=3000)

    class GlobalConfig(Env):
        __prefix__ = "myapp"

        debug_mode = Env.var(bool, "debug", default=False)

        service = ServiceConfig

    assert GlobalConfig().service.port == 8080

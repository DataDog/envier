from typing import Optional

import pytest

from envier import En
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


@pytest.mark.parametrize("prefix", ["", "myapp"])
@pytest.mark.parametrize(
    "deprecations,match",
    [
        (
            [("OLD_FOO", "0.1", "1.0")],
            "has been deprecated in version 0.1 and will be removed in version 1.0.",
        ),
        (
            [("OLD_FOO", None, "1.0")],
            "has been deprecated and will be removed in version 1.0.",
        ),
        (
            [("OLD_FOO", "0.1", None)],
            "has been deprecated in version 0.1.",
        ),
        (
            [("OLD_FOO", None, None)],
            "has been deprecated.",
        ),
    ],
)
def test_env_deprecations(monkeypatch, deprecations, match, prefix):
    full_deprecated_name = "_".join((prefix.upper(), "OLD_FOO")).strip("_")
    full_name = "_".join((prefix.upper(), "FOO")).strip("_")

    monkeypatch.setenv(full_deprecated_name, "42")

    class Config(Env):
        __prefix__ = prefix

        foo = Env.var(int, "FOO", deprecations=deprecations)

    message = " ".join((full_deprecated_name, match, "Use %s instead" % full_name))
    with pytest.warns(DeprecationWarning, match=message):
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


def test_env_shorthands():
    class Config(En):
        foo = En.v(int, "FOO", default=42)
        bar = En.d(str, lambda _: str(_.foo * 2))

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

    config = GlobalConfig()
    assert set(config.keys()) == {"debug_mode", "service"}
    assert config.service.port == 8080


def test_env_implicit_nested_config(monkeypatch):
    monkeypatch.setenv("MYAPP_SERVICE_PORT", "8080")

    class GlobalConfig(Env):
        __prefix__ = "myapp"

        debug_mode = Env.var(bool, "debug", default=False)

        class ServiceConfig(Env):
            __item__ = __prefix__ = "service"

            host = Env.var(str, "host", default="localhost")
            port = Env.var(int, "port", default=3000)

    config = GlobalConfig()
    assert set(config.keys()) == {"debug_mode", "service"}
    assert config.service.port == 8080


def test_env_include():
    class GlobalConfig(Env):
        __prefix__ = "myapp"

        debug_mode = Env.var(bool, "debug", default=False)

    class ServiceConfig(Env):
        __prefix__ = "service"

        host = Env.var(str, "host", default="localhost")
        port = Env.var(int, "port", default=3000)

    GlobalConfig.include(ServiceConfig)

    assert GlobalConfig().host == "localhost"


@pytest.mark.parametrize("overwrite", [True, False])
def test_env_include_overlap(overwrite):
    class GlobalConfig(Env):
        __prefix__ = "myapp"

        debug_mode = Env.var(bool, "debug", default=False)
        port = Env.var(int, "port", default=3000)

    class ServiceConfig(Env):
        __prefix__ = "service"

        debug_mode = Env.var(bool, "debug", default=True)

        host = Env.var(str, "host", default="localhost")
        port = Env.var(int, "port", default=3000)

    if not overwrite:
        with pytest.raises(ValueError):
            GlobalConfig.include(ServiceConfig)
    else:
        GlobalConfig.include(ServiceConfig, overwrite=True)

        assert GlobalConfig().debug_mode is True


def test_env_include_namespace(monkeypatch):
    monkeypatch.setenv("MYAPP_SERVICE_HOST", "example.com")

    class GlobalConfig(Env):
        __prefix__ = "myapp"

        debug_mode = Env.var(bool, "debug", default=False)

    class ServiceConfig(Env):
        __prefix__ = "service"

        host = Env.var(str, "host", default="localhost")
        port = Env.var(int, "port", default=3000)

    GlobalConfig.include(ServiceConfig, namespace="service")
    with pytest.raises(ValueError):
        GlobalConfig.include(ServiceConfig, namespace="service")
    GlobalConfig.include(ServiceConfig, namespace="service", overwrite=True)

    assert GlobalConfig().service.host == "example.com"

    # Check that we are not including configuration elsewhere
    with pytest.raises(AttributeError):
        GlobalConfig().host


@pytest.mark.parametrize(
    "map,expected",
    [
        (None, ["1", "2", "3", "4", "5"]),
        (int, [1, 2, 3, 4, 5]),
    ],
)
@pytest.mark.parametrize("_type", [list, set, tuple])
def test_env_collections(monkeypatch, _type, map, expected):
    monkeypatch.setenv("FOO", "1,2,3,4,5")

    class ListConfig(Env):
        foo = Env.var(_type, "FOO", map=map)

    assert ListConfig().foo == _type(expected)


@pytest.mark.parametrize(
    "map,expected",
    [
        (None, {"a": "1", "b": "2", "c": "3"}),
        (lambda k, v: (k.encode(), int(v)), {b"a": 1, b"b": 2, b"c": 3}),
    ],
)
def test_env_dicts(monkeypatch, map, expected):
    monkeypatch.setenv("FOO", "a:1,b:2,c:3")

    class DictConfig(Env):
        foo = Env.var(dict, "FOO", map=map)

    assert DictConfig().foo == expected


def test_env_optional_default():
    class DictConfig(Env):
        foo = Env.var(Optional[str], "foo", default=None)

    assert DictConfig().foo is None


@pytest.mark.parametrize("value,_type", [(1, int), ("1", str)])
def test_env_optional_set(monkeypatch, value, _type):
    monkeypatch.setenv("FOO", str(value))

    class DictConfig(Env):
        foo = Env.var(Optional[_type], "foo", default=None)

    assert DictConfig().foo == value


def test_env_parser_optional(monkeypatch):
    monkeypatch.setenv("FOO", "1")

    class DictConfig(Env):
        foo = Env.var(Optional[str], "foo", parser=lambda _: None, default=None)

    assert DictConfig().foo is None


@pytest.mark.parametrize("value", [1, None])
def test_env_derived_optional(monkeypatch, value):
    monkeypatch.setenv("FOO", "1")

    class DictConfig(Env):
        foo = Env.der(Optional[int], lambda _: value)

    assert DictConfig().foo is value


@pytest.mark.parametrize(
    "value,exc",
    [
        (0, None),
        (512, None),
        (-1, ValueError),
        (513, ValueError),
    ],
)
def test_env_validator(monkeypatch, value, exc):
    monkeypatch.setenv("FOO", str(value))

    class Config(Env):
        def validate(value):
            if not (0 <= value <= 512):
                raise ValueError("Value must be between 0 and 512")

        foo = Env.var(int, "FOO", validator=validate)

    if exc is not None:
        with pytest.raises(exc):
            Config()
    else:
        assert Config().foo == value

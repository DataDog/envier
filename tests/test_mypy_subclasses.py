from textwrap import dedent

import pytest

from tests.test_types import mypy


@pytest.mark.parametrize("owner", ["Env", "Base", "Alias"])
@pytest.mark.parametrize(
    "declaration,value_type",
    [
        ("Base.var(bool, 'enabled', default=False)", "bool"),
        ("Base.v(Optional[bool], 'enabled', default=None)", "Optional[bool]"),
        ("Base.der(bool, lambda _: False)", "bool"),
        ("Base.d(bool, lambda _: False)", "bool"),
        ("Base.var(name='enabled', type=bool, default=False)", "bool"),
        ("Base.v(name='enabled', type=Optional[bool], default=None)", "Optional[bool]"),
        ("Base.der(derivation=lambda _: False, type=bool)", "bool"),
        ("Base.d(derivation=lambda _: False, type=bool)", "bool"),
        ("Base.var(bool, 'enabled', default=DEFAULT)", "bool"),
        ("Base.var(bool, 'enabled', parser=parse, default=False)", "bool"),
        ("Base.var(Enabled, 'enabled', default=False)", "bool"),
    ],
)
def test_subclass_field_type(tmp_path, owner, declaration, value_type):
    declaration = declaration.replace("Base.", f"{owner}.")
    base = "Alias" if owner == "Alias" else "Base"
    path = tmp_path / "config_types.py"
    path.write_text(dedent(f"""\
        from typing import Optional
        from envier import Env

        class Base(Env):
            pass

        Alias = Base

        class Config({base}):
            enabled = {declaration}

        DEFAULT = False
        Enabled = bool

        def parse(value: str) -> bool:
            return bool(value)

        config = Config()

        def enabled() -> {value_type}:
            return config.enabled

        config.enabled = True
        config.enabled = "wrong"
        """))
    out, err, code = mypy(
        "--no-incremental", "--warn-return-any", "--python-version", "3.9", str(path)
    )
    output = out.decode()
    assert not err, err.decode()
    assert code == 1, output
    assert output.count("error:") == 1, output
    assert f'variable has type "{value_type}")  [assignment]' in output, output


@pytest.mark.parametrize("nested_base", ["En", "Env", "Left", "Later"])
def test_multiple_inheritance_nested_item(tmp_path, nested_base):
    path = tmp_path / "nested_types.py"
    path.write_text(dedent(f"""\
        from envier import En, Env

        class Left(Env):
            pass

        class Right(Env):
            pass

        class Config(Left, Right):
            class Nested({nested_base}):
                left, right = (1, 2)
                __item__ = "nested"
                enabled = Env.var(bool, "enabled", default=False)

            class Values(list[int]):
                pass

            class Replacement(En):
                __item__ = "Nested"
                count = Env.var(int, "count", default=0)

        class Later(Env):
            pass

        def enabled() -> bool:
            return Config().nested.enabled

        def count() -> int:
            return Config().Nested.count
        """))
    out, err, code = mypy("--no-incremental", "--warn-return-any", str(path))
    assert not err, err.decode()
    assert code == 0, out.decode()


@pytest.mark.parametrize("maker", ["var", "v", "der", "d"])
@pytest.mark.parametrize("argument", ["1", "int"])
def test_overridden_maker(tmp_path, maker, argument):
    path = tmp_path / "override_types.py"
    path.write_text(dedent(f"""\
        from envier import Env

        class Base(Env):
            @classmethod
            def {maker}(cls, value):
                return value

        class Config(Base):
            value = Base.{maker}({argument})

        reveal_type(Config().value)
        reveal_type(Base.{maker}({argument}))
        """))
    out, err, code = mypy("--no-incremental", str(path))
    assert not err, err.decode()
    assert code == 0, out.decode()
    assert out.decode().count('Revealed type is "Any"') == 2, out.decode()


@pytest.mark.parametrize(
    "call,diagnostic",
    [
        (
            "Base.var(name='enabled', default=False)",
            'Missing positional argument "type"',
        ),
        ("Base.var(*(bool, 'enabled'))", None),
        ("Base.var(value_type, 'enabled')", None),
    ],
)
def test_unsupported_type_argument(tmp_path, call, diagnostic):
    path = tmp_path / "argument_types.py"
    path.write_text(dedent(f"""\
        from typing import Type
        from envier import Env

        class Base(Env):
            pass

        def declare(value_type: Type[bool]) -> None:
            {call}
        """))
    out, err, code = mypy("--no-incremental", str(path))
    assert not err, err.decode()
    if diagnostic is None:
        assert code == 0, out.decode()
    else:
        assert code == 1, out.decode()
        assert diagnostic in out.decode(), out.decode()


@pytest.mark.parametrize(
    "item", ['__item__ = "nes" + "ted"', 'if True:\n    __item__ = "nested"']
)
def test_nonliteral_nested_item(tmp_path, item):
    path = tmp_path / "dynamic_item_types.py"
    path.write_text(
        "from envier import Env\n"
        "class Base(Env): pass\n"
        "class Config(Base):\n"
        "    class Nested(Env):\n"
        + "\n".join("        " + line for line in item.splitlines())
        + "\n    enabled = Env.var(bool, 'enabled', default=False)\n"
        "def enabled() -> bool:\n"
        "    return Config().enabled\n"
    )
    out, err, code = mypy("--no-incremental", "--warn-return-any", str(path))
    assert not err, err.decode()
    assert code == 0, out.decode()


def test_nested_item_incremental_cache(tmp_path):
    config = tmp_path / "cached_config.py"
    config.write_text(dedent("""\
        from typing import Optional, TypeVar, overload
        from envier import Env

        class Base(Env):
            pass

        class Config(Base):
            class Nested(Env):
                __item__ = "nested"
                enabled = Base.v(Optional[bool], "enabled", default=None)
                Result = Optional[bool]
                T = TypeVar("T")

                @property
                def label(self) -> str:
                    return "label"

                @classmethod
                def name(cls) -> str:
                    return "name"

                @overload
                def echo(self, value: int) -> int: ...
                @overload
                def echo(self, value: str) -> str: ...
                def echo(self, value):
                    return value

                class Deeper(Env):
                    __item__ = "deeper"
                    count = Env.var(int, "count", default=0)

            class Replacement(Env):
                __item__ = "Nested"
                count = Env.var(int, "count", default=0)
        """))
    consumer = tmp_path / "consumer.py"
    consumer.write_text(dedent("""\
        from cached_config import Config

        config = Config()
        def label() -> str:
            return config.nested.name()

        config.nested.enabled = "wrong"
        config.nested.deeper.count = "wrong"
        config.Nested.count = "wrong"
        """))
    for _ in range(2):
        out, err, code = mypy(
            "--cache-dir", str(tmp_path / "cache"), "--warn-return-any", str(consumer)
        )
        assert not err, err.decode()
        assert code == 1, out.decode()
        assert out.decode().count("error:") == 3, out.decode()
        assert out.decode().count("[assignment]") == 3, out.decode()

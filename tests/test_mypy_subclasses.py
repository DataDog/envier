from textwrap import dedent

import pytest

from tests.test_types import mypy


@pytest.mark.parametrize("owner", ["Env", "Base"])
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
    ],
)
def test_subclass_field_type(tmp_path, owner, declaration, value_type):
    declaration = declaration.replace("Base.", f"{owner}.")
    path = tmp_path / "config_types.py"
    path.write_text(dedent(f"""\
        from typing import Optional
        from envier import Env

        class Base(Env):
            pass

        class Config(Base):
            enabled = {declaration}

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


@pytest.mark.parametrize("nested_base", ["En", "Env"])
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
                __item__ = "nested"
                enabled = Env.var(bool, "enabled", default=False)

            class Values(list[int]):
                pass

        def enabled() -> bool:
            return Config().nested.enabled
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

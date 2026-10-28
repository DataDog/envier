from textwrap import dedent

import pytest

from tests.test_types import mypy


@pytest.mark.parametrize("owner", ["Base", "Alias", "Base[int]"])
@pytest.mark.parametrize(
    "declaration,value_type",
    [
        ("var(bool, 'enabled', default=False)", "bool"),
        ("v(Optional[bool], 'enabled', default=None)", "Optional[bool]"),
        ("der(bool, lambda _: False)", "bool"),
        ("d(bool, lambda _: False)", "bool"),
        ("var(name='enabled', type=bool, default=False)", "bool"),
        ("v(name='enabled', type=Optional[bool], default=None)", "Optional[bool]"),
        ("der(derivation=lambda _: False, type=bool)", "bool"),
        ("d(derivation=lambda _: False, type=bool)", "bool"),
        ("var(bool, 'enabled', default=DEFAULT)", "bool"),
        ("var(BoolType, 'enabled', default=False)", "bool"),
        ("var(get_type(), 'enabled', default=False)", "bool"),
    ],
)
def test_subclass_field_type(tmp_path, owner, declaration, value_type):
    base = owner if "[" in owner else f"{owner}[int]"
    path = tmp_path / "config_types.py"
    path.write_text(dedent(f"""\
        from typing import Generic, Optional, Type, TypeVar
        from envier import Env

        T = TypeVar("T")
        class Base(Env, Generic[T]):
            pass
        Alias = Base
        BoolType: Type[bool] = bool
        def get_type() -> Type[bool]:
            return bool

        class Config({base}):
            enabled = {owner}.{declaration}
            class Nested(Env):
                left, right = (1, 2)
                __item__ = "nested"

        DEFAULT = False
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


@pytest.mark.parametrize("maker", ["var", "v", "der", "d"])
def test_overridden_maker(tmp_path, maker):
    path = tmp_path / "override_types.py"
    path.write_text(dedent(f"""\
        from envier import Env
        class Base(Env):
            @classmethod
            def {maker}(cls, value):
                return value
        class Config(Base):
            value = Base.{maker}(1)
        reveal_type(Config().value)
        reveal_type(Base.{maker}(1))
        """))
    out, err, code = mypy("--no-incremental", str(path))
    assert not err, err.decode()
    assert code == 0, out.decode()
    assert out.decode().count('Revealed type is "Any"') == 2, out.decode()

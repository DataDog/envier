from textwrap import dedent

import pytest

from tests.test_types import mypy


@pytest.mark.parametrize(
    "declaration,value_type",
    [
        ("Base.var(bool, 'enabled', default=False)", "bool"),
        ("Base.v(Optional[bool], 'enabled', default=None)", "Optional[bool]"),
        ("Base.der(bool, lambda _: False)", "bool"),
        ("Base.d(bool, lambda _: False)", "bool"),
    ],
)
def test_subclass_field_type(tmp_path, declaration, value_type):
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

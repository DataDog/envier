from textwrap import dedent

import pytest

from tests.test_types import mypy


@pytest.mark.parametrize(
    "import_statement,base",
    [
        ("from envier import Env", "Env"),
        ("from envier import En", "En"),
        ("import envier", "envier.Env"),
        ("from envier.env import Env", "Env"),
    ],
)
@pytest.mark.parametrize("invalid_assignments", [False, True])
def test_subclass_types(tmp_path, import_statement, base, invalid_assignments):
    source = dedent("""\
        from typing import Optional
        {import_statement}

        class Base({base}):
            pass

        class Intermediate(Base):
            pass

        class Config(Intermediate):
            enabled = Intermediate.var(bool, "enabled", default=False)
            count = Intermediate.v(int, "count", default=0)
            derived = Intermediate.der(bool, lambda _: True)
            short_derived = Intermediate.d(bool, lambda _: False)
            optional = Intermediate.v(Optional[str], "optional", default=None)
            ordinary = bool(False)

            class Nested(Intermediate):
                __item__ = "nested"
                enabled = Intermediate.var(bool, "nested_enabled", default=False)

        config = Config()
        config.enabled = True
        config.count = 1
        config.derived = False
        config.short_derived = True
        config.optional = "value"
        config.optional = None
        config.nested.enabled = True

        def enabled() -> bool:
            return config.enabled

        def nested_enabled() -> bool:
            return config.nested.enabled
        """).format(import_statement=import_statement, base=base)
    if invalid_assignments:
        source += dedent("""\
            config.enabled = "wrong"
            config.count = "wrong"
            config.derived = "wrong"
            config.short_derived = "wrong"
            config.optional = 42
            config.nested.enabled = "wrong"
            """)

    path = tmp_path / "config_types.py"
    path.write_text(source)
    out, err, code = mypy("--no-incremental", "--warn-return-any", str(path))
    output = out.decode()
    assert not err, err.decode()
    if invalid_assignments:
        assert code == 1, output
        assert output.count("error:") == 6, output
        assert output.count("[assignment]") == 6, output
    else:
        assert code == 0, output

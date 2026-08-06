import subprocess


TYPING_FIXTURE = "tests/types_test.py"
FACTORY_TYPING_FIXTURE = "tests/factory_types_test.py"

EXPECTED_MYPY_ERRORS = """tests/types_test.py:55: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:56: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:57: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:58: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
tests/types_test.py:60: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
Found 5 errors in 1 file (checked 1 source file)
"""


def run_mypy(*args, **kwargs):
    subp = subprocess.Popen(
        ["mypy", "--python-version", "3.9"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        **kwargs,
    )
    stdout, stderr = subp.communicate()
    return stdout, stderr, subp.wait()


def run_pyright(*args, **kwargs):
    subp = subprocess.Popen(
        ["pyright"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        **kwargs,
    )
    stdout, stderr = subp.communicate()
    return stdout, stderr, subp.wait()


def test_mypy_rejects_invalid_assignments_with_plugin():
    out, _, code = run_mypy(TYPING_FIXTURE)
    assert code != 0
    assert out.decode() == EXPECTED_MYPY_ERRORS


def test_mypy_rejects_invalid_assignments_without_plugin():
    out, _, code = run_mypy("--config-file", "tests/mypy_no_plugin.ini", TYPING_FIXTURE)
    assert code != 0
    assert out.decode() == EXPECTED_MYPY_ERRORS


def test_pyright_rejects_invalid_assignments():
    out, _, code = run_pyright(TYPING_FIXTURE)
    output = out.decode()
    assert code != 0
    assert output.count(" - error:") == 5
    assert "5 errors, 0 warnings, 0 informations" in output


def test_factory_and_items_inference():
    for config in ("pyproject.toml", "tests/mypy_no_plugin.ini"):
        stdout, stderr, code = run_mypy("--config-file", config, FACTORY_TYPING_FIXTURE)
        assert code == 0, (stdout + stderr).decode()

    out, _, code = run_pyright(FACTORY_TYPING_FIXTURE)
    assert code == 0, out.decode()

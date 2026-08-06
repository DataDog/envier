import subprocess


EXPECTED_MYPY_OUTPUT = """tests/types_test.py:72: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:73: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:74: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:75: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
tests/types_test.py:77: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:78: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:79: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:80: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
Found 8 errors in 1 file (checked 1 source file)
"""


def mypy(*args, **kwargs):
    subp = subprocess.Popen(
        ["mypy", "--python-version", "3.9"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        **kwargs,
    )
    stdout, stderr = subp.communicate()
    return stdout, stderr, subp.wait()


def pyright(*args, **kwargs):
    subp = subprocess.Popen(
        ["pyright"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        **kwargs,
    )
    stdout, stderr = subp.communicate()
    return stdout, stderr, subp.wait()


def test_types():
    out, _, code = mypy("tests/types_test.py")
    assert code != 0
    assert out.decode() == EXPECTED_MYPY_OUTPUT


def test_mypy_types_without_plugin():
    out, _, code = mypy(
        "--config-file", "tests/mypy_no_plugin.ini", "tests/types_test.py"
    )
    assert code != 0
    assert out.decode() == EXPECTED_MYPY_OUTPUT


def test_pyright_types():
    out, _, code = pyright("tests/types_test.py")
    output = out.decode()
    assert code != 0
    assert output.count(" - error:") == 8
    assert "8 errors, 0 warnings, 0 informations" in output


def test_factory_types():
    for config in ("pyproject.toml", "tests/mypy_no_plugin.ini"):
        stdout, stderr, code = mypy(
            "--config-file", config, "tests/factory_types_test.py"
        )
        assert code == 0, (stdout + stderr).decode()

    out, _, code = pyright("tests/factory_types_test.py")
    assert code == 0, out.decode()

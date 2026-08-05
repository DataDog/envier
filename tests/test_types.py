import subprocess


EXPECTED_MYPY_OUTPUT = """tests/types_test.py:59: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:60: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:61: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:62: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
tests/types_test.py:64: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:65: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:66: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:67: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
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


def test_derivation_owner_types():
    mypy_out, _, mypy_code = mypy(
        "--config-file",
        "tests/mypy_no_plugin.ini",
        "tests/derivation_types_test.py",
    )
    assert mypy_code != 0
    assert b'No overload variant of "__get__"' in mypy_out

    pyright_out, _, pyright_code = pyright("tests/derivation_types_test.py")
    assert pyright_code != 0
    assert b'Cannot access attribute "derived" for class "BadConfig"' in pyright_out

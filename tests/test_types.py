import subprocess
from sys import version_info as PY

import pytest


def mypy(*args, **kwargs):
    subp = subprocess.Popen(
        ["mypy"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        **kwargs
    )
    stdout, stderr = subp.communicate()
    return stdout, stderr, subp.wait()


@pytest.mark.skipif(PY < (3, 6), reason="requires Python 3.6+")
def test_types():
    out, _, code = mypy("tests/types_test.py")
    assert code != 0
    assert (
        out.decode()
        == """tests/types_test.py:28: error: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
tests/types_test.py:29: error: Incompatible types in assignment (expression has type "str", variable has type "CustomObject")  [assignment]
tests/types_test.py:30: error: Incompatible types in assignment (expression has type "bool", variable has type "Optional[str]")  [assignment]
tests/types_test.py:31: error: Incompatible types in assignment (expression has type "bytes", variable has type "Optional[CustomObject]")  [assignment]
Found 4 errors in 1 file (checked 1 source file)
"""
    )

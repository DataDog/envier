from filecmp import cmp
from sys import version_info as PY

import pytest


@pytest.mark.skipif(PY < (3, 6), reason="requires Python 3.6+")
def test(app, rootdir):
    app.build()

    reference = rootdir / "test-root" / "_build" / "index.html"
    generated = app.outdir / "index.html"

    assert cmp(reference, generated)

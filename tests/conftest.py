import sys


if sys.version_info >= (3, 7):
    # DEV: We are not running the Sphinx extension tests on Python < 3.7 due to
    # lack of support.
    import pytest
    from sphinx.testing.path import path

    pytest_plugins = "sphinx.testing.fixtures"

    @pytest.fixture(scope="session")
    def rootdir():
        return path(__file__).parent.abspath() / "sphinx"

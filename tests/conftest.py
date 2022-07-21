try:
    import pytest
    from sphinx.testing.path import path

    pytest_plugins = "sphinx.testing.fixtures"

    @pytest.fixture(scope="session")
    def rootdir():
        return path(__file__).parent.abspath() / "sphinx"


except ImportError:
    import sys

    if sys.version_info >= (3, 6):
        raise

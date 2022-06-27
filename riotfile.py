from ast import Sub

from riot import Venv
from riot import latest


SUPPORTED_PYTHON_VERSIONS = ["2.7", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10"]

venv = Venv(
    venvs=[
        Venv(
            name="tests",
            venvs=[
                Venv(
                    pkgs={"mypy": latest},
                    pys=SUPPORTED_PYTHON_VERSIONS[2:],
                ),
                Venv(pys=SUPPORTED_PYTHON_VERSIONS[:2]),
            ],
            pkgs={"pytest": latest},
            command="pytest {cmdargs}",
        ),
        Venv(
            name="smoke-test",
            command="python -c 'import envier'",
            pys=SUPPORTED_PYTHON_VERSIONS,
        ),
        Venv(
            name="black",
            pkgs={"black": latest},
            command="black {cmdargs}",
            pys=["3"],
        ),
        Venv(
            name="mypy",
            pkgs={"mypy": latest},
            command="mypy {cmdargs}",
            pys=["3"],
        ),
        Venv(
            name="flake8",
            pkgs={
                "flake8": latest,
                "flake8-isort": latest,
            },
            command="flake8 {cmdargs}",
            pys=["3"],
        ),
    ],
)

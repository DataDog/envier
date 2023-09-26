import sys

from riot import Venv
from riot import latest


# Add the current directory to the path so _version.py can be imported.
sys.path.insert(0, ".")
from _version import Version  # noqa: E402

with open("tests/.python-version", "r") as f:
    SUPPORTED_PYTHON_VERSIONS = [
        "%s.%s" % (v.major, v.minor)
        for v in sorted(map(Version, f.read().splitlines()))
    ]

venv = Venv(
    venvs=[
        Venv(
            name="tests",
            venvs=[
                Venv(
                    pkgs={
                        "mypy": "==0.961",
                        "sphinx": "==5.1.1",
                        "alabaster": "==0.7.12",
                    },
                    pys=[
                        p
                        for p in SUPPORTED_PYTHON_VERSIONS
                        if Version(p) >= Version("3.6")
                    ],
                ),
                Venv(
                    pys=[
                        p
                        for p in SUPPORTED_PYTHON_VERSIONS
                        if Version(p) <= Version("3.5")
                    ],
                ),
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
            command="mypy --install-types --non-interactive {cmdargs}",
            pys=["3"],
        ),
        Venv(
            name="flake8",
            pkgs={
                "flake8": "<5",
                "flake8-isort": latest,
            },
            command="flake8 {cmdargs}",
            pys=["3"],
        ),
    ],
)

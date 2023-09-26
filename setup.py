from packaging import version
from setuptools import find_packages
from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()


with open("tests/.python-version", "r") as f:
    python_versions = list(map(version.Version, f.read().splitlines()))


test_deps = [
    "packaging",
    "riot==0.18.0",
]

setup(
    name="envier",
    description="Python application configuration via the environment",
    url="https://github.com/DataDog/envier",
    author="Datadog, Inc.",
    author_email="dev@datadoghq.com",
    classifiers=[
        "Programming Language :: Python",
    ]
    + [
        "Programming Language :: Python :: %s.%s" % (v.major, v.minor)
        for v in sorted(python_versions)
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=%s.%s"
    % (min(python_versions).major, min(python_versions).minor),
    install_requires=["typing; python_version<'3.5'"],
    extras_require={
        "mypy": ["mypy"],
        "test": test_deps,
    },
    setup_requires=["setuptools_scm", "packaging"],
    tests_require=test_deps,
    use_scm_version=True,
    # Required for mypy compatibility, see
    # https://mypy.readthedocs.io/en/stable/installed_packages.html#making-pep-561-compatible-packages
    zip_safe=False,
)

from setuptools import find_packages
from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()


with open("tests/.python-version", "r") as f:
    python_versions = sorted(f.read().splitlines())

min_python_version = python_versions[0].split(".")

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
        "Programming Language :: Python :: %s.%s" % (v[0], v[1])
        for v in [v.split(".") for v in python_versions]
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=%s.%s" % (min_python_version[0], min_python_version[1]),
    install_requires=["typing; python_version<'3.5'"],
    extras_require={"mypy": ["mypy"]},
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    # Required for mypy compatibility, see
    # https://mypy.readthedocs.io/en/stable/installed_packages.html#making-pep-561-compatible-packages
    zip_safe=False,
)

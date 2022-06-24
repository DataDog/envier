from setuptools import find_packages
from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="envier",
    description="Python application configuration via the environment",
    url="https://github.com/DataDog/envier",
    author="Datadog, Inc.",
    author_email="dev@datadoghq.com",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=2.7",
    install_requires=["typing; python_version<'3.5'"],
    extras_require={"mypy": ["mypy"]},
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    # Required for mypy compatibility, see
    # https://mypy.readthedocs.io/en/stable/installed_packages.html#making-pep-561-compatible-packages
    zip_safe=False,
)

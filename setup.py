import pathlib
from setuptools import setup
import setuptools


HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()
packages = setuptools.find_packages()

setup(
    name="hex-helpers",
    version="2.7.1",
    description="A series of light helpers for `freshdesk`,`gmail`,`habitica`,`hue lights`,`jira`,`slack`,`trello`",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Ctri-The-Third/ServiceHelpers",
    author="C'tri",
    author_email="python_packages@ctri.co.uk",
    license="GPL-3.0",
    classifiers=["Programming Language :: Python :: 3.9"],
    package_dir={"models": r"models"},
    packages=packages,
    include_package_data=True,
    install_requires=["requests", "google-api-python-client", "google-auth-oauthlib"],
)

print("complete")

import os
from os import path

from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
parent_directory = os.path.abspath(os.path.join(this_directory, os.pardir))

VERSION = {}
with open(f"{this_directory}/hebsafeharbor/version.py", "r") as version_file:
    exec(version_file.read(), VERSION)

def get_requirements_from_files(*files):
    install_requires = {}
    for filename in files:
        if os.path.isfile(filename):
            with open(filename) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "#" in line:
                            req, version = line.split("#")[0].strip().split("==")
                        else:
                            req, version = line, None

                        # requirement versions must be specified with "==", otherwise the line above will fail
                        if req not in install_requires:
                            install_requires[req] = version
    reqs = []
    for k, v in sorted(install_requires.items()):
        if v:
            reqs.append(f"{k}=={v}")
        else:
            reqs.append(k)
    return reqs


install_requires_ = get_requirements_from_files('requirements.txt')

for requirement in install_requires_:
    print("adding requirement: " + requirement)

try:
    with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""
    print("Could not find README.md - Skipping")

setup(
    name="hebsafeharbor",
    author="hebsafeharbor",
    version=VERSION["VERSION"],
    author_email="hebsafeharbor@gmail.com",
    url="https://github.com/8400TheHealthNetwork/HebSafeHarbor",
    license="MIT License (MIT)",
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="De-identification toolkit for clinical text in Hebrew",
    keywords=["hebrew nlp spacy SpaCy phi pii"],
    packages=find_packages(exclude=["demo"]),
    install_requires=install_requires_,
    python_requires=">=3.8.0",
)

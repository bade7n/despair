import setuptools

import re

with open("README.md", "r") as fh:
    long_description = fh.read()

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('despair/bootstrap.py').read(),
    re.M
    ).group(1)

setuptools.setup(
    name="despire-vladimiri",
    version="0.0.1",
    author="Vladimir I",
    author_email="vladimir.ilmov@gmail.com",
    description="Server bootstrap",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vladimiril/despire",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
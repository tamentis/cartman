#!/usr/bin/env python

import os.path
from setuptools import setup, find_packages

from cartman import __version__


here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, "README.rst")).read()
    CHANGES = open(os.path.join(here, "CHANGES.txt")).read()
except IOError:
    README = CHANGES = ""


setup(
    name="cartman",
    version=__version__,
    description="trac command-line tools",
    long_description=README + "\n\n" + CHANGES,
    author="Bertrand Janin",
    author_email="b@janin.com",
    url="http://tamentis.com/projects/cartman/",
    scripts=["cm"],
    license="ISC License (ISCL, BSD/MIT compatible)",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Framework :: Trac",
        "Topic :: Software Development :: Bug Tracking",
    ],
    install_requires=[
        "requests>=1.2.0",
#        "beautifulsoup4",
    ],
    setup_requires=[
        "nose>=1.0",
        "coverage>=3.5",
    ],
)

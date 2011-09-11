#!/usr/bin/env python

import os.path
from distutils.core import setup

from cartman import __version__

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

setup(
    name="cartman",
    version=__version__,
    description="trac command-line tools",
    long_description=README + "\n\n" + CHANGES,
    author="Bertrand Janin",
    author_email="tamentis@neopulsar.org",
    url="http://github.com/tamentis/tracman/",
    scripts=["cm"],
    packages=["cartman"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Home Automation",
        "Framework :: Trac",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: System :: Monitoring",
    ],
    install_requires=[
        "requests>=0.6.0",
    ],
    setup_requires=[
        "nose>=1.0",
        "coverage>=3.5",
    ],
)

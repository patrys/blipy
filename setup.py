import sys
import os

from distutils.core import setup

version = '0.2'

setup(
    name='blipy',
    version=version,
    description='A Python API for blip.pl.',
    url='http://pypi.python.org/pypi/Blipy',
    packages=['blipy',
              ],
    license='LGPL',
    author='Patryk Zawadzki, Cezary Statkiewicz',
    author_email='patrys@pld-linux.org, c.statkiewicz@gmail.com',
    download_url='http://github.com/patrys/blipy/zipball/master',
    classifiers=[
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    "Natural Language :: Polish",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    )

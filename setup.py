# setup.py
from distutils.core import setup

from setuptools import find_packages

setup(
    name='edgar_prelim',
    version='0.0.1',
    author='Seth Widoff',
    author_email='swidoff@gmail.com',
    url='https://github.com/swidoff/edgar_prelim',
    packages=find_packages(), install_requires=['pytest']
)


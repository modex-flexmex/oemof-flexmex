#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='oemoflex',
    version='0.0.0',
    description='Energy system model of the flexibilities in the European energy system',
    author='Jann Launer',
    author_email='jann.launer@rl-institut.de',
    long_description=read('README.rst'),
    packages=['oemoflex'],
    install_requires=[
        'pandas',
        'oemof',
        'oemof.tabular',
        'pyyaml'
    ],
    extras_require={
        'cartopy': ['cartopy'],
    }
)

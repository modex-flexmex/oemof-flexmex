#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='oemof-flexmex',
    version='0.0.0',
    description='Energy system model of the flexibilities in the European energy system',
    author='Jann Launer',
    author_email='jann.launer@rl-institut.de',
    long_description=read('README.rst'),
    packages=['oemof_flexmex'],
    install_requires=[
        'pandas',
        'oemof.tabular @ git+https://git@github.com/oemof/oemof-tabular@dev#egg=oemof.tabular',
        'pyomo<5.6.9',
        'pyutilib<6.0.0',
        'snakemake',
        'pyyaml',
        'addict',
    ],
)

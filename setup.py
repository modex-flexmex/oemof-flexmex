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
        'oemof',
        'oemof.tabular',
        'pyyaml',
        'addict',
        'Pyomo==5.6.7',
        'PyUtilib==5.7.2',
        'Snakemake>=5.32.0'
    ],
)

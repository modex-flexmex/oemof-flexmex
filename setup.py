#!/usr/bin/env python

from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="oemof-flexmex",
    version="0.0.0",
    description="Energy system model of the flexibilities in the European energy system",
    author="Jann Launer",
    author_email="jann.launer@rl-institut.de",
    long_description=read("README.rst"),
    packages=["oemof_flexmex"],
    install_requires=[
        "pandas",
        "oemof==0.3.2",
        "oemof.tabular==0.0.2",
        "pyyaml",
        "addict",
        "Pyomo==5.6.7",
        "PyUtilib==5.7.2",
        "Snakemake>=5.32.0",
    ],
    # black version is specified so that each contributor uses the same one
    extras_require={"dev": ["pytest", "black==22.3.0", "coverage", "flake8"]},
)

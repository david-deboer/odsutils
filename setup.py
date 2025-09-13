#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2024 David DeBoer
# Licensed under the 2-clause BSD license.

from setuptools import setup
import glob

setup_args = {
    'name': "odsutils",
    'description': "ODS Utils",
    'license': "MIT",
    'author': "David DeBoer",
    'author_email': "david.r.deboer@gmail.edu",
    'version': '0.5.0',
    'scripts': glob.glob('scripts/*'),
    'packages': ['odsutils'],
    'include_package_data': True,
    'package_data': {"odsutils": ['data/*.json']}
}

if __name__ == '__main__':
    setup(**setup_args)

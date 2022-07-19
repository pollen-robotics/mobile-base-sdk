#!/usr/bin/env python
"""Setup config file."""

from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='mobile-base-sdk',
    version='0.1.1',
    packages=find_packages(exclude=['tests']),

    install_requires=[
        'numpy',
        'reachy-sdk-api>=0.6.0',
        'grpcio>=1.37',
        'protobuf>3,<4',
        'pygame',
    ],

    extras_require={
        'doc': ['sphinx'],
    },

    author='Pollen Robotics',
    author_email='contact@pollen-robotics.com',
    url='https://github.com/pollen-robotics/mobile-base-sdk',

    description='Mobile Base SDK for the Reachy robot.',
    long_description=long_description,
    long_description_content_type='text/markdown',
)

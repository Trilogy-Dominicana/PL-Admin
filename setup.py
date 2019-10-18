#!/usr/bin/env python

from setuptools import setup
import os, sys, codecs

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_path = os.path.dirname(__file__)
reqs_file = open(os.path.join(setup_path, 'requirements.txt'), 'r')
reqs = reqs_file.readlines()
reqs_file.close()

setup(
    name="vivapl",
    version="0.0.1",
    description="Python PL/SQL manager",
    long_description=long_description,
    author="Wilowayne De La Cruz",
    author_email="wdelacruz@viva.com.do",
    url="https://gitlab.viva.com.do/anaiboa/pl-pap",
    packages=["vivapl"],
    install_requires=reqs,
    # tests_require=tests_require,
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 1 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

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
    packages=setup.find_packages(),
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







# setup(
#     name='vivapl',  
#     version='0.1',
#     # scripts=['dokr'],
#     author="Deepak Kumar",
#     author_email="deepak.kumar.iet@gmail.com",
#     description="A Docker and AWS utility package",
#     long_description=long_description,
#     long_description_content_type="text/markdown",
#     url="https://github.com/javatechy/dokr",
#     packages=setuptools.find_packages(),
#     classifiers=[
#         "Programming Language :: Python :: 3",
#         "License :: OSI Approved :: MIT License",
#         "Operating System :: OS Independent",
#     ],
#  )


# from setuptools import setup
# tests_require = ['nose', 'mock', 'responses==0.5.1', 'unittest2']


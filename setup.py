#!/usr/bin/python
# -*- coding: utf8 -*-
from setuptools import setup, find_packages

f = open('README')
readme = f.read()
f.close()

setup(name       = 'pyfspot',
    version      = '0.3',
    license      = 'LGPL',
    description  = 'Perform operations on your F-Spot database.',
    author       = "Mathieu Leplatre",
    author_email = "contact@mathieu-leplatre.info",
    url          = "https://github.com/leplatrem/pyfspot/",
    download_url = "http://pypi.python.org/pypi/pyfspot/",
    long_description = readme,
    provides     = ['pyfspot'],
    entry_points = dict(
        console_scripts = [
            'f-spot-admin = pyfspot.main:main',
        ]),
    install_requires=[
        'sqlalchemy',
        'pexif',
        'fixture',
    ],
    packages     = find_packages(),
    platforms    = ('any',),
    keywords     = ['f-spot',],
    classifiers  = ['Programming Language :: Python :: 2.5',
                    'Operating System :: OS Independent',
                    'Intended Audience :: End Users/Desktop',
                    'Natural Language :: English',
                    'Topic :: Utilities',
                    'Development Status :: 3 - Alpha'],
) 

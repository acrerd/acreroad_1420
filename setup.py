#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    "numpy", 
    #"PyQt5"
    # TODO: put package requirements here
]
dependency_links = [ "http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.12.1/PyQt4_gpl_x11-4.12.1.tar.gz"]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='acreroad_1420',
    version='0.1.0',
    description="Control, operation, and analysis code for the 1420 MHz telescope at the Acre Road Observatory, University of Glasgow.",
    long_description=readme + '\n\n' + history,
    author="Daniel Williams",
    author_email='mail@daniel-williams.co.uk',
    url='https://github.com/transientlunatic/acreroad_1420',
    packages=[
        'acreroad_1420',
    ],
    #package_dir={'acreroad_1420':
    #             'acreroad_1420'},
    entry_points = {
        'gui_scripts': [ 'srt_skymap = acreroad_1420.__main__:main'],
        'console_scripts' : ['srt_park = acreroad_1420.__main__:park'],
    },
    include_package_data=True,
    install_requires=requirements,
    dependency_links = dependency_links,
    license="BSD",
    zip_safe=False,
    keywords='acreroad_1420',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

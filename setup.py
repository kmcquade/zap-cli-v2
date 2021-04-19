"""
ZAP CLI tool for targeted tests from the command line.

.. moduleauthor:: Daniel Grunwell (grunny)
"""
import os
import re

from setuptools import setup


HERE = os.path.abspath(os.path.dirname(__file__))
VERSION_RE = re.compile(r"""__version__ = ['"]([0-9.]+)['"]""")
TESTS_REQUIRE = ["coverage", "nose", "pytest", "moto[s3]"]


def get_version():
    init = open(os.path.join(HERE, "zapcli", "version.py")).read()
    return VERSION_RE.search(init).group(1)


with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='zap-cli-v2',
    version=get_version(),
    description='A ZAP CLI tool for targeted tests from the command line.',
    long_description=long_description,
    url='https://github.com/kmcquade/zap-cli-v2',
    author='Daniel Grunwell (grunny)',
    author_email='mwgrunny@gmail.com',
    license='MIT',
    packages=[
        'zapcli',
        'zapcli.commands',
    ],
    install_requires=[
        'click',
        'python-owasp-zap-v2.4',
        'requests',
        'tabulate',
        'termcolor',
        'six',
    ],
    extras_require={
        'dev': [
            'coverage',
            'ddt',
            'mock',
            'pep8',
            'pylint',
            'pytest',
            'responses',
        ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'zap-cli-v2=zapcli.cli:cli',
        ],
    },
    test_suite='tests',
    classifiers=[
        'Topic :: Security',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
    ],
)

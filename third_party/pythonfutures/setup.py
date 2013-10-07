#!/usr/bin/env python
import sys

extras = {}
try:
    from setuptools import setup
    extras['zip_safe'] = False
    if sys.version_info < (2, 6):
        extras['install_requires'] = ['multiprocessing']
except ImportError:
    from distutils.core import setup

setup(name='futures',
      version='2.1.4',
      description='Backport of the concurrent.futures package from Python 3.2',
      author='Brian Quinlan',
      author_email='brian@sweetapp.com',
      maintainer='Alex Gronholm',
      maintainer_email='alex.gronholm+pypi@nextday.fi',
      url='http://code.google.com/p/pythonfutures',
      download_url='http://pypi.python.org/pypi/futures/',
      packages=['futures', 'concurrent', 'concurrent.futures'],
      license='BSD',
      classifiers=['License :: OSI Approved :: BSD License',
                   'Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python :: 2.5',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.1'],
      **extras
      )

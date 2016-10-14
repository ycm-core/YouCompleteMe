# Copyright (C) 2016 YouCompleteMe contributors
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycm.tests.test_utils import MockVimModule
MockVimModule()

from nose.tools import ok_
from ycm.paths import EndsWithPython


def EndsWithPython_Good( path ):
  ok_( EndsWithPython( path ) )


def EndsWithPython_Bad( path ):
  ok_( not EndsWithPython( path ) )


def EndsWithPython_Python2Paths_test():
  python_paths = [
    'python',
    'python2',
    '/usr/bin/python2.6',
    '/home/user/.pyenv/shims/python2.7',
    r'C:\Python26\python.exe'
  ]

  for path in python_paths:
    yield EndsWithPython_Good, path



def EndsWithPython_Python3Paths_test():
  python_paths = [
    'python3',
    '/usr/bin/python3.3',
    '/home/user/.pyenv/shims/python3.3',
    r'C:\Python33\python.exe'
  ]

  for path in python_paths:
    yield EndsWithPython_Good, path


def EndsWithPython_BadPaths_test():
  not_python_paths = [
    None,
    '',
    '/opt/local/bin/vim',
    r'C:\Program Files\Vim\vim74\gvim.exe',
    '/usr/bin/python2.5',
    '/home/user/.pyenv/shims/python3.2',
  ]

  for path in not_python_paths:
    yield EndsWithPython_Bad, path

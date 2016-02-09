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

from ycm.test_utils import MockVimModule
MockVimModule()

from nose.tools import ok_
from ycm.paths import EndsWithPython


def EndsWithPython_Python2Paths_test():
  python_paths = [
    'python',
    '/usr/bin/python2.6',
    '/home/user/.pyenv/shims/python2.7',
    r'C:\Python26\python.exe'
  ]

  for path in python_paths:
    ok_( EndsWithPython( path ) )


def EndsWithPython_NotPython2Paths_test():
  not_python_paths = [
    '/opt/local/bin/vim',
    r'C:\Program Files\Vim\vim74\gvim.exe',
    '/usr/bin/python3',
    '/home/user/.pyenv/shims/python3',
  ]

  for path in not_python_paths:
    ok_( not EndsWithPython( path ) )

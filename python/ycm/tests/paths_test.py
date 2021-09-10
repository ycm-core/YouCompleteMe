# Copyright (C) 2016-2017 YouCompleteMe contributors
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

from ycm.tests.test_utils import MockVimModule
MockVimModule()

from hamcrest import assert_that
from unittest import TestCase
from ycm.paths import _EndsWithPython


def EndsWithPython_Good( path ):
  assert_that( _EndsWithPython( path ),
              f'Path { path } does not end with a Python name.' )


def EndsWithPython_Bad( path ):
  assert_that( not _EndsWithPython( path ),
              f'Path { path } does end with a Python name.' )


class PathTest( TestCase ):
  def test_EndsWithPython_Python3Paths( self ):
    for path in [
      'python3',
      '/usr/bin/python3.6',
      '/home/user/.pyenv/shims/python3.6',
      r'C:\Python36\python.exe'
    ]:
      with self.subTest( path = path ):
        EndsWithPython_Good( path )


  def test_EndsWithPython_BadPaths( self ):
    for path in [
      None,
      '',
      '/opt/local/bin/vim',
      r'C:\Program Files\Vim\vim74\gvim.exe',
      '/usr/bin/python2.7',
      '/home/user/.pyenv/shims/python3.2',
    ]:
      with self.subTest( path = path ):
        EndsWithPython_Bad( path )

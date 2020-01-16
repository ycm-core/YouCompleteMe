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

import pytest
from hamcrest import assert_that
from ycm.paths import _EndsWithPython


def EndsWithPython_Good( path ):
  assert_that( _EndsWithPython( path ),
              'Path {0} does not end with a Python name.'.format( path ) )


def EndsWithPython_Bad( path ):
  assert_that( not _EndsWithPython( path ),
              'Path {0} does end with a Python name.'.format( path ) )


@pytest.mark.parametrize( 'path', [
    'python3',
    '/usr/bin/python3.5',
    '/home/user/.pyenv/shims/python3.5',
    r'C:\Python35\python.exe'
  ] )
def EndsWithPython_Python3Paths_test( path ):
  EndsWithPython_Good( path )


@pytest.mark.parametrize( 'path', [
    None,
    '',
    '/opt/local/bin/vim',
    r'C:\Program Files\Vim\vim74\gvim.exe',
    '/usr/bin/python2.7',
    '/home/user/.pyenv/shims/python3.2',
  ] )
def EndsWithPython_BadPaths_test( path ):
  EndsWithPython_Bad( path )

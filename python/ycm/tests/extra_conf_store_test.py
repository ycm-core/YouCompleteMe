#!/usr/bin/env python
#
# Copyright (C) 2013  Google Inc.
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

from nose.tools import eq_
from ycm.test_utils import MockVimModule
vim_mock = MockVimModule()
from ycm.extra_conf_store import _PathsToAllParentFolders


def PathsToAllParentFolders_Basic_test():
  eq_( [ '/home/user/projects', '/home/user', '/home', '/' ],
       list( _PathsToAllParentFolders( '/home/user/projects/test.c' ) ) )

def PathsToAllParentFolders_FileAtRoot_test():
  eq_( [ '/' ],
       list( _PathsToAllParentFolders( '/test.c' ) ) )

# We can't use backwards slashes in the paths because then the test would fail
# on Unix machines
def PathsToAllParentFolders_WindowsPath_test():
  eq_( [ r'C:/foo/goo/zoo', r'C:/foo/goo', r'C:/foo', 'C:' ],
       list( _PathsToAllParentFolders( r'C:/foo/goo/zoo/test.c' ) ) )



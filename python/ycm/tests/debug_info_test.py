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

from ycm.tests.test_utils import MockVimBuffers, MockVimModule, VimBuffer
MockVimModule()

from hamcrest import assert_that, matches_regexp

from ycm.tests import YouCompleteMeInstance


@YouCompleteMeInstance()
def DebugInfo_test( ycm ):
  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Server Python interpreter: .+\n'
        'Server Python version: .+\n'
        'Server has Clang support compiled in: (True|False)\n'
        'Clang version: .+\n'
        'No extra configuration file found\n'
        'Server running at: .+\n'
        'Server process ID: \d+\n'
        'Server logfiles:\n'
        '  .+\n'
        '  .+' )
    )

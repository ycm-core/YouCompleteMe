# coding: utf-8
#
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

from ycm.tests.test_utils import ( CurrentWorkingDirectory, MockVimModule,
                                   VimBuffer )
MockVimModule()

from hamcrest import assert_that, empty, has_entries
from mock import patch

from ycm.tests import PathToTestFile, YouCompleteMeInstance


@YouCompleteMeInstance()
def CreateCompletionRequest_UnicodeWorkingDirectory_test( ycm ):
  unicode_dir = PathToTestFile( 'uni¢𐍈d€' )
  current_buffer = VimBuffer( PathToTestFile( 'uni¢𐍈d€', 'current_buffer' ) )

  with CurrentWorkingDirectory( unicode_dir ):
    with patch( 'vim.buffers', [ current_buffer ] ):
      with patch( 'vim.current.buffer', current_buffer ):
        with patch( 'vim.current.window.cursor', ( 5, 2 ) ):
          ycm.CreateCompletionRequest(),

    results = ycm.GetCompletions()

  assert_that(
    results,
    has_entries( {
      'words': empty(),
      'refresh': 'always'
    } )
  )

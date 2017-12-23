# Copyright (C) 2017 YouCompleteMe Contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.tests.test_utils import MockVimModule
MockVimModule()

from hamcrest import assert_that, has_entry
from mock import patch
from ycm.client.base_request import BuildRequestData


@patch( 'ycm.client.base_request.GetCurrentDirectory',
        return_value = '/some/dir' )
@patch( 'ycm.vimsupport.CurrentLineAndColumn', return_value = ( 1, 1 ) )
def BuildRequestData_AddWorkingDir_test( *args ):
  assert_that( BuildRequestData(), has_entry( 'working_dir', '/some/dir' ) )


@patch( 'ycm.client.base_request.GetCurrentDirectory',
        return_value = '/some/dir' )
@patch( 'ycm.vimsupport.CurrentLineAndColumn', return_value = ( 1, 1 ) )
def BuildRequestData_AddWorkingDirWithFileName_test( *args ):
  assert_that( BuildRequestData( 'foo' ),
               has_entry( 'working_dir', '/some/dir' ) )

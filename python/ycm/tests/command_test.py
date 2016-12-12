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

from ycm.tests.test_utils import ( MockVimModule, MockVimBuffers, VimBuffer )
MockVimModule()

from hamcrest import assert_that, equal_to
from mock import patch

from ycm.tests import YouCompleteMeInstance


@YouCompleteMeInstance()
def SendCommandRequest_test( ycm ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.base_request.JsonFromFuture',
                return_value = 'Some response' ):
      assert_that(
        ycm.SendCommandRequest( 'GoTo', 'python' ),
        equal_to( 'Some response' )
      )

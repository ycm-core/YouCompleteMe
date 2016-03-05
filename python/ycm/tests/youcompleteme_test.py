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

from ycm.test_utils import MockVimModule
MockVimModule()

import sys
from mock import MagicMock
from hamcrest import assert_that, is_in, is_not

from ycm.youcompleteme import YouCompleteMe


class YouCompleteMe_test():

  def setUp( self ):
    self.ycm = YouCompleteMe( MagicMock( spec_set = dict ) )


  def tearDown( self ):
    self.ycm.OnVimLeave()


  def YcmCoreNotImported_test( self ):
    assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )

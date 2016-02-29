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

from mock import patch
from hamcrest import assert_that, is_in, is_not

from ycm import base
from ycm.youcompleteme import YouCompleteMe
from ycmd import user_options_store


class YouCompleteMe_test():

  # Minimal options to create the YouCompleteMe object.
  DEFAULT_OPTIONS = {
    'ycm_server_log_level': 'info',
    'ycm_server_keep_logfiles': 0,
    'ycm_min_num_of_chars_for_completion': 2,
    'ycm_auto_trigger': 1,
    'ycm_semantic_triggers': {}
  }


  def setUp( self ):
    with patch( 'vim.eval', side_effect = self.VimEval ):
      user_options_store.SetAll( base.BuildServerConf() )
      self.ycm = YouCompleteMe( user_options_store.GetAll() )


  def tearDown( self ):
    self.ycm.OnVimLeave()


  def VimEval( self, value ):
    if value == 'g:':
      return self.DEFAULT_OPTIONS


  def YcmCoreNotImported_test( self ):
    assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )

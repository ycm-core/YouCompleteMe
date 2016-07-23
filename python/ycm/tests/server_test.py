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

import requests
import time

from ycm.client.base_request import BaseRequest
from ycm.youcompleteme import YouCompleteMe
from ycmd import user_options_store

# The default options which are only relevant to the client, not the server and
# thus are not part of default_options.json, but are required for a working
# YouCompleteMe or OmniCompleter object.
DEFAULT_CLIENT_OPTIONS = {
  'server_log_level': 'info',
  'extra_conf_vim_data': [],
  'show_diagnostics_ui': 1,
  'enable_diagnostic_signs': 1,
  'enable_diagnostic_highlighting': 0,
  'always_populate_location_list': 0,
}


def MakeUserOptions( custom_options = {} ):
  options = dict( user_options_store.DefaultOptions() )
  options.update( DEFAULT_CLIENT_OPTIONS )
  options.update( custom_options )
  return options


class Server_test():

  def _IsReady( self ):
    return BaseRequest.GetDataFromHandler( 'ready' )


  def _WaitUntilReady( self, timeout = 5 ):
    total_slept = 0
    while True:
      try:
        if total_slept > timeout:
          raise RuntimeError( 'Waited for the server to be ready '
                              'for {0} seconds, aborting.'.format(
                                timeout ) )

        if self._IsReady():
          return
      except requests.exceptions.ConnectionError:
        pass
      finally:
        time.sleep( 0.1 )
        total_slept += 0.1


  def setUp( self ):
    self._server_state = YouCompleteMe( MakeUserOptions() )
    self._WaitUntilReady()


  def tearDown( self ):
    self._server_state.OnVimLeave()

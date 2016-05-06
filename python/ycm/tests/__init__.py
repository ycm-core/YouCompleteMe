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

from ycm.tests.test_utils import MockVimModule
MockVimModule()

import functools
import os
import requests
import time

from ycm.client.base_request import BaseRequest
from ycm.youcompleteme import YouCompleteMe
from ycmd import user_options_store
from ycmd.utils import WaitUntilProcessIsTerminated

# The default options which are only relevant to the client, not the server and
# thus are not part of default_options.json, but are required for a working
# YouCompleteMe object.
DEFAULT_CLIENT_OPTIONS = {
  'log_level': 'info',
  'keep_logfiles': 0,
  'extra_conf_vim_data': [],
  'show_diagnostics_ui': 1,
  'enable_diagnostic_signs': 1,
  'enable_diagnostic_highlighting': 0,
  'always_populate_location_list': 0,
}


def PathToTestFile( *args ):
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'testdata', *args )


def _MakeUserOptions( custom_options = {} ):
  options = dict( user_options_store.DefaultOptions() )
  options.update( DEFAULT_CLIENT_OPTIONS )
  options.update( custom_options )
  return options


def _IsReady():
  return BaseRequest.GetDataFromHandler( 'ready' )


def _WaitUntilReady( timeout = 5 ):
  expiration = time.time() + timeout
  while True:
    try:
      if time.time() > expiration:
        raise RuntimeError( 'Waited for the server to be ready '
                            'for {0} seconds, aborting.'.format( timeout ) )
      if _IsReady():
        return
    except requests.exceptions.ConnectionError:
      pass
    finally:
      time.sleep( 0.1 )


def StopServer( ycm ):
  try:
    ycm.OnVimLeave()
    WaitUntilProcessIsTerminated( ycm._server_popen )
  except Exception:
    pass


def YouCompleteMeInstance( custom_options = {} ):
  """Defines a decorator function for tests that passes a unique YouCompleteMe
  instance as a parameter. This instance is initialized with the default options
  `DEFAULT_CLIENT_OPTIONS`. Use the optional parameter |custom_options| to give
  additional options and/or override the already existing ones.

  Do NOT attach it to test generators but directly to the yielded tests.

  Example usage:

    from ycm.tests import YouCompleteMeInstance

    @YouCompleteMeInstance( { 'log_level': 'debug',
                              'keep_logfiles': 1 } )
    def Debug_test( ycm ):
        ...
  """
  def Decorator( test ):
    @functools.wraps( test )
    def Wrapper( *args, **kwargs ):
      ycm = YouCompleteMe( _MakeUserOptions( custom_options ) )
      _WaitUntilReady()
      try:
        test( ycm, *args, **kwargs )
      finally:
        StopServer( ycm )
    return Wrapper
  return Decorator

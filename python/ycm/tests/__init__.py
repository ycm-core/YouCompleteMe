# Copyright (C) 2016-2020 YouCompleteMe contributors
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

import os
from ycm.tests.test_utils import MockVimModule
MockVimModule()

import contextlib
import functools
import time
from urllib.error import HTTPError, URLError

from ycm.client.base_request import BaseRequest
from ycm.tests import test_utils
from ycm.youcompleteme import YouCompleteMe
from ycmd.utils import CloseStandardStreams, WaitUntilProcessIsTerminated


def PathToTestFile( *args ):
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'testdata', *args )


# The default options which are required for a working YouCompleteMe object.
DEFAULT_CLIENT_OPTIONS = {
  # YCM options
  'g:ycm_log_level': 'info',
  'g:ycm_keep_logfiles': 0,
  'g:ycm_extra_conf_vim_data': [],
  'g:ycm_server_python_interpreter': '',
  'g:ycm_show_diagnostics_ui': 1,
  'g:ycm_enable_diagnostic_signs': 1,
  'g:ycm_enable_diagnostic_highlighting': 0,
  'g:ycm_echo_current_diagnostic': 1,
  'g:ycm_filter_diagnostics': {},
  'g:ycm_always_populate_location_list': 0,
  'g:ycm_open_loclist_on_ycm_diags': 1,
  'g:ycm_collect_identifiers_from_tags_files': 0,
  'g:ycm_seed_identifiers_with_syntax': 0,
  'g:ycm_goto_buffer_command': 'same-buffer',
  'g:ycm_update_diagnostics_in_insert_mode': 1,
  # ycmd options
  'g:ycm_auto_trigger': 1,
  'g:ycm_min_num_of_chars_for_completion': 2,
  'g:ycm_semantic_triggers': {},
  'g:ycm_filetype_specific_completion_to_disable': { 'gitcommit': 1 },
  'g:ycm_max_num_candidates': 50,
  'g:ycm_max_diagnostics_to_display': 30,
  'g:ycm_disable_signature_help': 0,
}


@contextlib.contextmanager
def UserOptions( options ):
  old_vim_options = test_utils.VIM_OPTIONS.copy()
  test_utils.VIM_OPTIONS.update( DEFAULT_CLIENT_OPTIONS )
  test_utils.VIM_OPTIONS.update( options )
  try:
    yield
  finally:
    test_utils.VIM_OPTIONS = old_vim_options


def _IsReady():
  return BaseRequest().GetDataFromHandler( 'ready' )


def WaitUntilReady( timeout = 5 ):
  expiration = time.time() + timeout
  while True:
    try:
      if time.time() > expiration:
        raise RuntimeError( 'Waited for the server to be ready '
                            f'for { timeout } seconds, aborting.' )
      if _IsReady():
        return
    except ( URLError, HTTPError ):
      pass
    finally:
      time.sleep( 0.1 )


def StopServer( ycm ):
  try:
    ycm.OnVimLeave()
    WaitUntilProcessIsTerminated( ycm._server_popen )
    CloseStandardStreams( ycm._server_popen )
  except Exception:
    pass


def YouCompleteMeInstance( custom_options = {} ):
  """Defines a decorator function for tests that passes a unique YouCompleteMe
  instance as a parameter. This instance is initialized with the default options
  `DEFAULT_CLIENT_OPTIONS`. Use the optional parameter |custom_options| to give
  additional options and/or override the already existing ones.

  Example usage:

    from ycm.tests import YouCompleteMeInstance

    @YouCompleteMeInstance( { 'log_level': 'debug',
                              'keep_logfiles': 1 } )
    def Debug_test( ycm ):
        ...
  """
  def Decorator( test ):
    @functools.wraps( test )
    def Wrapper( test_case_instance, *args, **kwargs ):
      with UserOptions( custom_options ):
        ycm = YouCompleteMe()
        WaitUntilReady()
        ycm.CheckIfServerIsReady()
        try:
          test_utils.VIM_PROPS_FOR_BUFFER.clear()
          return test( test_case_instance, ycm, *args, **kwargs )
        finally:
          StopServer( ycm )
    return Wrapper
  return Decorator


@contextlib.contextmanager
def youcompleteme_instance( custom_options = {} ):
  """Defines a context manager to be used in case a shared YCM state
  between subtests is to be avoided, as could be the case with completion
  caching."""
  with UserOptions( custom_options ):
    ycm = YouCompleteMe()
    WaitUntilReady()
    try:
      test_utils.VIM_PROPS_FOR_BUFFER.clear()
      yield ycm
    finally:
      StopServer( ycm )

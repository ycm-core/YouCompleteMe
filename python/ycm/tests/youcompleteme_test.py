# Copyright (C) 2016-2018 YouCompleteMe contributors
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

from ycm.tests.test_utils import ( ExtendedMock,
                                   MockVimBuffers,
                                   MockVimModule,
                                   Version,
                                   VimBuffer,
                                   VimMatch,
                                   VimSign )
MockVimModule()

import os
import sys
from hamcrest import ( assert_that, contains, empty, equal_to, has_entries,
                       is_in, is_not, matches_regexp )
from mock import call, MagicMock, patch

from ycm import vimsupport
from ycm.paths import _PathToPythonUsedDuringBuild
from ycm.vimsupport import ( SetVariableValue,
                             SIGN_BUFFER_ID_INITIAL_VALUE )
from ycm.tests import ( StopServer,
                        test_utils,
                        UserOptions,
                        WaitUntilReady,
                        YouCompleteMeInstance )
from ycm.client.base_request import _LoadExtraConfFile
from ycm.youcompleteme import YouCompleteMe
from ycmd.responses import ServerError
from ycm.tests.mock_utils import ( MockAsyncServerResponseDone,
                                   MockAsyncServerResponseInProgress,
                                   MockAsyncServerResponseException )


from ycm import buffer as ycm_buffer_module


@YouCompleteMeInstance()
def YouCompleteMe_YcmCoreNotImported_test( ycm ):
  assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )


@patch( 'ycm.vimsupport.PostVimMessage' )
def YouCompleteMe_InvalidPythonInterpreterPath_test( post_vim_message ):
  with UserOptions( {
    'g:ycm_server_python_interpreter': '/invalid/python/path' } ):
    try:
      ycm = YouCompleteMe()

      assert_that( ycm.IsServerAlive(), equal_to( False ) )
      post_vim_message.assert_called_once_with(
        "Unable to start the ycmd server. "
        "Path in 'g:ycm_server_python_interpreter' option does not point "
        "to a valid Python 2.7 or 3.4+. "
        "Correct the error then restart the server with ':YcmRestartServer'." )

      post_vim_message.reset_mock()

      SetVariableValue( 'g:ycm_server_python_interpreter',
                        _PathToPythonUsedDuringBuild() )
      ycm.RestartServer()

      assert_that( ycm.IsServerAlive(), equal_to( True ) )
      post_vim_message.assert_called_once_with( 'Restarting ycmd server...' )
    finally:
      WaitUntilReady()
      StopServer( ycm )


@patch( 'ycmd.utils.PathToFirstExistingExecutable', return_value = None )
@patch( 'ycm.paths._EndsWithPython', return_value = False )
@patch( 'ycm.vimsupport.PostVimMessage' )
def YouCompleteMe_NoPythonInterpreterFound_test( post_vim_message, *args ):
  with UserOptions( {} ):
    try:
      with patch( 'ycmd.utils.ReadFile', side_effect = IOError ):
        ycm = YouCompleteMe()

      assert_that( ycm.IsServerAlive(), equal_to( False ) )
      post_vim_message.assert_called_once_with(
        "Unable to start the ycmd server. Cannot find Python 2.7 or 3.4+. "
        "Set the 'g:ycm_server_python_interpreter' option to a Python "
        "interpreter path. "
        "Correct the error then restart the server with ':YcmRestartServer'." )

      post_vim_message.reset_mock()

      SetVariableValue( 'g:ycm_server_python_interpreter',
                        _PathToPythonUsedDuringBuild() )
      ycm.RestartServer()

      assert_that( ycm.IsServerAlive(), equal_to( True ) )
      post_vim_message.assert_called_once_with( 'Restarting ycmd server...' )
    finally:
      WaitUntilReady()
      StopServer( ycm )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def RunNotifyUserIfServerCrashed( ycm, test, post_vim_message ):
  StopServer( ycm )

  ycm._logger = MagicMock( autospec = True )
  ycm._server_popen = MagicMock( autospec = True )
  ycm._server_popen.poll.return_value = test[ 'return_code' ]

  ycm.OnFileReadyToParse()

  assert_that( ycm._logger.error.call_args[ 0 ][ 0 ],
               test[ 'expected_message' ] )
  assert_that( post_vim_message.call_args[ 0 ][ 0 ],
               test[ 'expected_message' ] )


def YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedCore_test():
  message = (
    "The ycmd server SHUT DOWN \\(restart with ':YcmRestartServer'\\). "
    "Unexpected error while loading the YCM core library. Type "
    "':YcmToggleLogs ycmd_\\d+_stderr_.+.log' to check the logs." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 3,
    'expected_message': matches_regexp( message )
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_MissingCore_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library not detected; you need to compile YCM before "
              "using it. Follow the instructions in the documentation." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 4,
    'expected_message': equal_to( message )
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_Python2Core_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library compiled for Python 2 but loaded in Python 3. "
              "Set the 'g:ycm_server_python_interpreter' option to a Python 2 "
              "interpreter path." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 5,
    'expected_message': equal_to( message )
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_Python3Core_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library compiled for Python 3 but loaded in Python 2. "
              "Set the 'g:ycm_server_python_interpreter' option to a Python 3 "
              "interpreter path." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 6,
    'expected_message': equal_to( message )
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_OutdatedCore_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library too old; PLEASE RECOMPILE by running the "
              "install.py script. See the documentation for more details." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 7,
    'expected_message': equal_to( message )
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedExitCode_test():
  message = (
    "The ycmd server SHUT DOWN \\(restart with ':YcmRestartServer'\\). "
    "Unexpected exit code 1. Type "
    "':YcmToggleLogs ycmd_\\d+_stderr_.+.log' to check the logs." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 1,
    'expected_message': matches_regexp( message )
  } )


@YouCompleteMeInstance( { 'g:ycm_extra_conf_vim_data': [ 'tempname()' ] } )
def YouCompleteMe_DebugInfo_ServerRunning_test( ycm ):
  dir_of_script = os.path.dirname( os.path.abspath( __file__ ) )
  buf_name = os.path.join( dir_of_script, 'testdata', 'test.cpp' )
  extra_conf = os.path.join( dir_of_script, 'testdata', '.ycm_extra_conf.py' )
  _LoadExtraConfFile( extra_conf )

  current_buffer = VimBuffer( buf_name, filetype = 'cpp' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Client logfile: .+\n'
        'Server Python interpreter: .+\n'
        'Server Python version: .+\n'
        'Server has Clang support compiled in: (False|True)\n'
        'Clang version: .+\n'
        'Extra configuration file found and loaded\n'
        'Extra configuration path: .*testdata[/\\\\]\\.ycm_extra_conf\\.py\n'
        '[\\w\\W]*'
        'Server running at: .+\n'
        'Server process ID: \\d+\n'
        'Server logfiles:\n'
        '  .+\n'
        '  .+' )
    )


@YouCompleteMeInstance()
def YouCompleteMe_DebugInfo_ServerNotRunning_test( ycm ):
  StopServer( ycm )

  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Client logfile: .+\n'
        'Server errored, no debug info from server\n'
        'Server running at: .+\n'
        'Server process ID: \\d+\n'
        'Server logfiles:\n'
        '  .+\n'
        '  .+' )
    )


@YouCompleteMeInstance()
def YouCompleteMe_OnVimLeave_RemoveClientLogfileByDefault_test( ycm ):
  client_logfile = ycm._client_logfile
  assert_that( os.path.isfile( client_logfile ),
               'Logfile {0} does not exist.'.format( client_logfile ) )
  ycm.OnVimLeave()
  assert_that( not os.path.isfile( client_logfile ),
               'Logfile {0} was not removed.'.format( client_logfile ) )


@YouCompleteMeInstance( { 'g:ycm_keep_logfiles': 1 } )
def YouCompleteMe_OnVimLeave_KeepClientLogfile_test( ycm ):
  client_logfile = ycm._client_logfile
  assert_that( os.path.isfile( client_logfile ),
               'Logfile {0} does not exist.'.format( client_logfile ) )
  ycm.OnVimLeave()
  assert_that( os.path.isfile( client_logfile ),
               'Logfile {0} was removed.'.format( client_logfile ) )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.CloseBuffersForFilename', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenFilename', new_callable = ExtendedMock )
def YouCompleteMe_ToggleLogs_WithParameters_test( ycm,
                                                  open_filename,
                                                  close_buffers_for_filename ):
  logfile_buffer = VimBuffer( ycm._client_logfile )
  with MockVimBuffers( [ logfile_buffer ], [ logfile_buffer ] ):
    ycm.ToggleLogs( os.path.basename( ycm._client_logfile ),
                    'nonexisting_logfile',
                    os.path.basename( ycm._server_stdout ) )

    open_filename.assert_has_exact_calls( [
      call( ycm._server_stdout, { 'size': 12,
                                  'watch': True,
                                  'fix': True,
                                  'focus': False,
                                  'position': 'end' } )
    ] )
    close_buffers_for_filename.assert_has_exact_calls( [
      call( ycm._client_logfile )
    ] )


@YouCompleteMeInstance()
# Select the second item of the list which is the ycmd stderr logfile.
@patch( 'ycm.vimsupport.SelectFromList', return_value = 1 )
@patch( 'ycm.vimsupport.OpenFilename', new_callable = ExtendedMock )
def YouCompleteMe_ToggleLogs_WithoutParameters_SelectLogfileNotAlreadyOpen_test(
  ycm, open_filename, *args ):

  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    ycm.ToggleLogs()

  open_filename.assert_has_exact_calls( [
    call( ycm._server_stderr, { 'size': 12,
                                'watch': True,
                                'fix': True,
                                'focus': False,
                                'position': 'end' } )
  ] )


@YouCompleteMeInstance()
# Select the third item of the list which is the ycmd stdout logfile.
@patch( 'ycm.vimsupport.SelectFromList', return_value = 2 )
@patch( 'ycm.vimsupport.CloseBuffersForFilename', new_callable = ExtendedMock )
def YouCompleteMe_ToggleLogs_WithoutParameters_SelectLogfileAlreadyOpen_test(
  ycm, close_buffers_for_filename, *args ):

  logfile_buffer = VimBuffer( ycm._server_stdout )
  with MockVimBuffers( [ logfile_buffer ], [ logfile_buffer ] ):
    ycm.ToggleLogs()

  close_buffers_for_filename.assert_has_exact_calls( [
    call( ycm._server_stdout )
  ] )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.SelectFromList',
        side_effect = RuntimeError( 'Error message' ) )
@patch( 'ycm.vimsupport.PostVimMessage' )
def YouCompleteMe_ToggleLogs_WithoutParameters_NoSelection_test(
  ycm, post_vim_message, *args ):

  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    ycm.ToggleLogs()

  assert_that(
    # Argument passed to PostVimMessage.
    post_vim_message.call_args[ 0 ][ 0 ],
    equal_to( 'Error message' )
  )


@YouCompleteMeInstance()
def YouCompleteMe_GetDefinedSubcommands_ListFromServer_test( ycm ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.base_request._JsonFromFuture',
                return_value = [ 'SomeCommand', 'AnotherCommand' ] ):
      assert_that(
        ycm.GetDefinedSubcommands(),
        contains(
          'SomeCommand',
          'AnotherCommand'
        )
      )


@YouCompleteMeInstance()
@patch( 'ycm.client.base_request._logger', autospec = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_GetDefinedSubcommands_ErrorFromServer_test( ycm,
                                                              post_vim_message,
                                                              logger ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.base_request._JsonFromFuture',
                side_effect = ServerError( 'Server error' ) ):
      result = ycm.GetDefinedSubcommands()

  logger.exception.assert_called_with( 'Error while handling server response' )
  post_vim_message.assert_has_exact_calls( [
    call( 'Server error', truncate = False )
  ] )
  assert_that( result, empty() )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_ShowDetailedDiagnostic_MessageFromServer_test(
  ycm, post_vim_message ):

  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.base_request._JsonFromFuture',
                return_value = { 'message': 'some_detailed_diagnostic' } ):
      ycm.ShowDetailedDiagnostic(),

  post_vim_message.assert_has_exact_calls( [
    call( 'some_detailed_diagnostic', warning = False )
  ] )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_ShowDetailedDiagnostic_Exception_test(
  ycm, post_vim_message ):

  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.base_request._JsonFromFuture',
                side_effect = RuntimeError( 'Some exception' ) ):
      ycm.ShowDetailedDiagnostic(),

  post_vim_message.assert_has_exact_calls( [
    call( 'Some exception', truncate = False )
  ] )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_FiletypeNotSupported_test( ycm,
                                                             post_vim_message ):

  current_buffer = VimBuffer( 'buffer', filetype = 'not_supported' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    ycm.ShowDiagnostics()

  post_vim_message.assert_called_once_with(
    'Native filetype completion not supported for current file, '
    'cannot force recompilation.', warning = False )


@YouCompleteMeInstance()
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationListForWindow', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_NoDiagnosticsDetected_test(
  ycm, set_location_list_for_window, post_vim_message, *args ):

  current_buffer = VimBuffer( 'buffer', filetype = 'cpp' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = {} ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False ),
    call( 'No warnings or errors detected.', warning = False )
  ] )
  set_location_list_for_window.assert_called_once_with( 1, [] )


@YouCompleteMeInstance( { 'g:ycm_log_level': 'debug',
                          'g:ycm_keep_logfiles': 1,
                          'g:ycm_open_loclist_on_ycm_diags': 0 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationListForWindow', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_DiagnosticsFound_DoNotOpenLocationList_test(
  ycm, set_location_list_for_window, post_vim_message, *args ):

  diagnostic = {
    'kind': 'ERROR',
    'text': 'error text',
    'location': {
      'filepath': 'buffer',
      'line_num': 19,
      'column_num': 2
    }
  }

  current_buffer = VimBuffer( 'buffer',
                              filetype = 'cpp',
                              number = 3 )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = [ diagnostic ] ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False )
  ] )
  set_location_list_for_window.assert_called_once_with( 1, [ {
      'bufnr': 3,
      'lnum': 19,
      'col': 2,
      'text': 'error text',
      'type': 'E',
      'valid': 1
  } ] )


@YouCompleteMeInstance( { 'g:ycm_open_loclist_on_ycm_diags': 1 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationListForWindow', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenLocationList', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_DiagnosticsFound_OpenLocationList_test(
  ycm,
  open_location_list,
  set_location_list_for_window,
  post_vim_message,
  *args ):

  diagnostic = {
    'kind': 'ERROR',
    'text': 'error text',
    'location': {
      'filepath': 'buffer',
      'line_num': 19,
      'column_num': 2
    }
  }

  current_buffer = VimBuffer( 'buffer',
                              filetype = 'cpp',
                              number = 3 )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = [ diagnostic ] ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False )
  ] )
  set_location_list_for_window.assert_called_once_with( 1, [ {
      'bufnr': 3,
      'lnum': 19,
      'col': 2,
      'text': 'error text',
      'type': 'E',
      'valid': 1
  } ] )
  open_location_list.assert_called_once_with( focus = True )


@YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                          'g:ycm_enable_diagnostic_signs': 1,
                          'g:ycm_enable_diagnostic_highlighting': 1 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_UpdateDiagnosticInterface(
  ycm, post_vim_message, *args ):

  contents = """int main() {
  int x, y;
  x == y
}"""

  # List of diagnostics returned by ycmd for the above code.
  diagnostics = [ {
    'kind': 'ERROR',
    'text': "expected ';' after expression",
    'location': {
      'filepath': 'buffer',
      'line_num': 3,
      'column_num': 9
    },
    # Looks strange but this is really what ycmd is returning.
    'location_extent': {
      'start': {
        'filepath': '',
        'line_num': 0,
        'column_num': 0,
      },
      'end': {
        'filepath': '',
        'line_num': 0,
        'column_num': 0,
      }
    },
    'ranges': [],
    'fixit_available': True
  }, {
    'kind': 'WARNING',
    'text': 'equality comparison result unused',
    'location': {
      'filepath': 'buffer',
      'line_num': 3,
      'column_num': 7,
    },
    'location_extent': {
      'start': {
        'filepath': 'buffer',
        'line_num': 3,
        'column_num': 5,
      },
      'end': {
        'filepath': 'buffer',
        'line_num': 3,
        'column_num': 7,
      }
    },
    'ranges': [ {
      'start': {
        'filepath': 'buffer',
        'line_num': 3,
        'column_num': 3,
      },
      'end': {
        'filepath': 'buffer',
        'line_num': 3,
        'column_num': 9,
      }
    } ],
    'fixit_available': True
  } ]

  current_buffer = VimBuffer( 'buffer',
                              filetype = 'c',
                              contents = contents.splitlines(),
                              number = 5 )

  test_utils.VIM_MATCHES_FOR_WINDOW.clear()
  test_utils.VIM_SIGNS = []
  vimsupport.SIGN_ID_FOR_BUFFER.clear()

  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 3, 1 ) ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = diagnostics ):
      ycm.OnFileReadyToParse()
      ycm.HandleFileParseRequest( block = True )

    # The error on the current line is echoed, not the warning.
    post_vim_message.assert_called_once_with(
      "expected ';' after expression (FixIt)",
      truncate = True, warning = False )

    # Error match is added after warning matches.
    assert_that(
      test_utils.VIM_MATCHES_FOR_WINDOW,
      has_entries( {
        1: contains(
          VimMatch( 'YcmWarningSection', '\\%3l\\%5c\\_.\\{-}\\%3l\\%7c' ),
          VimMatch( 'YcmWarningSection', '\\%3l\\%3c\\_.\\{-}\\%3l\\%9c' ),
          VimMatch( 'YcmErrorSection', '\\%3l\\%8c' )
        )
      } )
    )

    # Only the error sign is placed.
    assert_that(
      test_utils.VIM_SIGNS,
      contains(
        VimSign( SIGN_BUFFER_ID_INITIAL_VALUE, 3, 'YcmError', 5 )
      )
    )

  # The error is not echoed again when moving the cursor along the line.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 3, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_not_called()

  # The error is cleared when moving the cursor to another line.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 2, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_called_once_with( "", warning = False )

  # The error is echoed when moving the cursor back.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 3, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_called_once_with(
      "expected ';' after expression (FixIt)",
      truncate = True, warning = False )

    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = diagnostics[ 1 : ] ):
      ycm.OnFileReadyToParse()
      ycm.HandleFileParseRequest( block = True )

    assert_that(
      test_utils.VIM_MATCHES_FOR_WINDOW,
      has_entries( {
        1: contains(
          VimMatch( 'YcmWarningSection', '\\%3l\\%5c\\_.\\{-}\\%3l\\%7c' ),
          VimMatch( 'YcmWarningSection', '\\%3l\\%3c\\_.\\{-}\\%3l\\%9c' )
        )
      } )
    )

    assert_that(
      test_utils.VIM_SIGNS,
      contains(
        VimSign( SIGN_BUFFER_ID_INITIAL_VALUE + 1, 3, 'YcmWarning', 5 )
      )
    )


def YouCompleteMe_UpdateDiagnosticInterface_OldVim_test():
  YouCompleteMe_UpdateDiagnosticInterface()


@patch( 'ycm.tests.test_utils.VIM_VERSION', Version( 8, 1, 614 ) )
def YouCompleteMe_UpdateDiagnosticInterface_NewVim_test():
  YouCompleteMe_UpdateDiagnosticInterface()


@YouCompleteMeInstance( { 'g:ycm_enable_diagnostic_highlighting': 1 } )
def YouCompleteMe_UpdateMatches_ClearDiagnosticMatchesInNewBuffer_test( ycm ):
  current_buffer = VimBuffer( 'buffer',
                              filetype = 'c',
                              number = 5 )

  test_utils.VIM_MATCHES_FOR_WINDOW.clear()
  test_utils.VIM_MATCHES_FOR_WINDOW[ 1 ] = [
    VimMatch( 'YcmWarningSection', '\\%3l\\%5c\\_.\\{-}\\%3l\\%7c' ),
    VimMatch( 'YcmWarningSection', '\\%3l\\%3c\\_.\\{-}\\%3l\\%9c' ),
    VimMatch( 'YcmErrorSection', '\\%3l\\%8c' )
  ]

  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    ycm.UpdateMatches()

  assert_that( test_utils.VIM_MATCHES_FOR_WINDOW,
               has_entries( { 1: empty() } ) )


@YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                          'g:ycm_always_populate_location_list': 1,
                          'g:ycm_enable_diagnostic_highlighting': 1 } )
@patch.object( ycm_buffer_module,
               'DIAGNOSTIC_UI_ASYNC_FILETYPES',
               [ 'ycmtest' ] )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_AsyncDiagnosticUpdate_SingleFile_test( ycm,
                                                         post_vim_message,
                                                         *args ):

  # This test simulates asynchronous diagnostic updates associated with a single
  # file (e.g. Translation Unit), but where the actual errors refer to other
  # open files and other non-open files. This is not strictly invalid, nor is it
  # completely normal, but it is supported and does work.

  # Contrast with the next test which sends the diagnostics filewise, which is
  # what the language server protocol will do.

  diagnostics = [
    {
      'kind': 'ERROR',
      'text': 'error text in current buffer',
      'location': {
        'filepath': '/current',
        'line_num': 1,
        'column_num': 1
      },
      'location_extent': {
        'start': {
          'filepath': '/current',
          'line_num': 1,
          'column_num': 1,
        },
        'end': {
          'filepath': '/current',
          'line_num': 1,
          'column_num': 1,
        }
      },
      'ranges': []
    },
    {
      'kind': 'ERROR',
      'text': 'error text in hidden buffer',
      'location': {
        'filepath': '/has_diags',
        'line_num': 4,
        'column_num': 2
      },
      'location_extent': {
        'start': {
          'filepath': '/has_diags',
          'line_num': 4,
          'column_num': 2,
        },
        'end': {
          'filepath': '/has_diags',
          'line_num': 4,
          'column_num': 2,
        }
      },
      'ranges': []
    },
    {
      'kind': 'ERROR',
      'text': 'error text in buffer not open in Vim',
      'location': {
        'filepath': '/not_open',
        'line_num': 8,
        'column_num': 4
      },
      'location_extent': {
        'start': {
          'filepath': '/not_open',
          'line_num': 8,
          'column_num': 4,
        },
        'end': {
          'filepath': '/not_open',
          'line_num': 8,
          'column_num': 4,
        }
      },
      'ranges': []
    }
  ]

  current_buffer = VimBuffer( '/current',
                              filetype = 'ycmtest',
                              contents = [ 'current' ] * 10,
                              number = 1 )
  no_diags_buffer = VimBuffer( '/no_diags',
                               filetype = 'ycmtest',
                               contents = [ 'nodiags' ] * 10,
                               number = 2 )
  hidden_buffer = VimBuffer( '/has_diags',
                             filetype = 'ycmtest',
                             contents = [ 'hasdiags' ] * 10,
                             number = 3 )

  buffers = [ current_buffer, no_diags_buffer, hidden_buffer ]
  windows = [ current_buffer, no_diags_buffer ]

  # Register each buffer internally with YCM
  for current in buffers:
    with MockVimBuffers( buffers, [ current ] ):
      ycm.OnFileReadyToParse()

  with patch( 'ycm.vimsupport.SetLocationListForWindow',
              new_callable = ExtendedMock ) as set_location_list_for_window:
    with MockVimBuffers( buffers, windows ):
      ycm.UpdateWithNewDiagnosticsForFile( '/current', diagnostics )

  # We update the diagnostic on the current cursor position
  post_vim_message.assert_has_exact_calls( [
    call( "error text in current buffer", truncate = True, warning = False ),
  ] )

  # Ensure we included all the diags though
  set_location_list_for_window.assert_has_exact_calls( [
    call( 1, [
      {
        'lnum': 1,
        'col': 1,
        'bufnr': 1,
        'valid': 1,
        'type': 'E',
        'text': 'error text in current buffer',
      },
      {
        'lnum': 4,
        'col': 2,
        'bufnr': 3,
        'valid': 1,
        'type': 'E',
        'text': 'error text in hidden buffer',
      },
      {
        'lnum': 8,
        'col': 4,
        'bufnr': -1, # sic: Our mocked bufnr function actually returns -1,
                     # even though YCM is passing "create if needed".
                     # FIXME? we shouldn't do that, and we should pass
                     # filename instead
        'valid': 1,
        'type': 'E',
        'text': 'error text in buffer not open in Vim'
      }
    ] )
  ] )

  assert_that(
    test_utils.VIM_MATCHES_FOR_WINDOW,
    has_entries( {
      1: contains(
        VimMatch( 'YcmErrorSection', '\\%1l\\%1c\\_.\\{-}\\%1l\\%1c' )
      )
    } )
  )


@YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                          'g:ycm_always_populate_location_list': 1,
                          'g:ycm_enable_diagnostic_highlighting': 1 } )
@patch.object( ycm_buffer_module,
               'DIAGNOSTIC_UI_ASYNC_FILETYPES',
               [ 'ycmtest' ] )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_AsyncDiagnosticUpdate_PerFile_test( ycm,
                                                      post_vim_message,
                                                      *args ):

  # This test simulates asynchronous diagnostic updates which are delivered per
  # file, including files which are open and files which are not.

  # Ordered to ensure that the calls to update are deterministic
  diagnostics_per_file = [
    ( '/current', [ {
        'kind': 'ERROR',
        'text': 'error text in current buffer',
        'location': {
          'filepath': '/current',
          'line_num': 1,
          'column_num': 1
        },
        'location_extent': {
          'start': {
            'filepath': '/current',
            'line_num': 1,
            'column_num': 1,
          },
          'end': {
            'filepath': '/current',
            'line_num': 1,
            'column_num': 1,
          }
        },
        'ranges': [],
      } ] ),
    ( '/separate_window', [ {
        'kind': 'ERROR',
        'text': 'error text in a buffer open in a separate window',
        'location': {
          'filepath': '/separate_window',
          'line_num': 3,
          'column_num': 3
        },
        'location_extent': {
          'start': {
            'filepath': '/separate_window',
            'line_num': 3,
            'column_num': 3,
          },
          'end': {
            'filepath': '/separate_window',
            'line_num': 3,
            'column_num': 3,
          }
        },
        'ranges': []
      } ] ),
    ( '/hidden', [ {
        'kind': 'ERROR',
        'text': 'error text in hidden buffer',
        'location': {
          'filepath': '/hidden',
          'line_num': 4,
          'column_num': 2
        },
        'location_extent': {
          'start': {
            'filepath': '/hidden',
            'line_num': 4,
            'column_num': 2,
          },
          'end': {
            'filepath': '/hidden',
            'line_num': 4,
            'column_num': 2,
          }
        },
        'ranges': []
      } ] ),
    ( '/not_open', [ {
        'kind': 'ERROR',
        'text': 'error text in buffer not open in Vim',
        'location': {
          'filepath': '/not_open',
          'line_num': 8,
          'column_num': 4
        },
        'location_extent': {
          'start': {
            'filepath': '/not_open',
            'line_num': 8,
            'column_num': 4,
          },
          'end': {
            'filepath': '/not_open',
            'line_num': 8,
            'column_num': 4,
          }
        },
        'ranges': []
      } ] )
  ]

  current_buffer = VimBuffer( '/current',
                              filetype = 'ycmtest',
                              contents = [ 'current' ] * 10,
                              number = 1 )
  no_diags_buffer = VimBuffer( '/no_diags',
                               filetype = 'ycmtest',
                               contents = [ 'no_diags' ] * 10,
                               number = 2 )
  separate_window = VimBuffer( '/separate_window',
                               filetype = 'ycmtest',
                               contents = [ 'separate_window' ] * 10,
                               number = 3 )
  hidden_buffer = VimBuffer( '/hidden',
                             filetype = 'ycmtest',
                             contents = [ 'hidden' ] * 10,
                             number = 4 )
  buffers = [
    current_buffer,
    no_diags_buffer,
    separate_window,
    hidden_buffer
  ]
  windows = [
    current_buffer,
    no_diags_buffer,
    separate_window
  ]

  # Register each buffer internally with YCM
  for current in buffers:
    with MockVimBuffers( buffers, [ current ] ):
      ycm.OnFileReadyToParse()

  with patch( 'ycm.vimsupport.SetLocationListForWindow',
              new_callable = ExtendedMock ) as set_location_list_for_window:
    with MockVimBuffers( buffers, windows ):
      for filename, diagnostics in diagnostics_per_file:
        ycm.UpdateWithNewDiagnosticsForFile( filename, diagnostics )

  # We update the diagnostic on the current cursor position
  post_vim_message.assert_has_exact_calls( [
    call( "error text in current buffer", truncate = True, warning = False ),
  ] )

  # Ensure we included all the diags though
  set_location_list_for_window.assert_has_exact_calls( [
    call( 1, [
      {
        'lnum': 1,
        'col': 1,
        'bufnr': 1,
        'valid': 1,
        'type': 'E',
        'text': 'error text in current buffer',
      },
    ] ),

    call( 3, [
      {
        'lnum': 3,
        'col': 3,
        'bufnr': 3,
        'valid': 1,
        'type': 'E',
        'text': 'error text in a buffer open in a separate window',
      },
    ] )
  ] )

  # FIXME: diagnostic matches in windows other than the current one are not
  # updated.
  assert_that(
    test_utils.VIM_MATCHES_FOR_WINDOW,
    has_entries( {
      1: contains(
        VimMatch( 'YcmErrorSection', '\\%1l\\%1c\\_.\\{-}\\%1l\\%1c' )
      )
    } )
  )


@YouCompleteMeInstance()
def YouCompleteMe_OnPeriodicTick_ServerNotRunning_test( ycm, *args ):
  with patch.object( ycm, 'IsServerAlive', return_value = False ):
    assert_that( ycm.OnPeriodicTick(), equal_to( False ) )


@YouCompleteMeInstance()
def YouCompleteMe_OnPeriodicTick_ServerNotReady_test( ycm, *args ):
  with patch.object( ycm, 'IsServerAlive', return_value = True ):
    with patch.object( ycm, 'IsServerReady', return_value = False ):
      assert_that( ycm.OnPeriodicTick(), equal_to( True ) )


@YouCompleteMeInstance()
@patch.object( ycm_buffer_module,
               'DIAGNOSTIC_UI_ASYNC_FILETYPES',
               [ 'ycmtest' ] )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.client.base_request._ValidateResponseObject', return_value = True )
@patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
def YouCompleteMe_OnPeriodicTick_DontRetry_test( ycm,
                                                 post_data_to_handler_async,
                                                 *args ):

  current_buffer = VimBuffer( '/current',
                              filetype = 'ycmtest',
                              number = 1 )

  # Create the request and make the first poll; we expect no response
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
    assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
    post_data_to_handler_async.assert_called()

  assert ycm._message_poll_request is not None
  post_data_to_handler_async.reset_mock()

  # OK that sent the request, now poll to check if it is complete (say it is
  # not)
  with patch.object( ycm._message_poll_request,
                     '_response_future',
                     new = MockAsyncServerResponseInProgress() ) as mock_future:
    poll_again = ycm.OnPeriodicTick()
    mock_future.done.assert_called()
    mock_future.result.assert_not_called()
    assert_that( poll_again, equal_to( True ) )

  # Poll again, but return a response (telling us to stop polling)
  with patch.object( ycm._message_poll_request,
                     '_response_future',
                     new = MockAsyncServerResponseDone( False ) ) \
      as mock_future:
    poll_again = ycm.OnPeriodicTick()
    mock_future.done.assert_called()
    mock_future.result.assert_called()
    post_data_to_handler_async.assert_not_called()
    # We reset and don't poll anymore
    assert_that( ycm._message_poll_request is None )
    assert_that( poll_again, equal_to( False ) )



@YouCompleteMeInstance()
@patch.object( ycm_buffer_module,
               'DIAGNOSTIC_UI_ASYNC_FILETYPES',
               [ 'ycmtest' ] )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.client.base_request._ValidateResponseObject', return_value = True )
@patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
def YouCompleteMe_OnPeriodicTick_Exception_test( ycm,
                                                 post_data_to_handler_async,
                                                 *args ):

  current_buffer = VimBuffer( '/current',
                              filetype = 'ycmtest',
                              number = 1 )

  # Create the request and make the first poll; we expect no response
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
    assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
    post_data_to_handler_async.assert_called()

  post_data_to_handler_async.reset_mock()

  # Poll again, but return an exception response
  mock_response = MockAsyncServerResponseException( RuntimeError( 'test' ) )
  with patch.object( ycm._message_poll_request,
                     '_response_future',
                     new = mock_response ) as mock_future:
    assert_that( ycm.OnPeriodicTick(), equal_to( False ) )
    mock_future.done.assert_called()
    mock_future.result.assert_called()
    post_data_to_handler_async.assert_not_called()
    # We reset and don't poll anymore
    assert_that( ycm._message_poll_request is None )


@YouCompleteMeInstance()
@patch.object( ycm_buffer_module,
               'DIAGNOSTIC_UI_ASYNC_FILETYPES',
               [ 'ycmtest' ] )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.client.base_request._ValidateResponseObject', return_value = True )
@patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
@patch( 'ycm.client.messages_request._HandlePollResponse' )
def YouCompleteMe_OnPeriodicTick_ValidResponse_test( ycm,
                                                     handle_poll_response,
                                                     post_data_to_handler_async,
                                                     *args ):

  current_buffer = VimBuffer( '/current',
                              filetype = 'ycmtest',
                              number = 1 )

  # Create the request and make the first poll; we expect no response
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
    assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
    post_data_to_handler_async.assert_called()

  post_data_to_handler_async.reset_mock()

  # Poll again, and return a _proper_ response (finally!).
  # Note, _HandlePollResponse is tested independently (for simplicity)
  with patch.object( ycm._message_poll_request,
                     '_response_future',
                     new = MockAsyncServerResponseDone( [] ) ) as mock_future:
    assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
    handle_poll_response.assert_called()
    mock_future.done.assert_called()
    mock_future.result.assert_called()
    post_data_to_handler_async.assert_called() # Poll again!
    assert_that( ycm._message_poll_request is not None )


@YouCompleteMeInstance()
@patch( 'ycm.client.completion_request.CompletionRequest.OnCompleteDone' )
def YouCompleteMe_OnCompleteDone_CompletionRequest_test( ycm,
                                                         on_complete_done ):
  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
    ycm.SendCompletionRequest()
  ycm.OnCompleteDone()
  on_complete_done.assert_called()


@YouCompleteMeInstance()
@patch( 'ycm.client.completion_request.CompletionRequest.OnCompleteDone' )
def YouCompleteMe_OnCompleteDone_NoCompletionRequest_test( ycm,
                                                           on_complete_done ):
  ycm.OnCompleteDone()
  on_complete_done.assert_not_called()


@YouCompleteMeInstance()
def YouCompleteMe_ShouldResendFileParseRequest_NoParseRequest_test( ycm ):
  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
    assert_that( ycm.ShouldResendFileParseRequest(), equal_to( False ) )

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

from ycm.client.messages_request import MessagesPoll
from ycm.tests.test_utils import ( ExtendedMock,
                                   MockVimBuffers,
                                   MockVimModule,
                                   Version,
                                   VimBuffer,
                                   VimProp,
                                   VimSign )
MockVimModule()

import os
import sys
from hamcrest import ( assert_that, contains_exactly, empty, equal_to,
                       has_entries, is_in, is_not, matches_regexp )
from unittest.mock import call, MagicMock, patch
from unittest import TestCase

from ycm.paths import _PathToPythonUsedDuringBuild
from ycm.vimsupport import SetVariableValue
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


def RunNotifyUserIfServerCrashed( ycm, post_vim_message, test ):
  StopServer( ycm )

  ycm._logger = MagicMock( autospec = True )
  ycm._server_popen = MagicMock( autospec = True )
  ycm._server_popen.poll.return_value = test[ 'return_code' ]

  ycm.OnFileReadyToParse()

  assert_that( ycm._logger.error.call_args[ 0 ][ 0 ],
               test[ 'expected_message' ] )
  assert_that( post_vim_message.call_args[ 0 ][ 0 ],
               test[ 'expected_message' ] )


def YouCompleteMe_UpdateDiagnosticInterface( ycm, post_vim_message, *args ):

  contents = "\nint main() { int x, y; x == y }"

  # List of diagnostics returned by ycmd for the above code.
  diagnostics = [ {
    'kind': 'ERROR',
    'text': "expected ';' after expression (fix available) "
    "[expected_semi_after_expr]",
    'location': {
      'filepath': 'buffer',
      'line_num': 2,
      'column_num': 31
    },
    # Looks strange but this is really what ycmd is returning.
    'location_extent': {
      'start': {
        'filepath': '',
        'line_num': 2,
        'column_num': 31,
      },
      'end': {
        'filepath': '',
        'line_num': 2,
        'column_num': 32,
      }
    },
    'ranges': [ {
      'start': {
        'line_num': 2,
        'column_num': 31,
        'filepath': 'buffer'
      },
      'end': {
        'line_num': 2,
        'column_num': 31,
        'filepath': 'buffer'
      }
    } ],
    'fixit_available': False
  }, {
    'kind': 'WARNING',
    'text': 'equality comparison result unused',
    'location': {
      'filepath': 'buffer',
      'line_num': 2,
      'column_num': 31,
    },
    'location_extent': {
      'start': {
        'filepath': 'buffer',
        'line_num': 2,
        'column_num': 31,
      },
      'end': {
        'filepath': 'buffer',
        'line_num': 2,
        'column_num': 32,
      }
    },
    'ranges': [ {
      'start': {
        'filepath': 'buffer',
        'line_num': 2,
        'column_num': 24,
      },
      'end': {
        'filepath': 'buffer',
        'line_num': 2,
        'column_num': 30,
      }
    } ],
    'fixit_available': False
  } ]

  current_buffer = VimBuffer( 'buffer',
                              filetype = 'c',
                              contents = contents.splitlines(),
                              number = 5 )

  test_utils.VIM_SIGNS = []
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 2, 1 ) ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = diagnostics ):
      ycm.OnFileReadyToParse()
      ycm.HandleFileParseRequest( block = True )
    # The error on the current line is echoed, not the warning.
    post_vim_message.assert_called_once_with(
      "expected ';' after expression (fix available) "
      "[expected_semi_after_expr]",
      truncate = True, warning = False )

    # Error match is added after warning matches.
    assert_that(
      test_utils.VIM_PROPS_FOR_BUFFER,
      has_entries( {
        current_buffer.number: contains_exactly(
          VimProp( 'YcmWarningProperty', 2, 31, 2, 32 ),
          VimProp( 'YcmWarningProperty', 2, 24, 2, 30 ),
          VimProp( 'YcmErrorProperty', 2, 31, 2, 32 ),
          VimProp( 'YcmErrorProperty', 2, 31, 2, 31 ),
        )
      } )
    )

    # Only the error sign is placed.
    assert_that(
      test_utils.VIM_SIGNS,
      contains_exactly(
        VimSign( 2, 'YcmError', 5 )
      )
    )

  # The error is not echoed again when moving the cursor along the line.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 2, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_not_called()

  # The error is cleared when moving the cursor to another line.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_called_once_with( "", warning = False )

  # The error is echoed when moving the cursor back.
  with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 2, 2 ) ):
    post_vim_message.reset_mock()
    ycm.OnCursorMoved()
    post_vim_message.assert_called_once_with(
      "expected ';' after expression (fix available) "
      "[expected_semi_after_expr]",
      truncate = True, warning = False )

    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = diagnostics[ 1 : ] ):
      ycm.OnFileReadyToParse()
      ycm.HandleFileParseRequest( block = True )

    assert_that(
      test_utils.VIM_PROPS_FOR_BUFFER,
      has_entries( {
        current_buffer.number: contains_exactly(
          VimProp( 'YcmWarningProperty', 2, 31, 2, 32 ),
          VimProp( 'YcmWarningProperty', 2, 24, 2, 30 )
        )
      } )
    )

    assert_that(
      test_utils.VIM_SIGNS,
      contains_exactly(
        VimSign( 2, 'YcmWarning', 5 )
      )
    )


class YouCompleteMeTest( TestCase ):
  @YouCompleteMeInstance()
  def test_YouCompleteMe_YcmCoreNotImported( self, ycm ):
    assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )


  @patch( 'ycm.vimsupport.PostVimMessage' )
  def test_YouCompleteMe_InvalidPythonInterpreterPath( self, post_vim_message ):
    with UserOptions( {
      'g:ycm_server_python_interpreter': '/invalid/python/path' } ):
      try:
        ycm = YouCompleteMe()

        assert_that( ycm.IsServerAlive(), equal_to( False ) )
        post_vim_message.assert_called_once_with(
          "Unable to start the ycmd server. "
          "Path in 'g:ycm_server_python_interpreter' option does not point "
          "to a valid Python 3.6+. "
          "Correct the error then restart the server with "
          "':YcmRestartServer'." )

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
  def test_YouCompleteMe_NoPythonInterpreterFound(
      self, post_vim_message, *args ):
    with UserOptions( {} ):
      try:
        with patch( 'ycmd.utils.ReadFile', side_effect = IOError ):
          ycm = YouCompleteMe()

        assert_that( ycm.IsServerAlive(), equal_to( False ) )
        post_vim_message.assert_called_once_with(
          "Unable to start the ycmd server. Cannot find Python 3.6+. "
          "Set the 'g:ycm_server_python_interpreter' option to a Python "
          "interpreter path. "
          "Correct the error then restart the server with "
          "':YcmRestartServer'." )

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
  def test_YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedCore(
      self, ycm, post_vim_message ):
    message = (
      "The ycmd server SHUT DOWN \\(restart with ':YcmRestartServer'\\). "
      "Unexpected error while loading the YCM core library. Type "
      "':YcmToggleLogs ycmd_\\d+_stderr_.+.log' to check the logs." )
    RunNotifyUserIfServerCrashed( ycm, post_vim_message, {
      'return_code': 3,
      'expected_message': matches_regexp( message )
    } )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_NotifyUserIfServerCrashed_MissingCore(
      self, ycm, post_vim_message ):
    message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
                "YCM core library not detected; you need to compile YCM before "
                "using it. Follow the instructions in the documentation." )
    RunNotifyUserIfServerCrashed( ycm, post_vim_message, {
      'return_code': 4,
      'expected_message': equal_to( message )
    } )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_NotifyUserIfServerCrashed_OutdatedCore(
      self, ycm, post_vim_message ):
    message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
                "YCM core library too old; PLEASE RECOMPILE by running the "
                "install.py script. See the documentation for more details." )
    RunNotifyUserIfServerCrashed( ycm, post_vim_message, {
      'return_code': 7,
      'expected_message': equal_to( message )
    } )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedExitCode(
      self, ycm, post_vim_message ):
    message = (
      "The ycmd server SHUT DOWN \\(restart with ':YcmRestartServer'\\). "
      "Unexpected exit code 1. Type "
      "':YcmToggleLogs ycmd_\\d+_stderr_.+.log' to check the logs." )
    RunNotifyUserIfServerCrashed( ycm, post_vim_message, {
      'return_code': 1,
      'expected_message': matches_regexp( message )
    } )


  @YouCompleteMeInstance( { 'g:ycm_extra_conf_vim_data': [ 'tempname()' ] } )
  @patch( 'ycm.vimsupport.VimSupportsPopupWindows', return_value=True )
  def test_YouCompleteMe_DebugInfo_ServerRunning( self, ycm, *args ):
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
  @patch( 'ycm.vimsupport.VimSupportsPopupWindows', return_value=True )
  def test_YouCompleteMe_DebugInfo_ServerNotRunning( self, ycm, *args ):
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
  def test_YouCompleteMe_OnVimLeave_RemoveClientLogfileByDefault( self, ycm ):
    client_logfile = ycm._client_logfile
    assert_that( os.path.isfile( client_logfile ),
                 f'Logfile { client_logfile } does not exist.' )
    ycm.OnVimLeave()
    assert_that( not os.path.isfile( client_logfile ),
                 f'Logfile { client_logfile } was not removed.' )


  @YouCompleteMeInstance( { 'g:ycm_keep_logfiles': 1 } )
  def test_YouCompleteMe_OnVimLeave_KeepClientLogfile( self, ycm ):
    client_logfile = ycm._client_logfile
    assert_that( os.path.isfile( client_logfile ),
                 f'Logfile { client_logfile } does not exist.' )
    ycm.OnVimLeave()
    assert_that( os.path.isfile( client_logfile ),
                 f'Logfile { client_logfile } was removed.' )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.CloseBuffersForFilename',
          new_callable = ExtendedMock )
  @patch( 'ycm.vimsupport.OpenFilename', new_callable = ExtendedMock )
  def test_YouCompleteMe_ToggleLogs_WithParameters(
      self, ycm, open_filename, close_buffers_for_filename ):
    logfile_buffer = VimBuffer( ycm._client_logfile )
    with MockVimBuffers( [ logfile_buffer ], [ logfile_buffer ] ):
      ycm.ToggleLogs( 90,
                      'botright vertical',
                      os.path.basename( ycm._client_logfile ),
                      'nonexisting_logfile',
                      os.path.basename( ycm._server_stdout ) )

      open_filename.assert_has_exact_calls( [
        call( ycm._server_stdout, { 'size': 90,
                                    'watch': True,
                                    'fix': True,
                                    'focus': False,
                                    'position': 'end',
                                    'mods': 'botright vertical' } )
      ] )
      close_buffers_for_filename.assert_has_exact_calls( [
        call( ycm._client_logfile )
      ] )


  @YouCompleteMeInstance()
  # Select the second item of the list which is the ycmd stderr logfile.
  @patch( 'ycm.vimsupport.SelectFromList', return_value = 1 )
  @patch( 'ycm.vimsupport.OpenFilename', new_callable = ExtendedMock )
  def test_YouCompleteMe_ToggleLogs_WithoutParameters_SelectLogfileNotAlreadyOpen( # noqa
    self, ycm, open_filename, *args ):

    current_buffer = VimBuffer( 'current_buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      ycm.ToggleLogs( 0, '' )

    open_filename.assert_has_exact_calls( [
      call( ycm._server_stderr, { 'size': 12,
                                  'watch': True,
                                  'fix': True,
                                  'focus': False,
                                  'position': 'end',
                                  'mods': '' } )
    ] )


  @YouCompleteMeInstance()
  # Select the third item of the list which is the ycmd stdout logfile.
  @patch( 'ycm.vimsupport.SelectFromList', return_value = 2 )
  @patch( 'ycm.vimsupport.CloseBuffersForFilename',
          new_callable = ExtendedMock )
  def test_YouCompleteMe_ToggleLogs_WithoutParameters_SelectLogfileAlreadyOpen(
    self, ycm, close_buffers_for_filename, *args ):

    logfile_buffer = VimBuffer( ycm._server_stdout )
    with MockVimBuffers( [ logfile_buffer ], [ logfile_buffer ] ):
      ycm.ToggleLogs( 0, '' )

    close_buffers_for_filename.assert_has_exact_calls( [
      call( ycm._server_stdout )
    ] )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.SelectFromList',
          side_effect = RuntimeError( 'Error message' ) )
  @patch( 'ycm.vimsupport.PostVimMessage' )
  def test_YouCompleteMe_ToggleLogs_WithoutParameters_NoSelection(
    self, ycm, post_vim_message, *args ):

    current_buffer = VimBuffer( 'current_buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      ycm.ToggleLogs( 0, '' )

    assert_that(
      # Argument passed to PostVimMessage.
      post_vim_message.call_args[ 0 ][ 0 ],
      equal_to( 'Error message' )
    )


  @YouCompleteMeInstance()
  def test_YouCompleteMe_GetDefinedSubcommands_ListFromServer( self, ycm ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.client.base_request._JsonFromFuture',
                  return_value = [ 'SomeCommand', 'AnotherCommand' ] ):
        assert_that(
          ycm.GetDefinedSubcommands(),
          contains_exactly(
            'SomeCommand',
            'AnotherCommand'
          )
        )


  @YouCompleteMeInstance()
  @patch( 'ycm.client.base_request._logger', autospec = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_GetDefinedSubcommands_ErrorFromServer(
      self, ycm, post_vim_message, logger ):
    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.client.base_request._JsonFromFuture',
                  side_effect = ServerError( 'Server error' ) ):
        result = ycm.GetDefinedSubcommands()

    logger.exception.assert_called_with(
        'Error while handling server response' )
    post_vim_message.assert_has_exact_calls( [
      call( 'Server error', truncate = False )
    ] )
    assert_that( result, empty() )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDetailedDiagnostic_MessageFromServer(
    self, ycm, post_vim_message ):

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.client.base_request._JsonFromFuture',
                  return_value = { 'message': 'some_detailed_diagnostic' } ):
        ycm.ShowDetailedDiagnostic( False ),

    post_vim_message.assert_has_exact_calls( [
      call( 'some_detailed_diagnostic', warning = False )
    ] )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDetailedDiagnostic_Exception(
    self, ycm, post_vim_message ):

    current_buffer = VimBuffer( 'buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      with patch( 'ycm.client.base_request._JsonFromFuture',
                  side_effect = RuntimeError( 'Some exception' ) ):
        ycm.ShowDetailedDiagnostic( False ),

    post_vim_message.assert_has_exact_calls( [
      call( 'Some exception', truncate = False )
    ] )


  @YouCompleteMeInstance()
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDiagnostics_FiletypeNotSupported(
    self, ycm, post_vim_message ):

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
  @patch( 'ycm.vimsupport.SetLocationListForWindow',
          new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDiagnostics_NoDiagnosticsDetected(
    self,
    ycm,
    set_location_list_for_window,
    post_vim_message,
    *args ):

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
    set_location_list_for_window.assert_called_once_with( 1, [], 1 )


  @YouCompleteMeInstance( { 'g:ycm_log_level': 'debug',
                            'g:ycm_keep_logfiles': 1,
                            'g:ycm_open_loclist_on_ycm_diags': 0 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  @patch( 'ycm.vimsupport.SetLocationListForWindow',
          new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDiagnostics_DiagnosticsFound_DoNotOpenLocationList(
    self,
    ycm,
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
    } ], 0 )


  @YouCompleteMeInstance( { 'g:ycm_open_loclist_on_ycm_diags': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  @patch( 'ycm.vimsupport.SetLocationListForWindow',
          new_callable = ExtendedMock )
  @patch( 'ycm.vimsupport.OpenLocationList', new_callable = ExtendedMock )
  def test_YouCompleteMe_ShowDiagnostics_DiagnosticsFound_OpenLocationList(
    self,
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
    } ], 1 )
    open_location_list.assert_called_once_with( focus = True )


  @YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                            'g:ycm_enable_diagnostic_signs': 1,
                            'g:ycm_enable_diagnostic_highlighting': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.client.event_notification.EventNotification.Done',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_UpdateDiagnosticInterface_OldVim(
    self, ycm, post_vim_message, *args ):
    YouCompleteMe_UpdateDiagnosticInterface( ycm, post_vim_message )


  @YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                            'g:ycm_enable_diagnostic_signs': 1,
                            'g:ycm_enable_diagnostic_highlighting': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.tests.test_utils.VIM_VERSION', Version( 8, 1, 614 ) )
  @patch( 'ycm.client.event_notification.EventNotification.Done',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_UpdateDiagnosticInterface_NewVim(
    self, ycm, post_vim_message, *args ):
    YouCompleteMe_UpdateDiagnosticInterface( ycm, post_vim_message )


  @YouCompleteMeInstance( { 'g:ycm_enable_diagnostic_highlighting': 1 } )
  def test_YouCompleteMe_UpdateMatches_ClearDiagnosticMatchesInNewBuffer(
      self, ycm ):
    current_buffer = VimBuffer( 'buffer',
                                filetype = 'c',
                                contents = '\n\n\n\n',
                                number = 5 )

    test_utils.VIM_PROPS_FOR_BUFFER[ current_buffer.number ] = [
      VimProp( 'YcmWarningProperty', 3, 5, 3, 7 ),
      VimProp( 'YcmWarningProperty', 3, 3, 3, 9 ),
      VimProp( 'YcmErrorProperty', 3, 8 )
    ]

    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      ycm.UpdateMatches()

    assert_that( test_utils.VIM_PROPS_FOR_BUFFER[ current_buffer.number ],
                 empty() )


  @YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                            'g:ycm_always_populate_location_list': 1,
                            'g:ycm_show_diagnostics_ui': 0,
                            'g:ycm_enable_diagnostic_highlighting': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_AsyncDiagnosticUpdate_UserDisabled(
      self,
      ycm,
      post_vim_message,
      *args ):
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
    ]
    current_buffer = VimBuffer( '/current',
                                filetype = 'ycmtest',
                                contents = [ 'current' ] * 10,
                                number = 1 )
    buffers = [ current_buffer ]
    windows = [ current_buffer ]

    # Register each buffer internally with YCM
    for current in buffers:
      with MockVimBuffers( buffers, [ current ] ):
        ycm.OnFileReadyToParse()
    with patch( 'ycm.vimsupport.SetLocationListForWindow',
                new_callable = ExtendedMock ) as set_location_list_for_window:
      with MockVimBuffers( buffers, windows ):
        ycm.UpdateWithNewDiagnosticsForFile( '/current', diagnostics )

    post_vim_message.assert_has_exact_calls( [] )
    set_location_list_for_window.assert_has_exact_calls( [] )

    assert_that(
      test_utils.VIM_PROPS_FOR_BUFFER,
      empty()
    )


  @YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                            'g:ycm_always_populate_location_list': 1,
                            'g:ycm_enable_diagnostic_highlighting': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_AsyncDiagnosticUpdate_SingleFile(
      self,
      ycm,
      post_vim_message,
      *args ):

    # This test simulates asynchronous diagnostic updates associated with a
    # single file (e.g. Translation Unit), but where the actual errors refer to
    # other open files and other non-open files. This is not strictly invalid,
    # nor is it completely normal, but it is supported and does work.

    # Contrast with the next test which sends the diagnostics filewise, which
    # is what the language server protocol will do.

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
      ], False )
    ] )

    assert_that(
      test_utils.VIM_PROPS_FOR_BUFFER,
      has_entries( {
        1: contains_exactly(
          VimProp( 'YcmErrorProperty', 1, 1, 1, 1 )
        )
      } )
    )


  @YouCompleteMeInstance( { 'g:ycm_echo_current_diagnostic': 1,
                            'g:ycm_always_populate_location_list': 1,
                            'g:ycm_enable_diagnostic_highlighting': 1 } )
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
  def test_YouCompleteMe_AsyncDiagnosticUpdate_PerFile(
      self,
      ycm,
      post_vim_message,
      *args ):

    # This test simulates asynchronous diagnostic updates which are delivered
    # per file, including files which are open and files which are not.

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
      ], False ),

      call( 3, [
        {
          'lnum': 3,
          'col': 3,
          'bufnr': 3,
          'valid': 1,
          'type': 'E',
          'text': 'error text in a buffer open in a separate window',
        },
      ], False )
    ] )

    assert_that(
      test_utils.VIM_PROPS_FOR_BUFFER,
      has_entries( {
        1: contains_exactly(
          VimProp( 'YcmErrorProperty', 1, 1, 1, 1 )
        ),
        3: contains_exactly(
          VimProp( 'YcmErrorProperty', 3, 3, 3, 3 )
        )
      } )
    )


  @YouCompleteMeInstance()
  def test_YouCompleteMe_OnPeriodicTick_ServerNotRunning( self, ycm ):
    with patch.object( ycm, 'IsServerAlive', return_value = False ):
      assert_that( ycm.OnPeriodicTick(), equal_to( False ) )


  @YouCompleteMeInstance()
  def test_YouCompleteMe_OnPeriodicTick_ServerNotReady( self, ycm ):
    with patch.object( ycm, 'IsServerAlive', return_value = True ):
      with patch.object( ycm, 'IsServerReady', return_value = False ):
        assert_that( ycm.OnPeriodicTick(), equal_to( True ) )


  @YouCompleteMeInstance()
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.client.base_request._ValidateResponseObject',
          return_value = True )
  @patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
  def test_YouCompleteMe_OnPeriodicTick_DontRetry(
      self,
      ycm,
      post_data_to_handler_async,
      *args ):

    current_buffer = VimBuffer( '/current',
                                filetype = 'ycmtest',
                                number = 1 )

    # Create the request and make the first poll; we expect no response
    with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
      assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
      post_data_to_handler_async.assert_called()

    assert ycm._message_poll_requests[ 'ycmtest' ] is not None
    post_data_to_handler_async.reset_mock()

    # OK that sent the request, now poll to check if it is complete (say it is
    # not)
    with MockVimBuffers( [ current_buffer ],
                         [ current_buffer ],
                         ( 1, 1 ) ) as v:
      mock_response = MockAsyncServerResponseInProgress()
      with patch.dict( ycm._message_poll_requests, {} ):
        ycm._message_poll_requests[ 'ycmtest' ] = MessagesPoll(
                                                    v.current.buffer )
        ycm._message_poll_requests[ 'ycmtest' ]._response_future = mock_response
        mock_future = ycm._message_poll_requests[ 'ycmtest' ]._response_future
        poll_again = ycm.OnPeriodicTick()
        mock_future.done.assert_called()
        mock_future.result.assert_not_called()
        assert_that( poll_again, equal_to( True ) )

    # Poll again, but return a response (telling us to stop polling)
    with MockVimBuffers( [ current_buffer ],
                         [ current_buffer ],
                         ( 1, 1 ) ) as v:
      mock_response = MockAsyncServerResponseDone( False )
      with patch.dict( ycm._message_poll_requests, {} ):
        ycm._message_poll_requests[ 'ycmtest' ] = MessagesPoll(
                                                    v.current.buffer )
        ycm._message_poll_requests[ 'ycmtest' ]._response_future = mock_response
        mock_future = ycm._message_poll_requests[ 'ycmtest' ]._response_future
        poll_again = ycm.OnPeriodicTick()
        mock_future.done.assert_called()
        mock_future.result.assert_called()
        post_data_to_handler_async.assert_not_called()
        # We reset and don't poll anymore
        assert_that( ycm._message_poll_requests[ 'ycmtest' ] is None )
        assert_that( poll_again, equal_to( False ) )



  @YouCompleteMeInstance()
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.client.base_request._ValidateResponseObject',
          return_value = True )
  @patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
  def test_YouCompleteMe_OnPeriodicTick_Exception(
      self,
      ycm,
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
    with MockVimBuffers( [ current_buffer ],
                         [ current_buffer ],
                         ( 1, 1 ) ) as v:
      mock_response = MockAsyncServerResponseException(
                        RuntimeError( 'test' ) )
      with patch.dict( ycm._message_poll_requests, {} ):
        ycm._message_poll_requests[ 'ycmtest' ] = MessagesPoll(
                                                    v.current.buffer )
        ycm._message_poll_requests[ 'ycmtest' ]._response_future = mock_response
        mock_future = ycm._message_poll_requests[ 'ycmtest' ]._response_future
        assert_that( ycm.OnPeriodicTick(), equal_to( False ) )
        mock_future.done.assert_called()
        mock_future.result.assert_called()
        post_data_to_handler_async.assert_not_called()
        # We reset and don't poll anymore
        assert_that( ycm._message_poll_requests[ 'ycmtest' ] is None )


  @YouCompleteMeInstance()
  @patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
          return_value = True )
  @patch( 'ycm.client.base_request._ValidateResponseObject',
          return_value = True )
  @patch( 'ycm.client.base_request.BaseRequest.PostDataToHandlerAsync' )
  @patch( 'ycm.client.messages_request._HandlePollResponse' )
  def test_YouCompleteMe_OnPeriodicTick_ValidResponse(
      self, ycm, handle_poll_response, post_data_to_handler_async, *args ):

    current_buffer = VimBuffer( '/current',
                                filetype = 'ycmtest',
                                number = 1 )

    # Create the request and make the first poll; we expect no response
    with MockVimBuffers( [ current_buffer ],
                         [ current_buffer ],
                         ( 1, 1 ) ):
      assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
      post_data_to_handler_async.assert_called()

    post_data_to_handler_async.reset_mock()

    # Poll again, and return a _proper_ response (finally!).
    # Note, _HandlePollResponse is tested independently (for simplicity)
    with MockVimBuffers( [ current_buffer ],
                         [ current_buffer ],
                         ( 1, 1 ) ) as v:
      mock_response = MockAsyncServerResponseDone( [] )
      with patch.dict( ycm._message_poll_requests, {} ):
        ycm._message_poll_requests[ 'ycmtest' ] = MessagesPoll(
                                                    v.current.buffer )
        ycm._message_poll_requests[ 'ycmtest' ]._response_future = mock_response
        mock_future = ycm._message_poll_requests[ 'ycmtest' ]._response_future
        assert_that( ycm.OnPeriodicTick(), equal_to( True ) )
        handle_poll_response.assert_called()
        mock_future.done.assert_called()
        mock_future.result.assert_called()
        post_data_to_handler_async.assert_called() # Poll again!
        assert_that( ycm._message_poll_requests[ 'ycmtest' ] is not None )


  @YouCompleteMeInstance()
  @patch( 'ycm.client.completion_request.CompletionRequest.OnCompleteDone' )
  def test_YouCompleteMe_OnCompleteDone_CompletionRequest(
      self, ycm, on_complete_done ):
    current_buffer = VimBuffer( 'current_buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ], ( 1, 1 ) ):
      ycm.SendCompletionRequest()
    ycm.OnCompleteDone()
    on_complete_done.assert_called()


  @YouCompleteMeInstance()
  @patch( 'ycm.client.completion_request.CompletionRequest.OnCompleteDone' )
  def test_YouCompleteMe_OnCompleteDone_NoCompletionRequest(
      self, ycm, on_complete_done ):
    ycm.OnCompleteDone()
    on_complete_done.assert_not_called()


  @YouCompleteMeInstance()
  def test_YouCompleteMe_ShouldResendFileParseRequest_NoParseRequest(
      self, ycm ):
    current_buffer = VimBuffer( 'current_buffer' )
    with MockVimBuffers( [ current_buffer ], [ current_buffer ] ):
      assert_that( ycm.ShouldResendFileParseRequest(), equal_to( False ) )

# Copyright (C) 2016-2017 YouCompleteMe contributors
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

from ycm.tests.test_utils import ( ExtendedMock, MockVimBuffers, MockVimModule,
                                   VimBuffer, VimMatch )
MockVimModule()

import os
import sys
from hamcrest import ( assert_that, contains, empty, is_in, is_not, has_length,
                       matches_regexp )
from mock import call, MagicMock, patch

from ycm.tests import StopServer, test_utils, YouCompleteMeInstance
from ycm.client.base_request import _LoadExtraConfFile
from ycmd.responses import ServerError


@YouCompleteMeInstance()
def YouCompleteMe_YcmCoreNotImported_test( ycm ):
  assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def RunNotifyUserIfServerCrashed( ycm, test, post_vim_message ):
  StopServer( ycm )

  ycm._logger = MagicMock( autospec = True )
  ycm._server_popen = MagicMock( autospec = True )
  ycm._server_popen.poll.return_value = test[ 'return_code' ]
  ycm._server_popen.stderr.read.return_value = test[ 'stderr_output' ]

  ycm._NotifyUserIfServerCrashed()

  assert_that( ycm._logger.method_calls,
               has_length( len( test[ 'expected_logs' ] ) ) )
  ycm._logger.error.assert_has_calls(
    [ call( log ) for log in test[ 'expected_logs' ] ] )
  post_vim_message.assert_has_exact_calls( [
    call( test[ 'expected_vim_message' ] )
  ] )


def YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedCore_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "Unexpected error while loading the YCM core library. "
              "Use the ':YcmToggleLogs' command to check the logs." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 3,
    'stderr_output' : '',
    'expected_logs': [ message ],
    'expected_vim_message': message
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_MissingCore_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library not detected; you need to compile YCM before "
              "using it. Follow the instructions in the documentation." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 4,
    'stderr_output': '',
    'expected_logs': [ message ],
    'expected_vim_message': message
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_Python2Core_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library compiled for Python 2 but loaded in Python 3. "
              "Set the 'g:ycm_server_python_interpreter' option to a Python 2 "
              "interpreter path." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 5,
    'stderr_output': '',
    'expected_logs': [ message ],
    'expected_vim_message': message
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_Python3Core_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library compiled for Python 3 but loaded in Python 2. "
              "Set the 'g:ycm_server_python_interpreter' option to a Python 3 "
              "interpreter path." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 6,
    'stderr_output': '',
    'expected_logs': [ message ],
    'expected_vim_message': message
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_OutdatedCore_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "YCM core library too old; PLEASE RECOMPILE by running the "
              "install.py script. See the documentation for more details." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 7,
    'stderr_output': '',
    'expected_logs': [ message ],
    'expected_vim_message': message
  } )


def YouCompleteMe_NotifyUserIfServerCrashed_UnexpectedExitCode_test():
  message = ( "The ycmd server SHUT DOWN (restart with ':YcmRestartServer'). "
              "Unexpected exit code 1. Use the ':YcmToggleLogs' command to "
              "check the logs." )
  RunNotifyUserIfServerCrashed( {
    'return_code': 1,
    'stderr_output': 'First line\r\n'
                     'Second line',
    'expected_logs': [ 'First line\n'
                       'Second line',
                       message ],
    'expected_vim_message': message
  } )


@YouCompleteMeInstance( { 'extra_conf_vim_data': [ 'tempname()' ] } )
def YouCompleteMe_DebugInfo_ServerRunning_test( ycm ):
  dir_of_script = os.path.dirname( os.path.abspath( __file__ ) )
  buf_name = os.path.join( dir_of_script, 'testdata', 'test.cpp' )
  extra_conf = os.path.join( dir_of_script, 'testdata', '.ycm_extra_conf.py' )
  _LoadExtraConfFile( extra_conf )

  current_buffer = VimBuffer( buf_name, filetype='cpp' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Client logfile: .+\n'
        'Server Python interpreter: .+\n'
        'Server Python version: .+\n'
        'Server has Clang support compiled in: '
        '(?P<CLANG>True)?(?(CLANG)|False)\n'
        'Clang version: .+\n'
        'Extra configuration file found and loaded\n'
        'Extra configuration path: .*testdata[/\\\\]\\.ycm_extra_conf\\.py\n'
        '(?(CLANG)C-family completer debug information:\n'
        '  Compilation database path: None\n'
        '  Flags: \\[\'_TEMP_FILE_\'.*\\]\n)'
        'Server running at: .+\n'
        'Server process ID: \d+\n'
        'Server logfiles:\n'
        '  .+\n'
        '  .+' )
    )


@YouCompleteMeInstance()
def YouCompleteMe_DebugInfo_ServerNotRunning_test( ycm ):
  StopServer( ycm )

  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Client logfile: .+\n'
        'Server errored, no debug info from server\n'
        'Server running at: .+\n'
        'Server process ID: \d+\n'
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


@YouCompleteMeInstance( { 'keep_logfiles': 1 } )
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
  logfile_buffer = VimBuffer( ycm._client_logfile, window = 1 )
  with MockVimBuffers( [ logfile_buffer ], logfile_buffer ):
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
@patch( 'ycm.vimsupport.PostVimMessage' )
def YouCompleteMe_ToggleLogs_WithoutParameters_test( ycm, post_vim_message ):
  # We test on a Python buffer because the Python completer has subserver
  # logfiles.
  python_buffer = VimBuffer( 'buffer.py', filetype = 'python' )
  with MockVimBuffers( [ python_buffer ], python_buffer ):
    ycm.ToggleLogs()

  assert_that(
    # Argument passed to PostVimMessage.
    post_vim_message.call_args[ 0 ][ 0 ],
    matches_regexp(
      'Available logfiles are:\n'
      'jedihttp_\d+_stderr_.+.log\n'
      'jedihttp_\d+_stdout_.+.log\n'
      'ycm_.+.log\n'
      'ycmd_\d+_stderr_.+.log\n'
      'ycmd_\d+_stdout_.+.log' )
  )


@YouCompleteMeInstance()
def YouCompleteMe_GetDefinedSubcommands_ListFromServer_test( ycm ):
  current_buffer = VimBuffer( 'buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.base_request.JsonFromFuture',
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
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.base_request.JsonFromFuture',
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
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.base_request.JsonFromFuture',
                return_value = { 'message': 'some_detailed_diagnostic' } ):
      ycm.ShowDetailedDiagnostic(),

  post_vim_message.assert_has_exact_calls( [
    call( 'some_detailed_diagnostic', warning = False )
  ] )


@YouCompleteMeInstance()
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_FiletypeNotSupported_test( ycm,
                                                             post_vim_message ):

  current_buffer = VimBuffer( 'buffer', filetype = 'not_supported' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    ycm.ShowDiagnostics()

  post_vim_message.assert_called_once_with(
    'Native filetype completion not supported for current file, '
    'cannot force recompilation.', warning = False )


@YouCompleteMeInstance()
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationList', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_NoDiagnosticsDetected_test(
  ycm, set_location_list, post_vim_message, *args ):

  current_buffer = VimBuffer( 'buffer', filetype = 'cpp' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = {} ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False ),
    call( 'No warnings or errors detected.', warning = False )
  ] )
  set_location_list.assert_called_once_with( [] )


@YouCompleteMeInstance( { 'log_level': 'debug',
                          'keep_logfiles': 1,
                          'open_loclist_on_ycm_diags': 0 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.youcompleteme.YouCompleteMe.IsServerReady', return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationList', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_DiagnosticsFound_DoNotOpenLocationList_test(
  ycm, set_location_list, post_vim_message, *args ):

  diagnostic = {
    'kind': 'ERROR',
    'text': 'error text',
    'location': {
      'filepath': 'buffer',
      'line_num': 19,
      'column_num': 2
    }
  }

  current_buffer = VimBuffer( 'buffer', filetype = 'cpp', number = 3 )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = [ diagnostic ] ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False )
  ] )
  set_location_list.assert_called_once_with( [ {
      'bufnr': 3,
      'lnum': 19,
      'col': 2,
      'text': 'error text',
      'type': 'E',
      'valid': 1
  } ] )


@YouCompleteMeInstance( { 'open_loclist_on_ycm_diags': 1 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.youcompleteme.YouCompleteMe.IsServerReady', return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.SetLocationList', new_callable = ExtendedMock )
@patch( 'ycm.vimsupport.OpenLocationList', new_callable = ExtendedMock )
def YouCompleteMe_ShowDiagnostics_DiagnosticsFound_OpenLocationList_test(
  ycm, open_location_list, set_location_list, post_vim_message, *args ):

  diagnostic = {
    'kind': 'ERROR',
    'text': 'error text',
    'location': {
      'filepath': 'buffer',
      'line_num': 19,
      'column_num': 2
    }
  }

  current_buffer = VimBuffer( 'buffer', filetype = 'cpp', number = 3 )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = [ diagnostic ] ):
      ycm.ShowDiagnostics()

  post_vim_message.assert_has_exact_calls( [
    call( 'Forcing compilation, this will block Vim until done.',
          warning = False ),
    call( 'Diagnostics refreshed', warning = False )
  ] )
  set_location_list.assert_called_once_with( [ {
      'bufnr': 3,
      'lnum': 19,
      'col': 2,
      'text': 'error text',
      'type': 'E',
      'valid': 1
  } ] )
  open_location_list.assert_called_once_with( focus = True )


@YouCompleteMeInstance( { 'echo_current_diagnostic': 1,
                          'enable_diagnostic_signs': 1,
                          'enable_diagnostic_highlighting': 1 } )
@patch( 'ycm.youcompleteme.YouCompleteMe.FiletypeCompleterExistsForFiletype',
        return_value = True )
@patch( 'ycm.youcompleteme.YouCompleteMe.IsServerReady', return_value = True )
@patch( 'ycm.vimsupport.PostVimMessage', new_callable = ExtendedMock )
@patch( 'vim.command', new_callable = ExtendedMock )
def YouCompleteMe_UpdateDiagnosticInterface_PrioritizeErrorsOverWarnings_test(
  ycm, vim_command, post_vim_message, *args ):

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
                              number = 5,
                              window = 2 )

  test_utils.VIM_MATCHES = []

  with MockVimBuffers( [ current_buffer ], current_buffer, ( 3, 1 ) ):
    with patch( 'ycm.client.event_notification.EventNotification.Response',
                return_value = diagnostics ):
      ycm.OnFileReadyToParse( block = True )

    # Error match is added after warning matches.
    assert_that(
      test_utils.VIM_MATCHES,
      contains(
        VimMatch( 'YcmWarningSection', '\%3l\%5c\_.\{-}\%3l\%7c' ),
        VimMatch( 'YcmWarningSection', '\%3l\%3c\_.\{-}\%3l\%9c' ),
        VimMatch( 'YcmErrorSection', '\%3l\%8c' )
      )
    )

    # Only the error sign is placed.
    vim_command.assert_has_exact_calls( [
      call( 'sign define ycm_dummy_sign' ),
      call( 'sign place 3 name=ycm_dummy_sign line=3 buffer=5' ),
      call( 'sign place 1 name=YcmError line=3 buffer=5' ),
      call( 'sign undefine ycm_dummy_sign' ),
      call( 'sign unplace 3 buffer=5' )
    ] )

    # When moving the cursor on the diagnostics, the error is displayed to the
    # user, not the warning.
    ycm.OnCursorMoved()
    post_vim_message.assert_has_exact_calls( [
      call( "expected ';' after expression (FixIt)",
            truncate = True, warning = False )
    ] )

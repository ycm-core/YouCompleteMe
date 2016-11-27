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

from ycm.tests import StopServer
from ycm.tests.test_utils import ( ExtendedMock, MockVimBuffers, MockVimModule,
                                   VimBuffer )
MockVimModule()

import os
import sys
from hamcrest import assert_that, is_in, is_not, has_length, matches_regexp
from mock import call, MagicMock, patch

from ycm.tests import YouCompleteMeInstance


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


@YouCompleteMeInstance()
def YouCompleteMe_DebugInfo_ServerRunning_test( ycm ):
  current_buffer = VimBuffer( 'current_buffer' )
  with MockVimBuffers( [ current_buffer ], current_buffer ):
    assert_that(
      ycm.DebugInfo(),
      matches_regexp(
        'Client logfile: .+\n'
        'Server has Clang support compiled in: (True|False)\n'
        '(Clang version: .+\n)?'
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
        'Server crashed, no debug info from server\n'
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
  ycm.ToggleLogs()

  assert_that(
    # Argument passed to PostVimMessage.
    post_vim_message.call_args[ 0 ][ 0 ],
    matches_regexp(
      'Available logfiles are:\n'
      'ycm_.+.log\n'
      'ycmd_\d+_stderr_.+.log\n'
      'ycmd_\d+_stdout_.+.log' )
  )

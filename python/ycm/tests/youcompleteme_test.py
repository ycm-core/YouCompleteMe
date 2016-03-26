# coding: utf-8
#
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

import contextlib
import functools
import os
import sys
from mock import MagicMock, patch
from hamcrest import ( assert_that, contains_inanyorder, has_entries, is_in,
                       is_not )

from ycm.youcompleteme import YouCompleteMe
from ycmd import user_options_store
from ycmd.utils import ToBytes, ReadFile

# The default options which are only relevant to the client, not the server and
# thus are not part of default_options.json, but are required for a working
# YouCompleteMe object.
DEFAULT_CLIENT_OPTIONS = {
  'server_log_level': 'debug',
  'extra_conf_vim_data': [],
}


def CompletionEntryMatcher( word, menu ):
  return has_entries( { 'word': word,
                        'menu': menu,
                        'dup': 1,
                        'empty': 1 } )


@contextlib.contextmanager
def MockBuffer( contents, line, column, filetype, encoding ):
  """Mock a Vim buffer with contents, cursor at (line, column), filetype, and
  encoding. Line and column are 1-based. Column is byte indexed."""
  def VimEval( value ):
    """Minimal mock of the vim.eval() function to run the tests."""

    # Called by OnFileReadyToParse in OmniCompleter class.
    if value == '&omnifunc':
      return ''

    # Called by CurrentFiletypes in NativeFiletypeCompletionAvailable.
    if value == '&filetype':
      return filetype

    # Called by GetEncoding in ToUnicodeWithVimEncoding.
    if value == '&encoding':
      return encoding

    # Called by BufferModified in GetUnsavedAndCurrentBufferData.
    if value == 'getbufvar(0, "&ft")':
      return filetype

    # Called by FiletypesForBuffer in GetUnsavedAndCurrentBufferData.
    if value == 'getbufvar(0, "&mod")':
      return 1

    raise ValueError( 'Unexpected evaluation' )

  vim_contents = [ ToBytes( l ) for l in contents.splitlines() ]

  vim_current = MagicMock()
  vim_current.window.cursor = ( line, column )
  vim_current.line = vim_contents[ line - 1 ]

  current_buffer = MagicMock()
  current_buffer.name = 'TEST_BUFFER'
  current_buffer.number = 0
  current_buffer.__iter__.return_value = vim_contents

  with patch( 'vim.current', vim_current ):
    with patch( 'vim.buffers', [ current_buffer ] ):
      with patch( 'vim.current.buffer', current_buffer ):
        with patch( 'vim.eval', side_effect=VimEval ):
          yield


def SetUpYcm( test ):
  @functools.wraps( test )
  def Wrapper( *args, **kwargs ):
    try:
      options = dict( user_options_store.DefaultOptions() )
      options.update( DEFAULT_CLIENT_OPTIONS )
      user_options_store.SetAll( options )
      ycm = YouCompleteMe( user_options_store.GetAll() )
      test( ycm, *args, **kwargs )
    finally:
      # Write ycmd logs to nosetests stdout.
      if os.path.exists( ycm._server_stderr ):
        sys.stdout.write( ReadFile( ycm._server_stderr ) )
      if os.path.exists( ycm._server_stdout ):
        sys.stdout.write( ReadFile( ycm._server_stdout ) )
      ycm.OnVimLeave()
  return Wrapper


@SetUpYcm
def YouCompleteMe_YcmCoreNotImported_test( ycm ):
  assert_that( 'ycm_core', is_not( is_in( sys.modules ) ) )


def RunCompletionTest( ycm, test ):
  vim_buffer = test[ 'buffer' ]
  with MockBuffer( vim_buffer[ 'contents' ],
                   vim_buffer[ 'line' ],
                   vim_buffer[ 'column' ],
                   vim_buffer[ 'filetype' ],
                   vim_buffer[ 'encoding' ] ):
    ycm.OnFileReadyToParse()
    ycm.CreateCompletionRequest()
    request = ycm.GetCurrentCompletionRequest()
    request.Start()
    while not request.Done():
      pass
    assert_that( request.Response(), test[ 'expect' ][ 'completions' ] )


@SetUpYcm
def YouCompleteMe_CreateCompletionRequest_MultibyteLine_test( ycm ):
  RunCompletionTest( ycm, {
    'description': 'Completion works properly on multibyte line. '
                   'See issue #1378.',
    'buffer': {
      'contents': """identifier
中文 = id
""",
      'line': 2,
      'column': 12,
      'filetype': 'dummy_filetype',
      'encoding': 'utf8'
    },
    'expect': {
      'completions': contains_inanyorder(
        CompletionEntryMatcher( 'id', '[ID]' ),
        CompletionEntryMatcher( 'identifier', '[ID]' )
      )
    }
  } )

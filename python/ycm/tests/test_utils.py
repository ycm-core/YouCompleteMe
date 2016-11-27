# Copyright (C) 2011-2012 Google Inc.
#               2016      YouCompleteMe contributors
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

from mock import MagicMock, patch
from hamcrest import assert_that, equal_to
import contextlib
import functools
import nose
import os
import re
import sys

from ycmd.utils import GetCurrentDirectory, ToUnicode


BUFNR_REGEX = re.compile( '^bufnr\(\'(?P<buffer_filename>.+)\', ([01])\)$' )
BUFWINNR_REGEX = re.compile( '^bufwinnr\((?P<buffer_number>[0-9]+)\)$' )
BWIPEOUT_REGEX = re.compile(
  '^(?:silent! )bwipeout!? (?P<buffer_number>[0-9]+)$' )
GETBUFVAR_REGEX = re.compile(
  '^getbufvar\((?P<buffer_number>[0-9]+), "&(?P<option>.+)"\)$' )

# One-and only instance of mocked Vim object. The first 'import vim' that is
# executed binds the vim module to the instance of MagicMock that is created,
# and subsquent assignments to sys.modules[ 'vim' ] don't retrospectively
# update them. The result is that while running the tests, we must assign only
# one instance of MagicMock to sys.modules[ 'vim' ] and always return it.
#
# More explanation is available:
# https://github.com/Valloric/YouCompleteMe/pull/1694
VIM_MOCK = MagicMock()


@contextlib.contextmanager
def CurrentWorkingDirectory( path ):
  old_cwd = GetCurrentDirectory()
  os.chdir( path )
  try:
    yield
  finally:
    os.chdir( old_cwd )


def _MockGetBufferNumber( buffer_filename ):
  for vim_buffer in VIM_MOCK.buffers:
    if vim_buffer.name == buffer_filename:
      return vim_buffer.number
  return -1


def _MockGetBufferWindowNumber( buffer_number ):
  for vim_buffer in VIM_MOCK.buffers:
    if vim_buffer.number == buffer_number and vim_buffer.window:
      return vim_buffer.window
  return -1


def _MockGetBufferVariable( buffer_number, option ):
  for vim_buffer in VIM_MOCK.buffers:
    if vim_buffer.number == buffer_number:
      if option == 'mod':
        return vim_buffer.modified
      if option == 'ft':
        return vim_buffer.filetype
      return ''
  return ''


def _MockVimBufferEval( value ):
  if value == '&omnifunc':
    return VIM_MOCK.current.buffer.omnifunc

  if value == '&filetype':
    return VIM_MOCK.current.buffer.filetype

  match = BUFNR_REGEX.search( value )
  if match:
    buffer_filename = match.group( 'buffer_filename' )
    return _MockGetBufferNumber( buffer_filename )

  match = BUFWINNR_REGEX.search( value )
  if match:
    buffer_number = int( match.group( 'buffer_number' ) )
    return _MockGetBufferWindowNumber( buffer_number )

  match = GETBUFVAR_REGEX.search( value )
  if match:
    buffer_number = int( match.group( 'buffer_number' ) )
    option = match.group( 'option' )
    return _MockGetBufferVariable( buffer_number, option )

  return None


def _MockVimOptionsEval( value ):
  if value == '&previewheight':
    return 12

  if value == '&columns':
    return 80

  if value == '&ruler':
    return 0

  if value == '&showcmd':
    return 1

  return None


def _MockVimEval( value ):
  if value == 'g:ycm_min_num_of_chars_for_completion':
    return 0

  if value == 'g:ycm_server_python_interpreter':
    return ''

  if value == 'tempname()':
    return '_TEMP_FILE_'

  if value == 'complete_check()':
    return 0

  if value == 'tagfiles()':
    return [ 'tags' ]

  result = _MockVimOptionsEval( value )
  if result is not None:
    return result

  result = _MockVimBufferEval( value )
  if result is not None:
    return result

  raise ValueError( 'Unexpected evaluation: {0}'.format( value ) )


def _MockWipeoutBuffer( buffer_number ):
  buffers = VIM_MOCK.buffers

  for index, buffer in enumerate( buffers ):
    if buffer.number == buffer_number:
      return buffers.pop( index )


def MockVimCommand( command ):
  match = BWIPEOUT_REGEX.search( command )
  if match:
    return _MockWipeoutBuffer( int( match.group( 1 ) ) )

  raise RuntimeError( 'Unexpected command: ' + command )


class VimBuffer( object ):
  """An object that looks like a vim.buffer object:
   - |name|    : full path of the buffer with symbolic links resolved;
   - |number|  : buffer number;
   - |contents|: list of lines representing the buffer contents;
   - |filetype|: buffer filetype. Empty string if no filetype is set;
   - |modified|: True if the buffer has unsaved changes, False otherwise;
   - |window|  : number of the buffer window. None if the buffer is hidden;
   - |omnifunc|: omni completion function used by the buffer."""

  def __init__( self, name,
                      number = 1,
                      contents = [],
                      filetype = '',
                      modified = True,
                      window = None,
                      omnifunc = '' ):
    self.name = os.path.realpath( name ) if name else ''
    self.number = number
    self.contents = contents
    self.filetype = filetype
    self.modified = modified
    self.window = window
    self.omnifunc = omnifunc


  def __getitem__( self, index ):
    """Returns the bytes for a given line at index |index|."""
    return self.contents[ index ]


  def __len__( self ):
    return len( self.contents )


  def __setitem__( self, key, value ):
    return self.contents.__setitem__( key, value )


  def GetLines( self ):
    """Returns the contents of the buffer as a list of unicode strings."""
    return [ ToUnicode( x ) for x in self.contents ]


@contextlib.contextmanager
def MockVimBuffers( buffers, current_buffer, cursor_position = ( 1, 1 ) ):
  """Simulates the Vim buffers list |buffers| where |current_buffer| is the
  buffer displayed in the current window and |cursor_position| is the current
  cursor position. All buffers are represented by a VimBuffer object."""
  if current_buffer not in buffers:
    raise RuntimeError( 'Current buffer must be part of the buffers list.' )

  with patch( 'vim.buffers', buffers ):
    with patch( 'vim.current.buffer', current_buffer ):
      with patch( 'vim.current.window.cursor', cursor_position ):
        yield


def MockVimModule():
  """The 'vim' module is something that is only present when running inside the
  Vim Python interpreter, so we replace it with a MagicMock for tests. If you
  need to add additional mocks to vim module functions, then use 'patch' from
  mock module, to ensure that the state of the vim mock is returned before the
  next test. That is:

    from ycm.tests.test_utils import MockVimModule
    from mock import patch

    # Do this once
    MockVimModule()

    @patch( 'vim.eval', return_value='test' )
    @patch( 'vim.command', side_effect=ValueError )
    def test( vim_command, vim_eval ):
      # use vim.command via vim_command, e.g.:
      vim_command.assert_has_calls( ... )

  Failure to use this approach may lead to unexpected failures in other
  tests."""

  VIM_MOCK.buffers = {}
  VIM_MOCK.eval = MagicMock( side_effect = _MockVimEval )
  sys.modules[ 'vim' ] = VIM_MOCK

  return VIM_MOCK


class ExtendedMock( MagicMock ):
  """An extension to the MagicMock class which adds the ability to check that a
  callable is called with a precise set of calls in a precise order.

  Example Usage:
    from ycm.tests.test_utils import ExtendedMock
    @patch( 'test.testing', new_callable = ExtendedMock, ... )
    def my_test( test_testing ):
      ...
  """

  def assert_has_exact_calls( self, calls, any_order = False ):
    self.assert_has_calls( calls, any_order )
    assert_that( self.call_count, equal_to( len( calls ) ) )


def ExpectedFailure( reason, *exception_matchers ):
  """Defines a decorator to be attached to tests. This decorator
  marks the test as being known to fail, e.g. where documenting or exercising
  known incorrect behaviour.

  The parameters are:
    - |reason| a textual description of the reason for the known issue. This
               is used for the skip reason
    - |exception_matchers| additional arguments are hamcrest matchers to apply
                 to the exception thrown. If the matchers don't match, then the
                 test is marked as error, with the original exception.

  If the test fails (for the correct reason), then it is marked as skipped.
  If it fails for any other reason, it is marked as failed.
  If the test passes, then it is also marked as failed."""
  def decorator( test ):
    @functools.wraps( test )
    def Wrapper( *args, **kwargs ):
      try:
        test( *args, **kwargs )
      except Exception as test_exception:
        # Ensure that we failed for the right reason
        test_exception_message = ToUnicode( test_exception )
        try:
          for matcher in exception_matchers:
            assert_that( test_exception_message, matcher )
        except AssertionError:
          # Failed for the wrong reason!
          import traceback
          print( 'Test failed for the wrong reason: ' + traceback.format_exc() )
          # Real failure reason is the *original* exception, we're only trapping
          # and ignoring the exception that is expected.
          raise test_exception

        # Failed for the right reason
        raise nose.SkipTest( reason )
      else:
        raise AssertionError( 'Test was expected to fail: {0}'.format(
          reason ) )
    return Wrapper

  return decorator

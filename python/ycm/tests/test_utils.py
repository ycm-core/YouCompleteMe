# Copyright (C) 2011-2018 YouCompleteMe contributors
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

from collections import defaultdict, namedtuple
from future.utils import iteritems, PY2
from mock import DEFAULT, MagicMock, patch
from hamcrest import assert_that, equal_to
import contextlib
import functools
import json
import nose
import os
import re
import sys

from ycmd.utils import GetCurrentDirectory, ToBytes, ToUnicode


BUFNR_REGEX = re.compile( '^bufnr\(\'(?P<buffer_filename>.+)\', ([01])\)$' )
BUFWINNR_REGEX = re.compile( '^bufwinnr\((?P<buffer_number>[0-9]+)\)$' )
BWIPEOUT_REGEX = re.compile(
  '^(?:silent! )bwipeout!? (?P<buffer_number>[0-9]+)$' )
GETBUFVAR_REGEX = re.compile(
  '^getbufvar\((?P<buffer_number>[0-9]+), "(?P<option>.+)"\)$' )
MATCHADD_REGEX = re.compile(
  '^matchadd\(\'(?P<group>.+)\', \'(?P<pattern>.+)\'\)$' )
MATCHDELETE_REGEX = re.compile( '^matchdelete\((?P<id>\d+)\)$' )
OMNIFUNC_REGEX_FORMAT = (
  '^{omnifunc_name}\((?P<findstart>[01]),[\'"](?P<base>.*)[\'"]\)$' )
FNAMEESCAPE_REGEX = re.compile( '^fnameescape\(\'(?P<filepath>.+)\'\)$' )
SIGN_LIST_REGEX = re.compile(
  "^silent! sign place buffer=(?P<bufnr>\d+)$" )
SIGN_PLACE_REGEX = re.compile(
  '^sign place (?P<id>\d+) name=(?P<name>\w+) line=(?P<line>\d+) '
  'buffer=(?P<bufnr>\d+)$' )
SIGN_UNPLACE_REGEX = re.compile(
  '^sign unplace (?P<id>\d+) buffer=(?P<bufnr>\d+)$' )
REDIR_START_REGEX = re.compile( '^redir => (?P<variable>[\w:]+)$' )
REDIR_END_REGEX = re.compile( '^redir END$' )
EXISTS_REGEX = re.compile( '^exists\( \'(?P<option>[\w:]+)\' \)$' )
LET_REGEX = re.compile( '^let (?P<option>[\w:]+) = (?P<value>.*)$' )
HAS_PATCH_REGEX = re.compile( '^has\( \'patch(?P<patch>\d+)\' \)$' )

# One-and only instance of mocked Vim object. The first 'import vim' that is
# executed binds the vim module to the instance of MagicMock that is created,
# and subsquent assignments to sys.modules[ 'vim' ] don't retrospectively
# update them. The result is that while running the tests, we must assign only
# one instance of MagicMock to sys.modules[ 'vim' ] and always return it.
#
# More explanation is available:
# https://github.com/Valloric/YouCompleteMe/pull/1694
VIM_MOCK = MagicMock()

VIM_MATCHES_FOR_WINDOW = defaultdict( list )
VIM_SIGNS = []

VIM_OPTIONS = {
  '&previewheight': 12,
  '&columns': 80,
  '&ruler': 0,
  '&showcmd': 1,
  '&hidden': 0,
  '&expandtab': 1
}

# This variable must be patched with a Version object for tests depending on the
# Vim version. Example:
#
#   @patch( 'ycm.tests.test_utils.VIM_VERSION', Version( 7, 4, 1578 ) )
#   def ThisTestDependsOnTheVimVersion_test():
#     ...
#
VIM_VERSION = None

REDIR = {
  'status': False,
  'variable': '',
  'output': ''
}


Version = namedtuple( 'Version', [ 'major', 'minor', 'patch' ] )


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
  for window in VIM_MOCK.windows:
    if window.buffer.number == buffer_number:
      return window.number
  return -1


def _MockGetBufferVariable( buffer_number, option ):
  for vim_buffer in VIM_MOCK.buffers:
    if vim_buffer.number == buffer_number:
      if option == '&mod':
        return vim_buffer.modified
      if option == '&ft':
        return vim_buffer.filetype
      if option == 'changedtick':
        return vim_buffer.changedtick
      if option == '&bh':
        return vim_buffer.bufhidden
      return ''
  return ''


def _MockVimBufferEval( value ):
  if value == '&omnifunc':
    return VIM_MOCK.current.buffer.omnifunc_name

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

  current_buffer = VIM_MOCK.current.buffer
  match = re.search( OMNIFUNC_REGEX_FORMAT.format(
                         omnifunc_name = current_buffer.omnifunc_name ),
                     value )
  if match:
    findstart = int( match.group( 'findstart' ) )
    base = match.group( 'base' )
    value = current_buffer.omnifunc( findstart, base )
    return value if findstart else ToBytesOnPY2( value )

  return None


def _MockVimOptionsEval( value ):
  result = VIM_OPTIONS.get( value )
  if result is not None:
    return result

  if value == 'keys( g: )':
    global_options = {}
    for key, value in iteritems( VIM_OPTIONS ):
      if key.startswith( 'g:' ):
        global_options[ key[ 2: ] ] = value
    return global_options

  match = EXISTS_REGEX.search( value )
  if match:
    option = match.group( 'option' )
    return option in VIM_OPTIONS

  return None


def _MockVimFunctionsEval( value ):
  if value == 'tempname()':
    return '_TEMP_FILE_'

  if value == 'tagfiles()':
    return [ 'tags' ]

  if value == 'shiftwidth()':
    return 2

  return None


def _MockVimMatchEval( value ):
  current_window = VIM_MOCK.current.window.number

  if value == 'getmatches()':
    return VIM_MATCHES_FOR_WINDOW[ current_window ]

  match = MATCHADD_REGEX.search( value )
  if match:
    group = match.group( 'group' )
    option = match.group( 'pattern' )
    vim_match = VimMatch( group, option )
    VIM_MATCHES_FOR_WINDOW[ current_window ].append( vim_match )
    return vim_match.id

  match = MATCHDELETE_REGEX.search( value )
  if match:
    match_id = int( match.group( 'id' ) )
    vim_matches = VIM_MATCHES_FOR_WINDOW[ current_window ]
    for index, vim_match in enumerate( vim_matches ):
      if vim_match.id == match_id:
        vim_matches.pop( index )
        return -1
    return 0

  return None


def _MockVimVersionEval( value ):
  match = HAS_PATCH_REGEX.search( value )
  if match:
    if not isinstance( VIM_VERSION, Version ):
      raise RuntimeError( 'Vim version is not set.' )
    return VIM_VERSION.patch >= int( match.group( 'patch' ) )

  if value == 'v:version':
    if not isinstance( VIM_VERSION, Version ):
      raise RuntimeError( 'Vim version is not set.' )
    return VIM_VERSION.major * 100 + VIM_VERSION.minor

  return None


def _MockVimEval( value ):
  result = _MockVimOptionsEval( value )
  if result is not None:
    return result

  result = _MockVimFunctionsEval( value )
  if result is not None:
    return result

  result = _MockVimBufferEval( value )
  if result is not None:
    return result

  result = _MockVimMatchEval( value )
  if result is not None:
    return result

  result = _MockVimVersionEval( value )
  if result is not None:
    return result

  match = FNAMEESCAPE_REGEX.search( value )
  if match:
    return match.group( 'filepath' )

  if value == REDIR[ 'variable' ]:
    return REDIR[ 'output' ]

  raise VimError( 'Unexpected evaluation: {0}'.format( value ) )


def _MockWipeoutBuffer( buffer_number ):
  buffers = VIM_MOCK.buffers

  for index, buffer in enumerate( buffers ):
    if buffer.number == buffer_number:
      return buffers.pop( index )


def _MockSignCommand( command ):
  match = SIGN_LIST_REGEX.search( command )
  if match and REDIR[ 'status' ]:
    bufnr = int( match.group( 'bufnr' ) )
    REDIR[ 'output' ] = ( '--- Signs ---\n'
                          'Signs for foo:\n' )
    for sign in VIM_SIGNS:
      if sign.bufnr == bufnr:
        REDIR[ 'output' ] += (
          '    line={0}  id={1}  name={2}'.format( sign.line,
                                                   sign.id,
                                                   sign.name ) )
    return True

  match = SIGN_PLACE_REGEX.search( command )
  if match:
    VIM_SIGNS.append( VimSign( int( match.group( 'id' ) ),
                               int( match.group( 'line' ) ),
                               match.group( 'name' ),
                               int( match.group( 'bufnr' ) ) ) )
    return True

  match = SIGN_UNPLACE_REGEX.search( command )
  if match:
    sign_id = int( match.group( 'id' ) )
    bufnr = int( match.group( 'bufnr' ) )
    for sign in VIM_SIGNS:
      if sign.id == sign_id and sign.bufnr == bufnr:
        VIM_SIGNS.remove( sign )
        return True

  return False


def _MockVimCommand( command ):
  match = BWIPEOUT_REGEX.search( command )
  if match:
    return _MockWipeoutBuffer( int( match.group( 1 ) ) )

  match = REDIR_START_REGEX.search( command )
  if match:
    REDIR[ 'status' ] = True
    REDIR[ 'variable' ] = match.group( 'variable' )
    return

  match = REDIR_END_REGEX.search( command )
  if match:
    REDIR[ 'status' ] = False
    return

  if command == 'unlet ' + REDIR[ 'variable' ]:
    REDIR[ 'variable' ] = ''
    return

  result = _MockSignCommand( command )
  if result:
    return

  match = LET_REGEX.search( command )
  if match:
    option = match.group( 'option' )
    value = json.loads( match.group( 'value' ) )
    VIM_OPTIONS[ option ] = value
    return

  return DEFAULT


class VimBuffer( object ):
  """An object that looks like a vim.buffer object:
   - |name|     : full path of the buffer with symbolic links resolved;
   - |number|   : buffer number;
   - |contents| : list of lines representing the buffer contents;
   - |filetype| : buffer filetype. Empty string if no filetype is set;
   - |modified| : True if the buffer has unsaved changes, False otherwise;
   - |bufhidden|: value of the 'bufhidden' option (see :h bufhidden);
   - |omnifunc| : omni completion function used by the buffer. Must be a Python
                  function that takes the same arguments and returns the same
                  values as a Vim completion function (:h complete-functions).
                  Example:

                    def Omnifunc( findstart, base ):
                      if findstart:
                        return 5
                      return [ 'a', 'b', 'c' ]"""

  def __init__( self, name,
                      number = 1,
                      contents = [ '' ],
                      filetype = '',
                      modified = False,
                      bufhidden = '',
                      omnifunc = None,
                      visual_start = None,
                      visual_end = None ):
    self.name = os.path.realpath( name ) if name else ''
    self.number = number
    self.contents = contents
    self.filetype = filetype
    self.modified = modified
    self.bufhidden = bufhidden
    self.omnifunc = omnifunc
    self.omnifunc_name = omnifunc.__name__ if omnifunc else ''
    self.changedtick = 1
    self.options = {
     'mod': modified,
     'bh': bufhidden
    }
    self.visual_start = visual_start
    self.visual_end = visual_end


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


  def mark( self, name ):
    if name == '<':
      return self.visual_start
    if name == '>':
      return self.visual_end
    raise ValueError( 'Unexpected mark: {name}'.format( name = name ) )


class VimBuffers( object ):
  """An object that looks like a vim.buffers object."""

  def __init__( self, buffers ):
    """|buffers| is a list of VimBuffer objects."""
    self._buffers = buffers


  def __getitem__( self, number ):
    """Emulates vim.buffers[ number ]"""
    for buffer_object in self._buffers:
      if number == buffer_object.number:
        return buffer_object
    raise KeyError( number )


  def __iter__( self ):
    """Emulates for loop on vim.buffers"""
    return iter( self._buffers )


  def pop( self, index ):
    return self._buffers.pop( index )


class VimWindow( object ):
  """An object that looks like a vim.window object:
    - |number|: number of the window;
    - |buffer_object|: a VimBuffer object representing the buffer inside the
      window;
    - |cursor|: a tuple corresponding to the cursor position."""

  def __init__( self, number, buffer_object, cursor = None ):
    self.number = number
    self.buffer = buffer_object
    self.cursor = cursor
    self.options = {}


class VimWindows( object ):
  """An object that looks like a vim.windows object."""

  def __init__( self, buffers, cursor ):
    """|buffers| is a list of VimBuffer objects corresponding to the window
    layout. The first element of that list is assumed to be the current window.
    |cursor| is the cursor position of that window."""
    windows = []
    windows.append( VimWindow( 1, buffers[ 0 ], cursor ) )
    for window_number in range( 1, len( buffers ) ):
      windows.append( VimWindow( window_number + 1, buffers[ window_number ] ) )
    self._windows = windows


  def __getitem__( self, number ):
    """Emulates vim.windows[ number ]"""
    for window in self._windows:
      if number == window.number:
        return window
    raise KeyError( number )


  def __iter__( self ):
    """Emulates for loop on vim.windows"""
    return iter( self._windows )


class VimCurrent( object ):
  """An object that looks like a vim.current object. |current_window| must be a
  VimWindow object."""

  def __init__( self, current_window ):
    self.buffer = current_window.buffer
    self.window = current_window
    self.line = self.buffer.contents[ current_window.cursor[ 0 ] - 1 ]


class VimMatch( object ):

  def __init__( self, group, pattern ):
    current_window = VIM_MOCK.current.window.number
    self.id = len( VIM_MATCHES_FOR_WINDOW[ current_window ] ) + 1
    self.group = group
    self.pattern = pattern


  def __eq__( self, other ):
    return self.group == other.group and self.pattern == other.pattern


  def __repr__( self ):
    return "VimMatch( group = '{0}', pattern = '{1}' )".format( self.group,
                                                                self.pattern )


  def __getitem__( self, key ):
    if key == 'group':
      return self.group
    elif key == 'id':
      return self.id


class VimSign( object ):

  def __init__( self, sign_id, line, name, bufnr ):
    self.id = sign_id
    self.line = line
    self.name = name
    self.bufnr = bufnr


  def __eq__( self, other ):
    return ( self.id == other.id and
             self.line == other.line and
             self.name == other.name and
             self.bufnr == other.bufnr )


  def __repr__( self ):
    return ( "VimSign( id = {0}, line = {1}, "
                      "name = '{2}', bufnr = {3} )".format( self.id,
                                                            self.line,
                                                            self.name,
                                                            self.bufnr ) )


  def __getitem__( self, key ):
    if key == 'group':
      return self.group
    elif key == 'id':
      return self.id


@contextlib.contextmanager
def MockVimBuffers( buffers, window_buffers, cursor_position = ( 1, 1 ) ):
  """Simulates the Vim buffers list |buffers| where |current_buffer| is the
  buffer displayed in the current window and |cursor_position| is the current
  cursor position. All buffers are represented by a VimBuffer object."""
  if ( not isinstance( buffers, list ) or
       not all( isinstance( buf, VimBuffer ) for buf in buffers ) ):
    raise RuntimeError( 'First parameter must be a list of VimBuffer objects.' )
  if ( not isinstance( window_buffers, list ) or
       not all( isinstance( buf, VimBuffer ) for buf in window_buffers ) ):
    raise RuntimeError( 'Second parameter must be a list of VimBuffer objects '
                        'representing the window layout.' )
  if len( window_buffers ) < 1:
    raise RuntimeError( 'Second parameter must contain at least one element '
                        'which corresponds to the current window.' )

  with patch( 'vim.buffers', VimBuffers( buffers ) ):
    with patch( 'vim.windows', VimWindows( window_buffers,
                                           cursor_position ) ) as windows:
      with patch( 'vim.current', VimCurrent( windows[ 1 ] ) ):
        yield VIM_MOCK


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

  VIM_MOCK.command = MagicMock( side_effect = _MockVimCommand )
  VIM_MOCK.eval = MagicMock( side_effect = _MockVimEval )
  VIM_MOCK.error = VimError
  sys.modules[ 'vim' ] = VIM_MOCK

  return VIM_MOCK


class VimError( Exception ):

  def __init__( self, code ):
    self.code = code


  def __str__( self ):
    return repr( self.code )


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


def ToBytesOnPY2( data ):
  # To test the omnifunc, etc. returning strings, which can be of different
  # types depending on python version, we use ToBytes on PY2 and just the native
  # str on python3. This roughly matches what happens between py2 and py3
  # versions within Vim.
  if not PY2:
    return data

  if isinstance( data, list ):
    return [ ToBytesOnPY2( item ) for item in data ]
  if isinstance( data, dict ):
    for item in data:
      data[ item ] = ToBytesOnPY2( data[ item ] )
    return data
  return ToBytes( data )

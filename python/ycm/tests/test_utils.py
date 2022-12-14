# Copyright (C) 2011-2019 YouCompleteMe contributors
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

from collections import defaultdict, namedtuple
from unittest.mock import DEFAULT, MagicMock, patch
from unittest import skip
from hamcrest import ( assert_that,
                       contains_exactly,
                       contains_inanyorder,
                       equal_to )
import contextlib
import functools
import json
import os
import re
import sys

from unittest import skipIf

from ycmd.utils import GetCurrentDirectory, OnMac, OnWindows, ToUnicode


BUFNR_REGEX = re.compile(
  '^bufnr\\(\'(?P<buffer_filename>.+)\'(, ([01]))?\\)$' )
BUFWINNR_REGEX = re.compile( '^bufwinnr\\((?P<buffer_number>[0-9]+)\\)$' )
BWIPEOUT_REGEX = re.compile(
  '^(?:silent! )bwipeout!? (?P<buffer_number>[0-9]+)$' )
GETBUFVAR_REGEX = re.compile(
  '^getbufvar\\((?P<buffer_number>[0-9]+), "(?P<option>.+)"\\)( \\?\\? 0)?$' )
PROP_ADD_REGEX = re.compile(
        '^prop_add\\( '            # A literal at the start
        '(?P<start_line>\\d+), '   # First argument - number
        '(?P<start_column>\\d+), ' # Second argument - number
        '{(?P<opts>.+)} '          # Third argument is a complex dict, which
                                   # we parse separately
        '\\)$' )
PROP_REMOVE_REGEX = re.compile( '^prop_remove\\( (?P<prop>.+) \\)$' )
OMNIFUNC_REGEX_FORMAT = (
  '^{omnifunc_name}\\((?P<findstart>[01]),[\'"](?P<base>.*)[\'"]\\)$' )
FNAMEESCAPE_REGEX = re.compile( '^fnameescape\\(\'(?P<filepath>.+)\'\\)$' )
STRDISPLAYWIDTH_REGEX = re.compile(
  '^strdisplaywidth\\( ?\'(?P<text>.+)\' ?\\)$' )
REDIR_START_REGEX = re.compile( '^redir => (?P<variable>[\\w:]+)$' )
REDIR_END_REGEX = re.compile( '^redir END$' )
EXISTS_REGEX = re.compile( '^exists\\( \'(?P<option>[\\w:]+)\' \\)$' )
LET_REGEX = re.compile( '^let (?P<option>[\\w:]+) = (?P<value>.*)$' )
HAS_PATCH_REGEX = re.compile( '^has\\( \'patch(?P<patch>\\d+)\' \\)$' )

# One-and only instance of mocked Vim object. The first 'import vim' that is
# executed binds the vim module to the instance of MagicMock that is created,
# and subsquent assignments to sys.modules[ 'vim' ] don't retrospectively
# update them. The result is that while running the tests, we must assign only
# one instance of MagicMock to sys.modules[ 'vim' ] and always return it.
#
# More explanation is available:
# https://github.com/Valloric/YouCompleteMe/pull/1694
VIM_MOCK = MagicMock()

VIM_PROPS_FOR_BUFFER = defaultdict( list )
VIM_SIGNS = []

VIM_OPTIONS = {
  '&completeopt': b'',
  '&previewheight': 12,
  '&columns': 80,
  '&ruler': 0,
  '&showcmd': 1,
  '&hidden': 0,
  '&expandtab': 1
}

Version = namedtuple( 'Version', [ 'major', 'minor', 'patch' ] )

# This variable must be patched with a Version object for tests depending on a
# recent Vim version. Example:
#
#   @patch( 'ycm.tests.test_utils.VIM_VERSION', Version( 8, 1, 614 ) )
#   def ThisTestDependsOnTheVimVersion_test():
#     ...
#
# Default is the oldest supported version.
VIM_VERSION = Version( 7, 4, 1578 )

REDIR = {
  'status': False,
  'variable': '',
  'output': ''
}

WindowsAndMacOnly = skipIf( not OnWindows() or not OnMac(),
                            'Windows and macOS only' )


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
    return current_buffer.omnifunc( findstart, base )

  return None


def _MockVimWindowEval( value ):
  if value == 'winnr("#")':
    # For simplicity, we always assume there is no previous window.
    return 0

  return None


def _MockVimOptionsEval( value ):
  result = VIM_OPTIONS.get( value )
  if result is not None:
    return result

  if value == 'keys( g: )':
    global_options = {}
    for key, value in VIM_OPTIONS.items():
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

  if value.startswith( 'has( "' ):
    return False

  match = re.match( 'sign_getplaced\\( (?P<bufnr>\\d+), '
                    '{ "group": "ycm_signs" } \\)', value )
  if match:
    filtered = list( filter( lambda sign: sign.bufnr ==
                                          int( match.group( 'bufnr' ) ),
                             VIM_SIGNS ) )
    r = [ { 'signs': filtered } ]
    return r

  match = re.match( 'sign_unplacelist\\( (?P<sign_list>\\[.*\\]) \\)', value )
  if match:
    sign_list = eval( match.group( 'sign_list' ) )
    for sign in sign_list:
      VIM_SIGNS.remove( sign )
    return True # Why True?

  match = re.match( 'sign_placelist\\( (?P<sign_list>\\[.*\\]) \\)', value )
  if match:
    sign_list = json.loads( match.group( 'sign_list' ).replace( "'", '"' ) )
    for sign in sign_list:
      VIM_SIGNS.append( VimSign( sign[ 'lnum' ],
                                 sign[ 'name' ],
                                 sign[ 'buffer' ] ) )
    return True # Why True?

  return None


def _MockVimPropEval( value ):
  match = re.match( 'prop_list\\( (?P<lnum>\\d+), '
                    '{ "bufnr": (?P<bufnr>\\d+) } \\)', value )
  if match:
    return [ p for p in VIM_PROPS_FOR_BUFFER[ int( match.group( 'bufnr' ) ) ]
             if p.start_line == int( match.group( 'lnum' ) ) ]

  match = PROP_ADD_REGEX.search( value )
  if match:
    prop_start_line = int( match.group( 'start_line' ) )
    prop_start_column = int( match.group( 'start_column' ) )
    import ast
    opts = ast.literal_eval( '{' + match.group( 'opts' ) + '}' )
    vim_prop = VimProp(
        opts[ 'type' ],
        prop_start_line,
        prop_start_column,
        int( opts[ 'end_lnum' ] ) if opts[ 'end_lnum' ] else prop_start_line,
        int( opts[ 'end_col' ] ) if opts[ 'end_col' ] else prop_start_column
    )
    VIM_PROPS_FOR_BUFFER[ int( opts[ 'bufnr' ] ) ].append( vim_prop )
    return vim_prop.id

  match = PROP_REMOVE_REGEX.search( value )
  if match:
    prop, lin_num = eval( match.group( 'prop' ) )
    vim_props = VIM_PROPS_FOR_BUFFER[ prop[ 'bufnr' ] ]
    for index, vim_prop in enumerate( vim_props ):
      if vim_prop.id == prop[ 'id' ]:
        vim_props.pop( index )
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


def _MockVimEval( value ): # noqa
  if value == 'g:ycm_neovim_ns_id':
    return 1

  result = _MockVimOptionsEval( value )
  if result is not None:
    return result

  result = _MockVimFunctionsEval( value )
  if result is not None:
    return result

  result = _MockVimBufferEval( value )
  if result is not None:
    return result

  result = _MockVimWindowEval( value )
  if result is not None:
    return result

  result = _MockVimPropEval( value )
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

  match = STRDISPLAYWIDTH_REGEX.search( value )
  if match:
    return len( match.group( 'text' ) )

  raise VimError( f'Unexpected evaluation: { value }' )


def _MockWipeoutBuffer( buffer_number ):
  buffers = VIM_MOCK.buffers

  for index, buffer in enumerate( buffers ):
    if buffer.number == buffer_number:
      return buffers.pop( index )


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

  match = LET_REGEX.search( command )
  if match:
    option = match.group( 'option' )
    value = json.loads( match.group( 'value' ) )
    VIM_OPTIONS[ option ] = value
    return

  return DEFAULT


def _MockVimOptions( option ):
  result = VIM_OPTIONS.get( '&' + option )
  if result is not None:
    return result

  return None


class VimBuffer:
  """An object that looks like a vim.buffer object:
   - |name|     : full path of the buffer with symbolic links resolved;
   - |number|   : buffer number;
   - |contents| : list of lines representing the buffer contents;
   - |filetype| : buffer filetype. Empty string if no filetype is set;
   - |modified| : True if the buffer has unsaved changes, False otherwise;
   - |bufhidden|: value of the 'bufhidden' option (see :h bufhidden);
   - |vars|:      dict for buffer-local variables
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
                      visual_end = None,
                      vars = {} ):
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
    self.vars = vars # should really be a vim-specific dict-like obj


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
    raise ValueError( f'Unexpected mark: { name }' )


  def __repr__( self ):
    return f"VimBuffer( name = '{ self.name }', number = { self.number } )"


class VimBuffers:
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


class VimWindow:
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
    self.vars = {}


  def __repr__( self ):
    return ( f'VimWindow( number = { self.number }, '
                        f'buffer = { self.buffer }, '
                        f'cursor = { self.cursor } )' )


class VimWindows:
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
    try:
      return self._windows[ number ]
    except IndexError:
      raise IndexError( 'no such window' )


  def __iter__( self ):
    """Emulates for loop on vim.windows"""
    return iter( self._windows )


class VimCurrent:
  """An object that looks like a vim.current object. |current_window| must be a
  VimWindow object."""

  def __init__( self, current_window ):
    self.buffer = current_window.buffer
    self.window = current_window
    self.line = self.buffer.contents[ current_window.cursor[ 0 ] - 1 ]


class VimProp:

  def __init__( self,
                prop_type,
                start_line,
                start_column,
                end_line = None,
                end_column = None ):
    current_buffer = VIM_MOCK.current.buffer.number
    self.id = len( VIM_PROPS_FOR_BUFFER[ current_buffer ] ) + 1
    self.prop_type = prop_type
    self.start_line = start_line
    self.start_column = start_column
    self.end_line = end_line if end_line else start_line
    self.end_column = end_column if end_column else start_column


  def __eq__( self, other ):
    return ( self.prop_type == other.prop_type and
             self.start_line == other.start_line and
             self.start_column == other.start_column and
             self.end_line == other.end_line and
             self.end_column == other.end_column )


  def __repr__( self ):
    return ( f"VimProp( prop_type = '{ self.prop_type }',"
             f" start_line = { self.start_line }, "
             f" start_column = { self.start_column },"
             f" end_line = { self.end_line },"
             f" end_column = { self.end_column } )" )


  def __getitem__( self, key ):
    if key == 'type':
      return self.prop_type
    elif key == 'id':
      return self.id
    elif key == 'col':
      return self.start_column
    elif key == 'length':
      return self.end_column - self.start_column


  def get( self, key, default = None ):
    if key == 'type':
      return self.prop_type


class VimSign:

  def __init__( self, line, name, bufnr ):
    self.line = line
    self.name = name
    self.bufnr = bufnr


  def __eq__( self, other ):
    if isinstance( other, dict ):
      other = VimSign( other[ 'lnum' ], other[ 'name' ], other[ 'buffer' ] )
    return ( self.line == other.line and
             self.name == other.name and
             self.bufnr == other.bufnr )


  def __repr__( self ):
    return ( f"VimSign( line = { self.line }, "
                      f"name = '{ self.name }', bufnr = { self.bufnr } )" )


  def __getitem__( self, key ):
    if key == 'group':
      return self.group


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
      with patch( 'vim.current', VimCurrent( windows[ 0 ] ) ):
        yield VIM_MOCK


def MockVimModule():
  """The 'vim' module is something that is only present when running inside the
  Vim Python interpreter, so we replace it with a MagicMock for tests. If you
  need to add additional mocks to vim module functions, then use 'patch' from
  mock module, to ensure that the state of the vim mock is returned before the
  next test. That is:

    from ycm.tests.test_utils import MockVimModule
    from unittest.mock import patch

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
  VIM_MOCK.options = MagicMock()
  VIM_MOCK.options.__getitem__.side_effect = _MockVimOptions
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
    contains = contains_inanyorder if any_order else contains_exactly
    assert_that( self.call_args_list, contains( *calls ) )
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
        skip( reason )
      else:
        raise AssertionError( f'Test was expected to fail: { reason }' )
    return Wrapper

  return decorator

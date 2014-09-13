#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Google Inc.
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

import vim
import os
import tempfile
import json
from ycmd.utils import ToUtf8IfNeeded
from ycmd import user_options_store

BUFFER_COMMAND_MAP = { 'same-buffer'      : 'edit',
                       'horizontal-split' : 'split',
                       'vertical-split'   : 'vsplit',
                       'new-tab'          : 'tabedit' }

def CurrentLineAndColumn():
  """Returns the 0-based current line and 0-based current column."""
  # See the comment in CurrentColumn about the calculation for the line and
  # column number
  line, column = vim.current.window.cursor
  line -= 1
  return line, column


def CurrentColumn():
  """Returns the 0-based current column. Do NOT access the CurrentColumn in
  vim.current.line. It doesn't exist yet when the cursor is at the end of the
  line. Only the chars before the current column exist in vim.current.line."""

  # vim's columns are 1-based while vim.current.line columns are 0-based
  # ... but vim.current.window.cursor (which returns a (line, column) tuple)
  # columns are 0-based, while the line from that same tuple is 1-based.
  # vim.buffers buffer objects OTOH have 0-based lines and columns.
  # Pigs have wings and I'm a loopy purple duck. Everything makes sense now.
  return vim.current.window.cursor[ 1 ]


def CurrentLineContents():
  return vim.current.line


def TextAfterCursor():
  """Returns the text after CurrentColumn."""
  return vim.current.line[ CurrentColumn(): ]


# Expects version_string in 'MAJOR.MINOR.PATCH' format, e.g. '7.4.301'
def VimVersionAtLeast( version_string ):
  major, minor, patch = [ int( x ) for x in version_string.split( '.' ) ]

  # For Vim 7.4.301, v:version is '704'
  actual_major_and_minor = GetIntValue( 'v:version' )
  if actual_major_and_minor != major * 100 + minor:
    return False

  return GetBoolValue( 'has("patch{0}")'.format( patch ) )


# Note the difference between buffer OPTIONS and VARIABLES; the two are not
# the same.
def GetBufferOption( buffer_object, option ):
  # NOTE: We used to check for the 'options' property on the buffer_object which
  # is available in recent versions of Vim and would then use:
  #
  #   buffer_object.options[ option ]
  #
  # to read the value, BUT this caused annoying flickering when the
  # buffer_object was a hidden buffer (with option = 'ft'). This was all due to
  # a Vim bug. Until this is fixed, we won't use it.

  to_eval = 'getbufvar({0}, "&{1}")'.format( buffer_object.number, option )
  return GetVariableValue( to_eval )


def BufferModified( buffer_object ):
  return bool( int( GetBufferOption( buffer_object, 'mod' ) ) )


def GetUnsavedAndCurrentBufferData():
  buffers_data = {}
  for buffer_object in vim.buffers:
    if not ( BufferModified( buffer_object ) or
             buffer_object == vim.current.buffer ):
      continue

    buffers_data[ GetBufferFilepath( buffer_object ) ] = {
      'contents': '\n'.join( buffer_object ),
      'filetypes': FiletypesForBuffer( buffer_object )
    }

  return buffers_data


def GetBufferNumberForFilename( filename, open_file_if_needed = True ):
  return GetIntValue( u"bufnr('{0}', {1})".format(
      EscapeForVim( os.path.realpath( filename ) ),
      int( open_file_if_needed ) ) )


def GetCurrentBufferFilepath():
  return GetBufferFilepath( vim.current.buffer )


def BufferIsVisible( buffer_number ):
  if buffer_number < 0:
    return False
  window_number = GetIntValue( "bufwinnr({0})".format( buffer_number ) )
  return window_number != -1


def GetBufferFilepath( buffer_object ):
  if buffer_object.name:
    return buffer_object.name
  # Buffers that have just been created by a command like :enew don't have any
  # buffer name so we use the buffer number for that. Also, os.getcwd() throws
  # an exception when the CWD has been deleted so we handle that.
  try:
    folder_path = os.getcwd()
  except OSError:
    folder_path = tempfile.gettempdir()
  return os.path.join( folder_path, str( buffer_object.number ) )


def UnplaceSignInBuffer( buffer_number, sign_id ):
  if buffer_number < 0:
    return
  vim.command(
    'try | exec "sign unplace {0} buffer={1}" | catch /E158/ | endtry'.format(
        sign_id, buffer_number ) )


def PlaceSign( sign_id, line_num, buffer_num, is_error = True ):
  # libclang can give us diagnostics that point "outside" the file; Vim borks
  # on these.
  if line_num < 1:
    line_num = 1

  sign_name = 'YcmError' if is_error else 'YcmWarning'
  vim.command( 'sign place {0} line={1} name={2} buffer={3}'.format(
    sign_id, line_num, sign_name, buffer_num ) )


def PlaceDummySign( sign_id, buffer_num, line_num ):
    if buffer_num < 0 or line_num < 0:
      return
    vim.command( 'sign define ycm_dummy_sign' )
    vim.command(
      'sign place {0} name=ycm_dummy_sign line={1} buffer={2}'.format(
        sign_id,
        line_num,
        buffer_num,
      )
    )


def UnPlaceDummySign( sign_id, buffer_num ):
    if buffer_num < 0:
      return
    vim.command( 'sign undefine ycm_dummy_sign' )
    vim.command( 'sign unplace {0} buffer={1}'.format( sign_id, buffer_num ) )


def ClearYcmSyntaxMatches():
  matches = VimExpressionToPythonType( 'getmatches()' )
  for match in matches:
    if match[ 'group' ].startswith( 'Ycm' ):
      vim.eval( 'matchdelete({0})'.format( match[ 'id' ] ) )


# Returns the ID of the newly added match
# Both line and column numbers are 1-based
def AddDiagnosticSyntaxMatch( line_num,
                              column_num,
                              line_end_num = None,
                              column_end_num = None,
                              is_error = True ):
  group = 'YcmErrorSection' if is_error else 'YcmWarningSection'

  if not line_end_num:
    line_end_num = line_num

  line_num, column_num = LineAndColumnNumbersClamped( line_num, column_num )
  line_end_num, column_end_num = LineAndColumnNumbersClamped( line_end_num,
                                                              column_end_num )

  if not column_end_num:
    return GetIntValue(
      "matchadd('{0}', '\%{1}l\%{2}c')".format( group, line_num, column_num ) )
  else:
    return GetIntValue(
      "matchadd('{0}', '\%{1}l\%{2}c\_.\\{{-}}\%{3}l\%{4}c')".format(
        group, line_num, column_num, line_end_num, column_end_num ) )


# Clamps the line and column numbers so that they are not past the contents of
# the buffer. Numbers are 1-based.
def LineAndColumnNumbersClamped( line_num, column_num ):
  new_line_num = line_num
  new_column_num = column_num

  max_line = len( vim.current.buffer )
  if line_num and line_num > max_line:
    new_line_num = max_line

  max_column = len( vim.current.buffer[ new_line_num - 1 ] )
  if column_num and column_num > max_column:
    new_column_num = max_column

  return new_line_num, new_column_num


def SetLocationList( diagnostics ):
  """Diagnostics should be in qflist format; see ":h setqflist" for details."""
  vim.eval( 'setloclist( 0, {0} )'.format( json.dumps( diagnostics ) ) )


def ConvertDiagnosticsToQfList( diagnostics ):
  def ConvertDiagnosticToQfFormat( diagnostic ):
    # see :h getqflist for a description of the dictionary fields
    # Note that, as usual, Vim is completely inconsistent about whether
    # line/column numbers are 1 or 0 based in its various APIs. Here, it wants
    # them to be 1-based.
    location = diagnostic[ 'location' ]
    line_num = location[ 'line_num' ]

    # libclang can give us diagnostics that point "outside" the file; Vim borks
    # on these.
    if line_num < 1:
      line_num = 1

    return {
      'bufnr' : GetBufferNumberForFilename( location[ 'filepath' ] ),
      'lnum'  : line_num,
      'col'   : location[ 'column_num' ],
      'text'  : ToUtf8IfNeeded( diagnostic[ 'text' ] ),
      'type'  : diagnostic[ 'kind' ][ 0 ],
      'valid' : 1
    }

  return [ ConvertDiagnosticToQfFormat( x ) for x in diagnostics ]


# Given a dict like {'a': 1}, loads it into Vim as if you ran 'let g:a = 1'
# When |overwrite| is True, overwrites the existing value in Vim.
def LoadDictIntoVimGlobals( new_globals, overwrite = True ):
  extend_option = '"force"' if overwrite else '"keep"'

  # We need to use json.dumps because that won't use the 'u' prefix on strings
  # which Vim would bork on.
  vim.eval( 'extend( g:, {0}, {1})'.format( json.dumps( new_globals ),
                                            extend_option ) )


# Changing the returned dict will NOT change the value in Vim.
def GetReadOnlyVimGlobals( force_python_objects = False ):
  if force_python_objects:
    return vim.eval( 'g:' )

  try:
    # vim.vars is fairly new so it might not exist
    return vim.vars
  except:
    return vim.eval( 'g:' )


def VimExpressionToPythonType( vim_expression ):
  result = vim.eval( vim_expression )
  if not isinstance( result, basestring ):
    return result
  try:
    return int( result )
  except ValueError:
    return result


def HiddenEnabled( buffer_object ):
  return bool( int( GetBufferOption( buffer_object, 'hid' ) ) )


def BufferIsUsable( buffer_object ):
  return not BufferModified( buffer_object ) or HiddenEnabled( buffer_object )


def EscapedFilepath( filepath ):
  return filepath.replace( ' ' , r'\ ' )


# Both |line| and |column| need to be 1-based
def JumpToLocation( filename, line, column ):
  # Add an entry to the jumplist
  vim.command( "normal! m'" )

  if filename != GetCurrentBufferFilepath():
    # We prefix the command with 'keepjumps' so that opening the file is not
    # recorded in the jumplist. So when we open the file and move the cursor to
    # a location in it, the user can use CTRL-O to jump back to the original
    # location, not to the start of the newly opened file.
    # Sadly this fails on random occasions and the undesired jump remains in the
    # jumplist.
    user_command = user_options_store.Value( 'goto_buffer_command' )
    command = BUFFER_COMMAND_MAP.get( user_command, 'edit' )
    if command == 'edit' and not BufferIsUsable( vim.current.buffer ):
      command = 'split'
    vim.command( 'keepjumps {0} {1}'.format( command,
                                             EscapedFilepath( filename ) ) )
  vim.current.window.cursor = ( line, column - 1 )

  # Center the screen on the jumped-to location
  vim.command( 'normal! zz' )


def NumLinesInBuffer( buffer_object ):
  # This is actually less than obvious, that's why it's wrapped in a function
  return len( buffer_object )


# Calling this function from the non-GUI thread will sometimes crash Vim. At the
# time of writing, YCM only uses the GUI thread inside Vim (this used to not be
# the case).
def PostVimMessage( message ):
  vim.command( "echohl WarningMsg | echom '{0}' | echohl None"
               .format( EscapeForVim( str( message ) ) ) )


# Unlike PostVimMesasge, this supports messages with newlines in them because it
# uses 'echo' instead of 'echomsg'. This also means that the message will NOT
# appear in Vim's message log.
def PostMultiLineNotice( message ):
  vim.command( "echohl WarningMsg | echo '{0}' | echohl None"
               .format( EscapeForVim( str( message ) ) ) )


def PresentDialog( message, choices, default_choice_index = 0 ):
  """Presents the user with a dialog where a choice can be made.
  This will be a dialog for gvim users or a question in the message buffer
  for vim users or if `set guioptions+=c` was used.

  choices is list of alternatives.
  default_choice_index is the 0-based index of the default element
  that will get choosen if the user hits <CR>. Use -1 for no default.

  PresentDialog will return a 0-based index into the list
  or -1 if the dialog was dismissed by using <Esc>, Ctrl-C, etc.

  See also:
    :help confirm() in vim (Note that vim uses 1-based indexes)

  Example call:
    PresentDialog("Is this a nice example?", ["Yes", "No", "May&be"])
      Is this a nice example?
      [Y]es, (N)o, May(b)e:"""
  to_eval = "confirm('{0}', '{1}', {2})".format( EscapeForVim( message ),
    EscapeForVim( "\n" .join( choices ) ), default_choice_index + 1 )
  return int( vim.eval( to_eval ) ) - 1


def Confirm( message ):
  return bool( PresentDialog( message, [ "Ok", "Cancel" ] ) == 0 )


def EchoText( text, log_as_message = True ):
  def EchoLine( text ):
    command = 'echom' if log_as_message else 'echo'
    vim.command( "{0} '{1}'".format( command, EscapeForVim( text ) ) )

  for line in str( text ).split( '\n' ):
    EchoLine( line )


# Echos text but truncates it so that it all fits on one line
def EchoTextVimWidth( text ):
  vim_width = GetIntValue( '&columns' )
  truncated_text = ToUtf8IfNeeded( text )[ : int( vim_width * 0.9 ) ]
  truncated_text.replace( '\n', ' ' )

  old_ruler = GetIntValue( '&ruler' )
  old_showcmd = GetIntValue( '&showcmd' )
  vim.command( 'set noruler noshowcmd' )

  EchoText( truncated_text, False )

  vim.command( 'let &ruler = {0}'.format( old_ruler ) )
  vim.command( 'let &showcmd = {0}'.format( old_showcmd ) )


def EscapeForVim( text ):
  return text.replace( "'", "''" )


def CurrentFiletypes():
  return vim.eval( "&filetype" ).split( '.' )


def FiletypesForBuffer( buffer_object ):
  # NOTE: Getting &ft for other buffers only works when the buffer has been
  # visited by the user at least once, which is true for modified buffers
  return GetBufferOption( buffer_object, 'ft' ).split( '.' )


def GetVariableValue( variable ):
  return vim.eval( variable )


def GetBoolValue( variable ):
  return bool( int( vim.eval( variable ) ) )


def GetIntValue( variable ):
  return int( vim.eval( variable ) )


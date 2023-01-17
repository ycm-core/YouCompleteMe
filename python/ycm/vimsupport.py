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

import vim
import os
import json
import re
from collections import defaultdict, namedtuple
from functools import lru_cache as memoize
from ycmd.utils import ( ByteOffsetToCodepointOffset,
                         GetCurrentDirectory,
                         JoinLinesAsUnicode,
                         OnMac,
                         OnWindows,
                         ToBytes,
                         ToUnicode )

BUFFER_COMMAND_MAP = { 'same-buffer'      : 'edit',
                       'split'            : 'split',
                       # These commands are obsolete. :vertical or :tab should
                       # be used with the 'split' command instead.
                       'horizontal-split' : 'split',
                       'vertical-split'   : 'vsplit',
                       'new-tab'          : 'tabedit' }

FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT = (
    'The requested operation will apply changes to {0} files which are not '
    'currently open. This will therefore open {0} new files in the hidden '
    'buffers. The quickfix list can then be used to review the changes. No '
    'files will be written to disk. Do you wish to continue?' )

NO_SELECTION_MADE_MSG = "No valid selection was made; aborting."

# When we're in a buffer without a file name associated with it, we need to
# invent a file name. We do so by the means of $CWD/$BUFNR.
# However, that causes problems with diagnostics - we also need a way to map
# those same file names back to their originating buffer numbers.
MADEUP_FILENAME_TO_BUFFER_NUMBER = {}

NO_COMPLETIONS = {
  'line': -1,
  'column': -1,
  'completion_start_column': -1,
  'completions': []
}

YCM_NEOVIM_NS_ID = vim.eval( 'g:ycm_neovim_ns_id' )

# Virtual text is not a feature in itself and early patches don't work well, so
# we need to keep changing this at the moment
VIM_VIRTUAL_TEXT_VERSION_REQ = '9.0.214'


def CurrentLineAndColumn():
  """Returns the 0-based current line and 0-based current column."""
  # See the comment in CurrentColumn about the calculation for the line and
  # column number
  line, column = vim.current.window.cursor
  line -= 1
  return line, column


def SetCurrentLineAndColumn( line, column ):
  """Sets the cursor position to the 0-based line and 0-based column."""
  # Line from vim.current.window.cursor is 1-based.
  vim.current.window.cursor = ( line + 1, column )


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
  return ToUnicode( vim.current.line )


def CurrentLineContentsAndCodepointColumn():
  """Returns the line contents as a unicode string and the 0-based current
  column as a codepoint offset. If the current column is outside the line,
  returns the column position at the end of the line."""
  line = CurrentLineContents()
  byte_column = CurrentColumn()
  # ByteOffsetToCodepointOffset expects 1-based offset.
  column = ByteOffsetToCodepointOffset( line, byte_column + 1 ) - 1
  return line, column


def TextAfterCursor():
  """Returns the text after CurrentColumn."""
  return ToUnicode( vim.current.line[ CurrentColumn(): ] )


def TextBeforeCursor():
  """Returns the text before CurrentColumn."""
  return ToUnicode( vim.current.line[ :CurrentColumn() ] )


def BufferModified( buffer_object ):
  return buffer_object.options[ 'mod' ]


def GetBufferData( buffer_object ):
  return {
    # Add a newline to match what gets saved to disk. See #1455 for details.
    'contents': JoinLinesAsUnicode( buffer_object ) + '\n',
    'filetypes': FiletypesForBuffer( buffer_object )
  }


def GetUnsavedAndSpecifiedBufferData( included_buffer, included_filepath ):
  """Build part of the request containing the contents and filetypes of all
  dirty buffers as well as the buffer |included_buffer| with its filepath
  |included_filepath|."""
  buffers_data = { included_filepath: GetBufferData( included_buffer ) }

  for buffer_object in vim.buffers:
    if not BufferModified( buffer_object ):
      continue

    filepath = GetBufferFilepath( buffer_object )
    if filepath in buffers_data:
      continue

    buffers_data[ filepath ] = GetBufferData( buffer_object )

  return buffers_data


def GetBufferNumberForFilename( filename, create_buffer_if_needed = False ):
  realpath = os.path.realpath( filename )
  return MADEUP_FILENAME_TO_BUFFER_NUMBER.get( realpath, GetIntValue(
      f"bufnr('{ EscapeForVim( realpath ) }', "
             f"{ int( create_buffer_if_needed ) })" ) )


def GetCurrentBufferFilepath():
  return GetBufferFilepath( vim.current.buffer )


def BufferIsVisible( buffer_number ):
  if buffer_number < 0:
    return False
  window_number = GetIntValue( f"bufwinnr({ buffer_number })" )
  return window_number != -1


def GetBufferFilepath( buffer_object ):
  if buffer_object.name:
    return os.path.abspath( ToUnicode( buffer_object.name ) )
  # Buffers that have just been created by a command like :enew don't have any
  # buffer name so we use the buffer number for that.
  name = os.path.join( GetCurrentDirectory(), str( buffer_object.number ) )
  MADEUP_FILENAME_TO_BUFFER_NUMBER[ name ] = buffer_object.number
  return name


def GetCurrentBufferNumber():
  return vim.current.buffer.number


def GetBufferChangedTick( bufnr ):
  return GetIntValue( f'getbufvar({ bufnr }, "changedtick")' or 0 )


# Returns a range covering the earliest and latest lines visible in the current
# tab page for the supplied buffer number. By default this range is then
# extended by half of the resulting range size
def RangeVisibleInBuffer( bufnr, grow_factor=0.5 ):
  windows = [ w for w in vim.eval( f'win_findbuf( { bufnr } )' )
              if GetIntValue( vim.eval( f'win_id2tabwin( { w } )[ 0 ]' ) ) ==
                vim.current.tabpage.number ]

  class Location:
    line: int = None
    col: int = None

  class Range:
    start: Location = Location()
    end: Location = Location()

  buffer = vim.buffers[ bufnr ]

  if not windows:
    return None

  r = Range()
  # Note, for this we ignore horizontal scrolling
  for winid in windows:
    win_info = vim.eval( f'getwininfo( { winid } )[ 0 ]' )
    if r.start.line is None or r.start.line > int( win_info[ 'topline' ] ):
      r.start.line = int( win_info[ 'topline' ] )
    if r.end.line is None or r.end.line < int( win_info[ 'botline' ] ):
      r.end.line = int( win_info[ 'botline' ] )

  # Extend the range by 1 factor, and calculate the columns
  num_lines = r.end.line - r.start.line + 1
  r.start.line = max( r.start.line - int( num_lines * grow_factor ), 1 )
  r.start.col = 1
  r.end.line = min( r.end.line + int( num_lines * grow_factor ), len( buffer ) )
  r.end.col = len( buffer[ r.end.line - 1 ] )

  filepath = GetBufferFilepath( buffer )
  return {
    'start': {
      'line_num': r.start.line,
      'column_num': r.start.col,
      'filepath': filepath,
    },
    'end': {
      'line_num': r.end.line,
      'column_num': r.end.col,
      'filepath': filepath,
    }
  }


def VisibleRangeOfBufferOverlaps( bufnr, expanded_range ):
  visible_range = RangeVisibleInBuffer( bufnr, 0 )
  # As above, we ignore horizontal scroll and only check lines
  return (
    expanded_range is not None and
    visible_range is not None and
    visible_range[ 'start' ][ 'line_num' ]
      >= expanded_range[ 'start' ][ 'line_num' ] and
    visible_range[ 'end' ][ 'line_num' ]
      <= expanded_range[ 'end' ][ 'line_num' ]
  )


def CaptureVimCommand( command ):
  vim.command( 'redir => b:ycm_command' )
  vim.command( f'silent! { command }' )
  vim.command( 'redir END' )
  output = ToUnicode( vim.eval( 'b:ycm_command' ) )
  vim.command( 'unlet b:ycm_command' )
  return output


def GetSignsInBuffer( buffer_number ):
  return vim.eval(
      f'sign_getplaced( { buffer_number }, {{ "group": "ycm_signs" }} )'
  )[ 0 ][ 'signs' ]


class DiagnosticProperty( namedtuple( 'DiagnosticProperty', [ 'id',
                                                              'type',
                                                              'line',
                                                              'column',
                                                              'length' ] ) ):
  def __eq__( self, other ):
    return ( self.type == other.type and
             self.line == other.line and
             self.column == other.column and
             self.length == other.length )


def GetTextPropertyForDiag( buffer_number, line_number, diag ):
  range = diag[ 'location_extent' ]
  start = range[ 'start' ]
  end = range[ 'end' ]
  length = end[ 'column_num' ] - start[ 'column_num' ]
  if diag[ 'kind' ] == 'ERROR':
    property_name = 'YcmErrorProperty'
  else:
    property_name = 'YcmWarningProperty'
  if HasFastPropList():
    vim_props = vim.eval( f'prop_list( { line_number }, '
                          f'{{ "bufnr": { buffer_number }, '
                             f'"types": [ "{ property_name }" ] }} )' )
    return next( filter(
        lambda p: start[ 'column_num' ] == int( p[ 'col' ] ) and
                  length == int( p[ 'length' ] ),
        vim_props ) )
  else:
    vim_props = vim.eval( f'prop_list( { line_number }, '
                                     f'{{ "bufnr": { buffer_number } }} )' )
    return next( filter(
        lambda p: start[ 'column_num' ] == int( p[ 'col' ] ) and
                  length == int( p[ 'length' ] ) and
                  property_name == p[ 'type' ],
        vim_props ) )


def GetTextProperties( buffer_number ):
  if not VimIsNeovim():
    if HasFastPropList():
      return [
        DiagnosticProperty(
            int( p[ 'id' ] ),
            p[ 'type' ],
            int( p[ 'lnum' ] ),
            int( p[ 'col' ] ),
            int( p[ 'length' ] ) )
        for p in vim.eval(
            f'prop_list( 1, '
                         f'{{ "bufnr": { buffer_number }, '
                             '"end_lnum": -1, '
                             '"types": [ "YcmErrorProperty", '
                                        '"YcmWarningProperty" ] } )' ) ]
    else:
      properties = []
      for line_number in range( len( vim.buffers[ buffer_number ] ) ):
        vim_props =  vim.eval( f'prop_list( {line_number + 1}, '
                               f'{{ "bufnr": { buffer_number } }} )' )
        properties.extend(
          DiagnosticProperty(
            int( p[ 'id' ] ),
            p[ 'type' ],
            line_number + 1,
            int( p[ 'col' ] ),
            int( p[ 'length' ] ) )
          for p in vim_props if p.get( 'type', '' ).startswith( 'Ycm' )
        )
      return properties
  else:
    ext_marks = vim.eval(
      f'nvim_buf_get_extmarks( { buffer_number }, '
                             f'{ YCM_NEOVIM_NS_ID }, '
                              '0, '
                              '-1, '
                              '{ "details": 1 } )' )
    return [ DiagnosticProperty(
               int( id ),
               extra_args[ 'hl_group' ],
               int( line ) + 1, # Neovim uses 0-based lines and columns
               int( column ) + 1,
               int( extra_args[ 'end_col' ] ) - int( column ) )
             for id, line, column, extra_args in ext_marks ]


def AddTextProperty( buffer_number,
                     line,
                     column,
                     prop_type,
                     extra_args ):
  if not VimIsNeovim():
    extra_args.update( {
      'type': prop_type,
      'bufnr': buffer_number
    } )
    return GetIntValue( f'prop_add( { line }, '
                                  f'{ column }, '
                                  f'{ json.dumps( extra_args ) } )' )
  else:
    extra_args[ 'hl_group' ] = prop_type
    # Neovim uses 0-based offsets
    if 'end_lnum' in extra_args:
      extra_args[ 'end_line' ] = extra_args.pop( 'end_lnum' ) - 1
    if 'end_col' in extra_args:
      extra_args[ 'end_col' ] = extra_args.pop( 'end_col' ) - 1
    line -= 1
    column -= 1
    return GetIntValue( f'nvim_buf_set_extmark( { buffer_number }, '
                                              f'{ YCM_NEOVIM_NS_ID }, '
                                              f'{ line }, '
                                              f'{ column }, '
                                              f'{ extra_args } )' )


def RemoveDiagnosticProperty( buffer_number: int, prop: DiagnosticProperty ):
  RemoveTextProperty( buffer_number,
                      prop.line,
                      prop.id,
                      prop.type )


def RemoveTextProperty( buffer_number, line_num, prop_id, prop_type ):
  if not VimIsNeovim():
    p = {
      'bufnr': buffer_number,
      'id': prop_id,
      'type': prop_type,
      'both': 1,
      'all': 1
    }
    vim.eval( f'prop_remove( { p }, { line_num } )' )
  else:
    vim.eval( f'nvim_buf_del_extmark( { buffer_number }, '
                                    f'{ YCM_NEOVIM_NS_ID }, '
                                    f'{ prop_id } )' )


# Clamps the line and column numbers so that they are not past the contents of
# the buffer. Numbers are 1-based byte offsets.
def LineAndColumnNumbersClamped( bufnr, line_num, column_num ):
  vim_buffer = vim.buffers[ bufnr ]
  line_num = max( min( line_num, len( vim_buffer ) ), 1 )
  # Vim buffers are lists Unicode objects on Python 3.
  max_column = len( ToBytes( vim_buffer[ line_num - 1 ] ) ) + 1

  return line_num, max( min( column_num, max_column ), 1 )


def SetLocationList( diagnostics ):
  """Set the location list for the current window to the supplied diagnostics"""
  SetLocationListForWindow( 0, diagnostics )


def GetWindowsForBufferNumber( buffer_number ):
  """Return the list of windows containing the buffer with number
  |buffer_number| for the current tab page."""
  return [ window for window in vim.windows
           if window.buffer.number == buffer_number ]


def SetLocationListsForBuffer( buffer_number,
                               diagnostics,
                               open_on_edit = False ):
  """Populate location lists for all windows containing the buffer with number
  |buffer_number|. See SetLocationListForWindow for format of diagnostics."""
  for window in GetWindowsForBufferNumber( buffer_number ):
    SetLocationListForWindow( window.number, diagnostics, open_on_edit )


def SetLocationListForWindow( window_number,
                              diagnostics,
                              open_on_edit = False ):
  """Populate the location list with diagnostics. Diagnostics should be in
  qflist format; see ":h setqflist" for details."""
  ycm_loc_id = vim.windows[ window_number - 1 ].vars.get( 'ycm_loc_id' )
  # User may have made a bunch of `:lgrep` calls and we do not own the
  # location list with the ID we remember any more.
  if ( ycm_loc_id is not None and
       vim.eval( f'getloclist( { window_number }, '
                               f'{{ "id": { ycm_loc_id }, '
                                '"title": 0 } ).title' ) == 'ycm_loc' ):
    ycm_loc_id = None

  if ycm_loc_id is None:
    # Create new and populate
    vim.eval( f'setloclist( { window_number }, '
                           '[], '
                           '" ", '
                           '{ "title": "ycm_loc", '
                            f'"items": { json.dumps( diagnostics ) } }} )' )
    vim.windows[ window_number - 1 ].vars[ 'ycm_loc_id' ] = GetIntValue(
        f'getloclist( { window_number }, {{ "nr": "$", "id": 0 }} ).id' )
  elif open_on_edit:
    # Remove old and create new list
    vim.eval( f'setloclist( { window_number }, '
                           '[], '
                           '"r", '
                          f'{{ "id": { ycm_loc_id }, '
                              '"items": [], "title": "" } )' )
    vim.eval( f'setloclist( { window_number }, '
                           '[], '
                           '" ", '
                           '{ "title": "ycm_loc", '
                            f'"items": { json.dumps( diagnostics ) } }} )' )
    vim.windows[ window_number - 1 ].vars[ 'ycm_loc_id' ] = GetIntValue(
        f'getloclist( { window_number }, {{ "nr": "$", "id": 0 }} ).id' )
  else:
    # Just populate the old one
    vim.eval( f'setloclist( { window_number }, '
                           '[], '
                           '"r", '
                          f'{{ "id": { ycm_loc_id }, '
                             f'"items": { json.dumps( diagnostics ) } }} )' )


def OpenLocationList( focus = False, autoclose = False ):
  """Open the location list to the bottom of the current window with its
  height automatically set to fit all entries. This behavior can be overridden
  by using the YcmLocationOpened autocommand. When focus is set to True, the
  location list window becomes the active window. When autoclose is set to True,
  the location list window is automatically closed after an entry is
  selected."""
  vim.command( 'lopen' )

  SetFittingHeightForCurrentWindow()

  if autoclose:
    AutoCloseOnCurrentBuffer( 'ycmlocation' )

  if VariableExists( '#User#YcmLocationOpened' ):
    vim.command( 'doautocmd User YcmLocationOpened' )

  if not focus:
    JumpToPreviousWindow()


def SetQuickFixList( quickfix_list ):
  """Populate the quickfix list and open it. List should be in qflist format:
  see ":h setqflist" for details."""
  vim.eval( f'setqflist( { json.dumps( quickfix_list ) } )' )


def OpenQuickFixList( focus = False, autoclose = False ):
  """Open the quickfix list to full width at the bottom of the screen with its
  height automatically set to fit all entries. This behavior can be overridden
  by using the YcmQuickFixOpened autocommand.
  See the OpenLocationList function for the focus and autoclose options."""
  vim.command( 'botright copen' )

  SetFittingHeightForCurrentWindow()

  if autoclose:
    AutoCloseOnCurrentBuffer( 'ycmquickfix' )

  if VariableExists( '#User#YcmQuickFixOpened' ):
    vim.command( 'doautocmd User YcmQuickFixOpened' )

  if not focus:
    JumpToPreviousWindow()


def ComputeFittingHeightForCurrentWindow():
  current_window = vim.current.window
  if not current_window.options[ 'wrap' ]:
    return len( vim.current.buffer )

  window_width = current_window.width
  fitting_height = 0
  for line in vim.current.buffer:
    fitting_height += len( line ) // window_width + 1
  return fitting_height


def SetFittingHeightForCurrentWindow():
  if int( vim.current.buffer.vars.get( 'ycm_no_resize', 0 ) ):
    return

  vim.command( f'{ ComputeFittingHeightForCurrentWindow() }wincmd _' )


def ConvertDiagnosticsToQfList( diagnostics ):
  def ConvertDiagnosticToQfFormat( diagnostic ):
    # See :h getqflist for a description of the dictionary fields.
    # Note that, as usual, Vim is completely inconsistent about whether
    # line/column numbers are 1 or 0 based in its various APIs. Here, it wants
    # them to be 1-based. The documentation states quite clearly that it
    # expects a byte offset, by which it means "1-based column number" as
    # described in :h getqflist ("the first column is 1").
    location = diagnostic[ 'location' ]
    line_num = location[ 'line_num' ]

    # libclang can give us diagnostics that point "outside" the file; Vim borks
    # on these.
    if line_num < 1:
      line_num = 1

    text = diagnostic[ 'text' ]
    if diagnostic.get( 'fixit_available', False ):
      text += ' (FixIt available)'

    return {
      'bufnr' : GetBufferNumberForFilename( location[ 'filepath' ],
                                            create_buffer_if_needed = True ),
      'lnum'  : line_num,
      'col'   : location[ 'column_num' ],
      'text'  : text,
      'type'  : diagnostic[ 'kind' ][ 0 ],
      'valid' : 1
    }

  return [ ConvertDiagnosticToQfFormat( x ) for x in diagnostics ]


def GetVimGlobalsKeys():
  return vim.eval( 'keys( g: )' )


def VimExpressionToPythonType( vim_expression ):
  """Returns a Python type from the return value of the supplied Vim expression.
  If the expression returns a list, dict or other non-string type, then it is
  returned unmodified. If the string return can be converted to an
  integer, returns an integer, otherwise returns the result converted to a
  Unicode string."""

  result = vim.eval( vim_expression )
  if not ( isinstance( result, str ) or isinstance( result, bytes ) ):
    return result

  try:
    return int( result )
  except ValueError:
    return ToUnicode( result )


def HiddenEnabled( buffer_object ):
  if buffer_object.options[ 'bh' ] == "hide":
    return True
  return GetBoolValue( '&hidden' )


def BufferIsUsable( buffer_object ):
  return not BufferModified( buffer_object ) or HiddenEnabled( buffer_object )


def EscapeFilepathForVimCommand( filepath ):
  return GetVariableValue( f"fnameescape('{ EscapeForVim( filepath ) }')" )


def ComparePaths( path1, path2 ):
  # Assume that the file system is case-insensitive on Windows and macOS and
  # case-sensitive on other platforms. While this is not necessarily true, being
  # completely correct here is not worth the trouble as this assumption
  # represents the overwhelming use case and detecting the case sensitivity of a
  # file system is tricky.
  if OnWindows() or OnMac():
    return path1.lower() == path2.lower()
  return path1 == path2


# Both |line| and |column| need to be 1-based
def TryJumpLocationInTab( tab, filename, line, column ):
  for win in tab.windows:
    if ComparePaths( GetBufferFilepath( win.buffer ), filename ):
      vim.current.tabpage = tab
      vim.current.window = win
      if line is not None and column is not None:
        vim.current.window.cursor = ( line, column - 1 )
        # Open possible folding at location
        vim.command( 'normal! zv' )
        # Center the screen on the jumped-to location
        vim.command( 'normal! zz' )

      return True
  # 'filename' is not opened in this tab page
  return False


# Both |line| and |column| need to be 1-based
def TryJumpLocationInTabs( filename, line, column ):
  for tab in vim.tabpages:
    if TryJumpLocationInTab( tab, filename, line, column ):
      return True
  # 'filename' is not opened in any tab pages
  return False


# Maps User command to vim command
def GetVimCommand( user_command, default = 'edit' ):
  vim_command = BUFFER_COMMAND_MAP.get( user_command, default )
  if vim_command == 'edit' and not BufferIsUsable( vim.current.buffer ):
    vim_command = 'split'
  return vim_command


def JumpToFile( filename, command, modifiers ):
  vim_command = GetVimCommand( command )
  try:
    escaped_filename = EscapeFilepathForVimCommand( filename )
    vim.command(
        f'keepjumps { modifiers } { vim_command } { escaped_filename }' )
  # When the file we are trying to jump to has a swap file
  # Vim opens swap-exists-choices dialog and throws vim.error with E325 error,
  # or KeyboardInterrupt after user selects one of the options.
  except vim.error as e:
    if 'E325' not in str( e ):
      raise
    # Do nothing if the target file is still not opened (user chose (Q)uit).
    if filename != GetCurrentBufferFilepath():
      return False
  # Thrown when user chooses (A)bort in .swp message box.
  except KeyboardInterrupt:
    return False
  return True


# Both |line| and |column| need to be 1-based
def JumpToLocation( filename, line, column, modifiers, command ):
  # Add an entry to the jumplist
  vim.command( "normal! m'" )

  if filename != GetCurrentBufferFilepath():
    # We prefix the command with 'keepjumps' so that opening the file is not
    # recorded in the jumplist. So when we open the file and move the cursor to
    # a location in it, the user can use CTRL-O to jump back to the original
    # location, not to the start of the newly opened file.
    # Sadly this fails on random occasions and the undesired jump remains in the
    # jumplist.
    if command == 'split-or-existing-window':
      if 'tab' in modifiers:
        if TryJumpLocationInTabs( filename, line, column ):
          return
      elif TryJumpLocationInTab( vim.current.tabpage, filename, line, column ):
        return
      command = 'split'

    # This command is kept for backward compatibility. :tab should be used with
    # the 'split-or-existing-window' command instead.
    if command == 'new-or-existing-tab':
      if TryJumpLocationInTabs( filename, line, column ):
        return
      command = 'new-tab'

    if not JumpToFile( filename, command, modifiers ):
      return

  if line is not None and column is not None:
    vim.current.window.cursor = ( line, column - 1 )

    # Open possible folding at location
    vim.command( 'normal! zv' )
    # Center the screen on the jumped-to location
    vim.command( 'normal! zz' )


def NumLinesInBuffer( buffer_object ):
  # This is actually less than obvious, that's why it's wrapped in a function
  return len( buffer_object )


# Calling this function from the non-GUI thread will sometimes crash Vim. At
# the time of writing, YCM only uses the GUI thread inside Vim (this used to
# not be the case).
def PostVimMessage( message, warning = True, truncate = False ):
  """Display a message on the Vim status line. By default, the message is
  highlighted and logged to Vim command-line history (see :h history).
  Unset the |warning| parameter to disable this behavior. Set the |truncate|
  parameter to avoid hit-enter prompts (see :h hit-enter) when the message is
  longer than the window width."""
  echo_command = 'echom' if warning else 'echo'

  # Displaying a new message while previous ones are still on the status line
  # might lead to a hit-enter prompt or the message appearing without a
  # newline so we do a redraw first.
  vim.command( 'redraw' )

  if warning:
    vim.command( 'echohl WarningMsg' )

  message = ToUnicode( message )

  if truncate:
    vim_width = GetIntValue( '&columns' )

    message = message.replace( '\n', ' ' )
    if len( message ) >= vim_width:
      message = message[ : vim_width - 4 ] + '...'

    old_ruler = GetIntValue( '&ruler' )
    old_showcmd = GetIntValue( '&showcmd' )
    vim.command( 'set noruler noshowcmd' )

    vim.command( f"{ echo_command } '{ EscapeForVim( message ) }'" )

    SetVariableValue( '&ruler', old_ruler )
    SetVariableValue( '&showcmd', old_showcmd )
  else:
    for line in message.split( '\n' ):
      vim.command( f"{ echo_command } '{ EscapeForVim( line ) }'" )

  if warning:
    vim.command( 'echohl None' )


def PresentDialog( message, choices, default_choice_index = 0 ):
  """Presents the user with a dialog where a choice can be made.
  This will be a dialog for gvim users or a question in the message buffer
  for vim users or if `set guioptions+=c` was used.

  choices is list of alternatives.
  default_choice_index is the 0-based index of the default element
  that will get choosen if the user hits <CR>. Use -1 for no default.

  PresentDialog will return a 0-based index into the list
  or -1 if the dialog was dismissed by using <Esc>, Ctrl-C, etc.

  If you are presenting a list of options for the user to choose from, such as
  a list of imports, or lines to insert (etc.), SelectFromList is a better
  option.

  See also:
    :help confirm() in vim (Note that vim uses 1-based indexes)

  Example call:
    PresentDialog("Is this a nice example?", ["Yes", "No", "May&be"])
      Is this a nice example?
      [Y]es, (N)o, May(b)e:"""
  message = EscapeForVim( ToUnicode( message ) )
  choices = EscapeForVim( ToUnicode( '\n'.join( choices ) ) )
  to_eval = ( f"confirm('{ message }', "
                      f"'{ choices }', "
                      f"{ default_choice_index + 1 })" )
  try:
    return GetIntValue( to_eval ) - 1
  except KeyboardInterrupt:
    return -1


def Confirm( message ):
  """Display |message| with Ok/Cancel operations. Returns True if the user
  selects Ok"""
  return bool( PresentDialog( message, [ "Ok", "Cancel" ] ) == 0 )


def SelectFromList( prompt, items ):
  """Ask the user to select an item from the list |items|.

  Presents the user with |prompt| followed by a numbered list of |items|,
  from which they select one. The user is asked to enter the number of an
  item or click it.

  |items| should not contain leading ordinals: they are added automatically.

  Returns the 0-based index in the list |items| that the user selected, or an
  exception if no valid item was selected.

  See also :help inputlist()."""

  vim_items = [ prompt ]
  vim_items.extend( [ f"{ i + 1 }: { item }"
                      for i, item in enumerate( items ) ] )

  # The vim documentation warns not to present lists larger than the number of
  # lines of display. This is sound advice, but there really isn't any sensible
  # thing we can do in that scenario. Testing shows that Vim just pages the
  # message; that behaviour is as good as any, so we don't manipulate the list,
  # or attempt to page it.

  # For an explanation of the purpose of inputsave() / inputrestore(),
  # see :help input(). Briefly, it makes inputlist() work as part of a mapping.
  vim.eval( 'inputsave()' )
  try:
    # Vim returns the number the user entered, or the line number the user
    # clicked. This may be wildly out of range for our list. It might even be
    # negative.
    #
    # The first item is index 0, and this maps to our "prompt", so we subtract 1
    # from the result and return that, assuming it is within the range of the
    # supplied list. If not, we return negative.
    #
    # See :help input() for explanation of the use of inputsave() and inpput
    # restore(). It is done in try/finally in case vim.eval ever throws an
    # exception (such as KeyboardInterrupt)
    selected = GetIntValue( "inputlist( " + json.dumps( vim_items ) + " )" ) - 1
  except KeyboardInterrupt:
    selected = -1
  finally:
    vim.eval( 'inputrestore()' )

  if selected < 0 or selected >= len( items ):
    # User selected something outside of the range
    raise RuntimeError( NO_SELECTION_MADE_MSG )

  return selected


def EscapeForVim( text ):
  return ToUnicode( text.replace( "'", "''" ) )


def AllOpenedFiletypes():
  """Returns a dict mapping filetype to list of buffer numbers for all open
  buffers"""
  filetypes = defaultdict( list )
  for buffer in vim.buffers:
    for filetype in FiletypesForBuffer( buffer ):
      filetypes[ filetype ].append( buffer.number )
  return filetypes


def CurrentFiletypes():
  filetypes = vim.eval( "&filetype" )
  if not filetypes:
    filetypes = 'ycm_nofiletype'
  return ToUnicode( filetypes ).split( '.' )


def CurrentFiletypesEnabled( disabled_filetypes ):
  """Return False if one of the current filetypes is disabled, True otherwise.
  |disabled_filetypes| must be a dictionary where keys are the disabled
  filetypes and values are unimportant. The special key '*' matches all
  filetypes."""
  return ( '*' not in disabled_filetypes and
           not any( x in disabled_filetypes for x in CurrentFiletypes() ) )


def GetBufferFiletypes( bufnr ):
  command = f'getbufvar({ bufnr }, "&ft")'
  filetypes = vim.eval( command )
  if not filetypes:
    filetypes = 'ycm_nofiletype'
  return ToUnicode( filetypes ).split( '.' )


def FiletypesForBuffer( buffer_object ):
  # NOTE: Getting &ft for other buffers only works when the buffer has been
  # visited by the user at least once, which is true for modified buffers

  # We don't use
  #
  #   buffer_object.options[ 'ft' ]
  #
  # to get the filetypes because this causes annoying flickering when the buffer
  # is hidden.
  return GetBufferFiletypes( buffer_object.number )


def VariableExists( variable ):
  return GetBoolValue( f"exists( '{ EscapeForVim( variable ) }' )" )


def SetVariableValue( variable, value ):
  vim.command( f"let { variable } = { json.dumps( value ) }" )


def GetVariableValue( variable ):
  return vim.eval( variable )


def GetBoolValue( variable ):
  return bool( int( vim.eval( variable ) ) )


def GetIntValue( variable ):
  return int( vim.eval( variable ) )


def _SortChunksByFile( chunks ):
  """Sort the members of the list |chunks| (which must be a list of dictionaries
  conforming to ycmd.responses.FixItChunk) by their filepath. Returns a new
  list in arbitrary order."""

  chunks_by_file = defaultdict( list )

  for chunk in chunks:
    filepath = chunk[ 'range' ][ 'start' ][ 'filepath' ]
    chunks_by_file[ filepath ].append( chunk )

  return chunks_by_file


def _GetNumNonVisibleFiles( file_list ):
  """Returns the number of file in the iterable list of files |file_list| which
  are not curerntly open in visible windows"""
  return len(
      [ f for f in file_list
        if not BufferIsVisible( GetBufferNumberForFilename( f ) ) ] )


def _OpenFileInSplitIfNeeded( filepath ):
  """Ensure that the supplied filepath is open in a visible window, opening a
  new split if required. Returns the buffer number of the file and an indication
  of whether or not a new split was opened.

  If the supplied filename is already open in a visible window, return just
  return its buffer number. If the supplied file is not visible in a window
  in the current tab, opens it in a new vertical split.

  Returns a tuple of ( buffer_num, split_was_opened ) indicating the buffer
  number and whether or not this method created a new split. If the user opts
  not to open a file, or if opening fails, this method raises RuntimeError,
  otherwise, guarantees to return a visible buffer number in buffer_num."""

  buffer_num = GetBufferNumberForFilename( filepath )

  # We only apply changes in the current tab page (i.e. "visible" windows).
  # Applying changes in tabs does not lead to a better user experience, as the
  # quickfix list no longer works as you might expect (doesn't jump into other
  # tabs), and the complexity of choosing where to apply edits is significant.
  if BufferIsVisible( buffer_num ):
    # file is already open and visible, just return that buffer number (and an
    # idicator that we *didn't* open a split)
    return ( buffer_num, False )

  # The file is not open in a visible window, so we open it in a split.
  # We open the file with a small, fixed height. This means that we don't
  # make the current buffer the smallest after a series of splits.
  OpenFilename( filepath, {
    'focus': True,
    'fix': True,
    'size': GetIntValue( '&previewheight' ),
  } )

  # OpenFilename returns us to the original cursor location. This is what we
  # want, because we don't want to disorientate the user, but we do need to
  # know the (now open) buffer number for the filename
  buffer_num = GetBufferNumberForFilename( filepath )
  if not BufferIsVisible( buffer_num ):
    # This happens, for example, if there is a swap file and the user
    # selects the "Quit" or "Abort" options. We just raise an exception to
    # make it clear to the user that the abort has left potentially
    # partially-applied changes.
    raise RuntimeError(
        f'Unable to open file: { filepath }\nFixIt/Refactor operation '
        'aborted prior to completion. Your files have not been '
        'fully updated. Please use undo commands to revert the '
        'applied changes.' )

  # We opened this file in a split
  return ( buffer_num, True )


def ReplaceChunks( chunks, silent=False ):
  """Apply the source file deltas supplied in |chunks| to arbitrary files.
  |chunks| is a list of changes defined by ycmd.responses.FixItChunk,
  which may apply arbitrary modifications to arbitrary files.

  If a file specified in a particular chunk is not currently open in a visible
  buffer (i.e., one in a window visible in the current tab), we:
    - issue a warning to the user that we're going to open new files (and offer
      her the option to abort cleanly)
    - open the file in a new split, make the changes, then hide the buffer.

  If for some reason a file could not be opened or changed, raises RuntimeError.
  Otherwise, returns no meaningful value."""

  # We apply the edits file-wise for efficiency.
  chunks_by_file = _SortChunksByFile( chunks )

  # We sort the file list simply to enable repeatable testing.
  sorted_file_list = sorted( chunks_by_file.keys() )

  if not silent:
    # Make sure the user is prepared to have her screen mutilated by the new
    # buffers.
    num_files_to_open = _GetNumNonVisibleFiles( sorted_file_list )

    if num_files_to_open > 0:
      if not Confirm(
            FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( num_files_to_open ) ):
        return

  # Store the list of locations where we applied changes. We use this to display
  # the quickfix window showing the user where we applied changes.
  locations = []

  for filepath in sorted_file_list:
    buffer_num, close_window = _OpenFileInSplitIfNeeded( filepath )

    locations.extend( ReplaceChunksInBuffer( chunks_by_file[ filepath ],
                                             vim.buffers[ buffer_num ] ) )

    # When opening tons of files, we don't want to have a split for each new
    # file, as this simply does not scale, so we open the window, make the
    # edits, then hide the window.
    if close_window:
      # Some plugins (I'm looking at you, syntastic) might open a location list
      # for the window we just opened. We don't want that location list hanging
      # around, so we close it. lclose is a no-op if there is no location list.
      vim.command( 'lclose' )

      # Note that this doesn't lose our changes. It simply "hides" the buffer,
      # which can later be re-accessed via the quickfix list or `:ls`
      vim.command( 'hide' )

  # Open the quickfix list, populated with entries for each location we changed.
  if not silent:
    if locations:
      SetQuickFixList( locations )

    PostVimMessage( f'Applied { len( chunks ) } changes', warning = False )


def ReplaceChunksInBuffer( chunks, vim_buffer ):
  """Apply changes in |chunks| to the buffer-like object |buffer| and return the
  locations for that buffer."""

  # We apply the chunks from the bottom to the top of the buffer so that we
  # don't need to adjust the position of the remaining chunks due to text
  # changes. This assumes that chunks are not overlapping. However, we still
  # allow multiple chunks to share the same starting position (because of the
  # language server protocol specs). These chunks must be applied in their order
  # of appareance. Since Python sorting is stable, if we sort the whole list in
  # reverse order of location, these chunks will be reversed. Therefore, we
  # need to fully reverse the list then sort it on the starting position in
  # reverse order.
  chunks.reverse()
  chunks.sort( key = lambda chunk: (
    chunk[ 'range' ][ 'start' ][ 'line_num' ],
    chunk[ 'range' ][ 'start' ][ 'column_num' ]
  ), reverse = True )

  # However, we still want to display the locations from the top of the buffer
  # to its bottom.
  return reversed( [ ReplaceChunk( chunk[ 'range' ][ 'start' ],
                                   chunk[ 'range' ][ 'end' ],
                                   chunk[ 'replacement_text' ],
                                   vim_buffer )
                     for chunk in chunks ] )


def SplitLines( contents ):
  """Return a list of each of the lines in the byte string |contents|.
  Behavior is equivalent to str.splitlines with the following exceptions:
   - empty strings are returned as [ '' ];
   - a trailing newline is not ignored (i.e. SplitLines( '\n' )
     returns [ '', '' ], not [ '' ] )."""
  if contents == b'':
    return [ b'' ]

  lines = contents.splitlines()

  if contents.endswith( b'\r' ) or contents.endswith( b'\n' ):
    lines.append( b'' )

  return lines


# Replace the chunk of text specified by a contiguous range with the supplied
# text and return the location.
# * start and end are objects with line_num and column_num properties
# * the range is inclusive
# * indices are all 1-based
#
# NOTE: Works exclusively with bytes() instances and byte offsets as returned
# by ycmd and used within the Vim buffers
def ReplaceChunk( start, end, replacement_text, vim_buffer ):
  # ycmd's results are all 1-based, but vim's/python's are all 0-based
  # (so we do -1 on all of the values)
  start_line = start[ 'line_num' ] - 1
  end_line = end[ 'line_num' ] - 1

  start_column = start[ 'column_num' ] - 1
  end_column = end[ 'column_num' ] - 1

  # When sending a request to the server, a newline is added to the buffer
  # contents to match what gets saved to disk. If the server generates a chunk
  # containing that newline, this chunk goes past the Vim buffer contents since
  # there is actually no new line. When this happens, recompute the end position
  # of where the chunk is applied and remove all trailing characters in the
  # chunk.
  if end_line >= len( vim_buffer ):
    end_column = len( ToBytes( vim_buffer[ -1 ] ) )
    end_line = len( vim_buffer ) - 1
    replacement_text = replacement_text.rstrip()

  # NOTE: replacement_text is unicode, but all our offsets are byte offsets,
  # so we convert to bytes
  replacement_lines = SplitLines( ToBytes( replacement_text ) )

  # NOTE: Vim buffers are a list of unicode objects on Python 3.
  start_existing_text = ToBytes( vim_buffer[ start_line ] )[ : start_column ]
  end_line_text = ToBytes( vim_buffer[ end_line ] )
  end_existing_text = end_line_text[ end_column : ]

  replacement_lines[ 0 ] = start_existing_text + replacement_lines[ 0 ]
  replacement_lines[ -1 ] = replacement_lines[ -1 ] + end_existing_text

  cursor_line, cursor_column = CurrentLineAndColumn()

  vim_buffer[ start_line : end_line + 1 ] = replacement_lines[ : ]

  # When the cursor position is on the last line in the replaced area, and ends
  # up somewhere after the end of the new text, we need to reset the cursor
  # position. This is because Vim doesn't know where to put it, and guesses
  # badly. We put it at the end of the new text.
  if cursor_line == end_line and cursor_column >= end_column:
    cursor_line = start_line + len( replacement_lines ) - 1
    cursor_column += len( replacement_lines[ - 1 ] ) - len( end_line_text )
    SetCurrentLineAndColumn( cursor_line, cursor_column )

  return {
    'bufnr': vim_buffer.number,
    'filename': vim_buffer.name,
    # line and column numbers are 1-based in qflist
    'lnum': start_line + 1,
    'col': start_column + 1,
    'text': replacement_text,
    'type': 'F',
  }


def InsertNamespace( namespace ):
  if VariableExists( 'g:ycm_csharp_insert_namespace_expr' ):
    expr = GetVariableValue( 'g:ycm_csharp_insert_namespace_expr' )
    if expr:
      SetVariableValue( "g:ycm_namespace_to_insert", namespace )
      vim.eval( expr )
      return

  pattern = r'^\s*using\(\s\+[a-zA-Z0-9]\+\s\+=\)\?\s\+[a-zA-Z0-9.]\+\s*;\s*'
  existing_indent = ''
  line = SearchInCurrentBuffer( pattern )
  if line:
    existing_line = LineTextInCurrentBuffer( line )
    existing_indent = re.sub( r'\S.*', '', existing_line )
  new_line = f'{ existing_indent }using { namespace };\n'
  replace_pos = { 'line_num': line + 1, 'column_num': 1 }
  ReplaceChunk( replace_pos, replace_pos, new_line, vim.current.buffer )
  PostVimMessage( f'Add namespace: { namespace }', warning = False )


def SearchInCurrentBuffer( pattern ):
  """ Returns the 1-indexed line on which the pattern matches
  (going UP from the current position) or 0 if not found """
  return GetIntValue( f"search('{ EscapeForVim( pattern ) }', 'Wcnb')" )


def LineTextInCurrentBuffer( line_number ):
  """ Returns the text on the 1-indexed line (NOT 0-indexed) """
  return vim.current.buffer[ line_number - 1 ]


def ClosePreviewWindow():
  """ Close the preview window if it is present, otherwise do nothing """
  vim.command( 'silent! pclose!' )


def JumpToPreviewWindow():
  """ Jump the vim cursor to the preview window, which must be active. Returns
  boolean indicating if the cursor ended up in the preview window """
  vim.command( 'silent! wincmd P' )
  return vim.current.window.options[ 'previewwindow' ]


def JumpToPreviousWindow():
  """ Jump the vim cursor to its previous window position """
  vim.command( 'silent! wincmd p' )


def JumpToTab( tab_number ):
  """Jump to Vim tab with corresponding number """
  vim.command( f'silent! tabn { tab_number }' )


def OpenFileInPreviewWindow( filename ):
  """ Open the supplied filename in the preview window """
  vim.command( 'silent! pedit! ' + filename )


def WriteToPreviewWindow( message ):
  """ Display the supplied message in the preview window """

  # This isn't something that comes naturally to Vim. Vim only wants to show
  # tags and/or actual files in the preview window, so we have to hack it a
  # little bit. We generate a temporary file name and "open" that, then write
  # the data to it. We make sure the buffer can't be edited or saved. Other
  # approaches include simply opening a split, but we want to take advantage of
  # the existing Vim options for preview window height, etc.

  ClosePreviewWindow()

  OpenFileInPreviewWindow( vim.eval( 'tempname()' ) )

  if JumpToPreviewWindow():
    # We actually got to the preview window. By default the preview window can't
    # be changed, so we make it writable, write to it, then make it read only
    # again.
    vim.current.buffer.options[ 'modifiable' ] = True
    vim.current.buffer.options[ 'readonly' ]   = False

    vim.current.buffer[ : ] = message.splitlines()

    vim.current.buffer.options[ 'buftype' ]    = 'nofile'
    vim.current.buffer.options[ 'bufhidden' ]  = 'wipe'
    vim.current.buffer.options[ 'buflisted' ]  = False
    vim.current.buffer.options[ 'swapfile' ]   = False
    vim.current.buffer.options[ 'modifiable' ] = False
    vim.current.buffer.options[ 'readonly' ]   = True

    # We need to prevent closing the window causing a warning about unsaved
    # file, so we pretend to Vim that the buffer has not been changed.
    vim.current.buffer.options[ 'modified' ]   = False

    JumpToPreviousWindow()
  else:
    # We couldn't get to the preview window, but we still want to give the user
    # the information we have. The only remaining option is to echo to the
    # status area.
    PostVimMessage( message, warning = False )


def BufferIsVisibleForFilename( filename ):
  """Check if a buffer exists for a specific file."""
  buffer_number = GetBufferNumberForFilename( filename )
  return BufferIsVisible( buffer_number )


def CloseBuffersForFilename( filename ):
  """Close all buffers for a specific file."""
  buffer_number = GetBufferNumberForFilename( filename )
  while buffer_number != -1:
    vim.command( f'silent! bwipeout! { buffer_number }' )
    new_buffer_number = GetBufferNumberForFilename( filename )
    if buffer_number == new_buffer_number:
      raise RuntimeError( f"Buffer { buffer_number } for filename "
                          f"'{ filename }' should already be wiped out." )
    buffer_number = new_buffer_number


def OpenFilename( filename, options = {} ):
  """Open a file in Vim. Following options are available:
  - command: specify which Vim command is used to open the file. Choices
  are same-buffer, horizontal-split, vertical-split, and new-tab (default:
  horizontal-split);
  - size: set the height of the window for a horizontal split or the width for
  a vertical one (default: '');
  - fix: set the winfixheight option for a horizontal split or winfixwidth for
  a vertical one (default: False). See :h winfix for details;
  - focus: focus the opened file (default: False);
  - watch: automatically watch for changes (default: False). This is useful
  for logs;
  - position: set the position where the file is opened (default: start).
  Choices are 'start' and 'end'.
  - mods: The vim <mods> for the command, such as :vertical"""

  # Set the options.
  command = GetVimCommand( options.get( 'command', 'horizontal-split' ),
                           'horizontal-split' )
  size = ( options.get( 'size', '' ) if command in [ 'split', 'vsplit' ] else
           '' )
  focus = options.get( 'focus', False )

  # There is no command in Vim to return to the previous tab so we need to
  # remember the current tab if needed.
  if not focus and command == 'tabedit':
    previous_tab = GetIntValue( 'tabpagenr()' )
  else:
    previous_tab = None

  # Open the file.
  try:
    vim.command( f'{ options.get( "mods", "") }'
                 f'{ size }'
                 f'{ command } '
                 f'{ filename }' )
  # When the file we are trying to jump to has a swap file,
  # Vim opens swap-exists-choices dialog and throws vim.error with E325 error,
  # or KeyboardInterrupt after user selects one of the options which actually
  # opens the file (Open read-only/Edit anyway).
  except vim.error as e:
    if 'E325' not in str( e ):
      raise

    # Otherwise, the user might have chosen Quit. This is detectable by the
    # current file not being the target file
    if filename != GetCurrentBufferFilepath():
      return
  except KeyboardInterrupt:
    # Raised when the user selects "Abort" after swap-exists-choices
    return

  _SetUpLoadedBuffer( command,
                      filename,
                      options.get( 'fix', False ),
                      options.get( 'position', 'start' ),
                      options.get( 'watch', False ) )

  # Vim automatically set the focus to the opened file so we need to get the
  # focus back (if the focus option is disabled) when opening a new tab or
  # window.
  if not focus:
    if command == 'tabedit':
      JumpToTab( previous_tab )
    if command in [ 'split', 'vsplit' ]:
      JumpToPreviousWindow()


def _SetUpLoadedBuffer( command, filename, fix, position, watch ):
  """After opening a buffer, configure it according to the supplied options,
  which are as defined by the OpenFilename method."""

  if command == 'split':
    vim.current.window.options[ 'winfixheight' ] = fix
  if command == 'vsplit':
    vim.current.window.options[ 'winfixwidth' ] = fix

  if watch:
    vim.current.buffer.options[ 'autoread' ] = True
    vim.command( "exec 'au BufEnter <buffer> :silent! checktime {0}'"
                 .format( filename ) )

  if position == 'end':
    vim.command( 'silent! normal! Gzz' )


def BuildRange( start_line, end_line ):
  # Vim only returns the starting and ending lines of the range of a command.
  # Check if those lines correspond to a previous visual selection and if they
  # do, use the columns of that selection to build the range.
  start = vim.current.buffer.mark( '<' )
  end = vim.current.buffer.mark( '>' )
  if not start or not end or start_line != start[ 0 ] or end_line != end[ 0 ]:
    start = [ start_line, 0 ]
    end = [ end_line, len( vim.current.buffer[ end_line - 1 ] ) ]
  # Vim Python API returns 1-based lines and 0-based columns while ycmd expects
  # 1-based lines and columns.
  return {
    'range': {
      'start': {
        'line_num': start[ 0 ],
        'column_num': start[ 1 ] + 1
      },
      'end': {
        'line_num': end[ 0 ],
        # Vim returns the maximum 32-bit integer value when a whole line is
        # selected. Use the end of line instead.
        'column_num': min( end[ 1 ],
                           len( vim.current.buffer[ end[ 0 ] - 1 ] ) ) + 1
      }
    }
  }


# Expects version_string in 'MAJOR.MINOR.PATCH' format, e.g. '8.1.278'
def VimVersionAtLeast( version_string ):
  major, minor, patch = ( int( x ) for x in version_string.split( '.' ) )

  # For Vim 8.1.278, v:version is '801'
  actual_major_and_minor = GetIntValue( 'v:version' )
  matching_major_and_minor = major * 100 + minor
  if actual_major_and_minor != matching_major_and_minor:
    return actual_major_and_minor > matching_major_and_minor

  return GetBoolValue( f"has( 'patch{ patch }' )" )


def AutoCloseOnCurrentBuffer( name ):
  """Create an autocommand group with name |name| on the current buffer that
  automatically closes it when leaving its window."""
  vim.command( f'augroup { name }' )
  vim.command( 'autocmd! * <buffer>' )
  vim.command( 'autocmd WinLeave <buffer> '
               'if bufnr( "%" ) == expand( "<abuf>" ) | q | endif '
               f'| autocmd! { name }' )
  vim.command( 'augroup END' )


@memoize()
def VimIsNeovim():
  return GetBoolValue( 'has( "nvim" )' )


@memoize()
def HasFastPropList():
  return GetBoolValue( 'has( "patch-8.2.3652" )' )


@memoize()
def VimSupportsPopupWindows():
  return VimHasFunctions( 'popup_create',
                          'popup_atcursor',
                          'popup_move',
                          'popup_hide',
                          'popup_settext',
                          'popup_show',
                          'popup_close' )


@memoize()
def VimSupportsVirtualText():
  return not VimIsNeovim() and VimVersionAtLeast( VIM_VIRTUAL_TEXT_VERSION_REQ )


@memoize()
def VimHasFunction( func ):
  return bool( GetIntValue( f"exists( '*{ EscapeForVim( func ) }' )" ) )


def VimHasFunctions( *functions ):
  return all( VimHasFunction( f ) for f in functions )


def WinIDForWindow( window ):
  return GetIntValue( f'win_getid( { window.number }, '
                                 f'{ window.tabpage.number } )' )


def ScreenPositionForLineColumnInWindow( window, line, column ):
  return vim.eval( f'screenpos( { WinIDForWindow( window ) }, '
                              f'{ line }, '
                              f'{ column } )' )


def UsingPreviewPopup():
  return 'popup' in ToUnicode( vim.options[ 'completeopt' ] ).split( ',' )


def DisplayWidth():
  return GetIntValue( '&columns' )


def DisplayWidthOfString( s ):
  return GetIntValue( f"strdisplaywidth( '{ EscapeForVim( s ) }' )" )


def BuildQfListItem( goto_data_item ):
  qf_item = {}
  if 'filepath' in goto_data_item:
    qf_item[ 'filename' ] = ToUnicode( goto_data_item[ 'filepath' ] )
  if 'description' in goto_data_item:
    qf_item[ 'text' ] = ToUnicode( goto_data_item[ 'description' ] )
  if 'line_num' in goto_data_item:
    qf_item[ 'lnum' ] = goto_data_item[ 'line_num' ]
  if 'column_num' in goto_data_item:
    # ycmd returns columns 1-based, and QuickFix lists require "byte offsets".
    # See :help getqflist and equivalent comment in
    # vimsupport.ConvertDiagnosticsToQfList.
    #
    # When the Vim help says "byte index", it really means "1-based column
    # number" (which is somewhat confusing). :help getqflist states "first
    # column is 1".
    qf_item[ 'col' ] = goto_data_item[ 'column_num' ]

  return qf_item

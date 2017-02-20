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

from future.utils import iterkeys
import vim
import os
import json
import re
from collections import defaultdict
from ycmd.utils import ( GetCurrentDirectory, JoinLinesAsUnicode, ToBytes,
                         ToUnicode )
from ycmd import user_options_store

BUFFER_COMMAND_MAP = { 'same-buffer'      : 'edit',
                       'horizontal-split' : 'split',
                       'vertical-split'   : 'vsplit',
                       'new-tab'          : 'tabedit' }

FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT = (
    'The requested operation will apply changes to {0} files which are not '
    'currently open. This will therefore open {0} new files in the hidden '
    'buffers. The quickfix list can then be used to review the changes. No '
    'files will be written to disk. Do you wish to continue?' )

NO_SELECTION_MADE_MSG = "No valid selection was made; aborting."


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
  return ToUnicode( vim.current.line )


def TextAfterCursor():
  """Returns the text after CurrentColumn."""
  return ToUnicode( vim.current.line[ CurrentColumn(): ] )


def TextBeforeCursor():
  """Returns the text before CurrentColumn."""
  return ToUnicode( vim.current.line[ :CurrentColumn() ] )


# Expects version_string in 'MAJOR.MINOR.PATCH' format, e.g. '7.4.301'
def VimVersionAtLeast( version_string ):
  major, minor, patch = [ int( x ) for x in version_string.split( '.' ) ]

  # For Vim 7.4.301, v:version is '704'
  actual_major_and_minor = GetIntValue( 'v:version' )
  matching_major_and_minor = major * 100 + minor
  if actual_major_and_minor != matching_major_and_minor:
    return actual_major_and_minor > matching_major_and_minor

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


def GetUnsavedAndSpecifiedBufferData( including_filepath ):
  """Build part of the request containing the contents and filetypes of all
  dirty buffers as well as the buffer with filepath |including_filepath|."""
  buffers_data = {}
  for buffer_object in vim.buffers:
    buffer_filepath = GetBufferFilepath( buffer_object )
    if not ( BufferModified( buffer_object ) or
             buffer_filepath == including_filepath ):
      continue

    buffers_data[ buffer_filepath ] = {
      # Add a newline to match what gets saved to disk. See #1455 for details.
      'contents': JoinLinesAsUnicode( buffer_object ) + '\n',
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
  # buffer name so we use the buffer number for that.
  return os.path.join( GetCurrentDirectory(), str( buffer_object.number ) )


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


def AddDiagnosticSyntaxMatch( line_num,
                              column_num,
                              line_end_num = None,
                              column_end_num = None,
                              is_error = True ):
  """Highlight a range in the current window starting from
  (|line_num|, |column_num|) included to (|line_end_num|, |column_end_num|)
  excluded. If |line_end_num| or |column_end_num| are not given, highlight the
  character at (|line_num|, |column_num|). Both line and column numbers are
  1-based. Return the ID of the newly added match."""
  group = 'YcmErrorSection' if is_error else 'YcmWarningSection'

  line_num, column_num = LineAndColumnNumbersClamped( line_num, column_num )

  if not line_end_num or not column_end_num:
    return GetIntValue(
      "matchadd('{0}', '\%{1}l\%{2}c')".format( group, line_num, column_num ) )

  # -1 and then +1 to account for column end not included in the range.
  line_end_num, column_end_num = LineAndColumnNumbersClamped(
      line_end_num, column_end_num - 1 )
  column_end_num += 1

  return GetIntValue(
    "matchadd('{0}', '\%{1}l\%{2}c\_.\\{{-}}\%{3}l\%{4}c')".format(
      group, line_num, column_num, line_end_num, column_end_num ) )


# Clamps the line and column numbers so that they are not past the contents of
# the buffer. Numbers are 1-based byte offsets.
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
  """Populate the location list with diagnostics. Diagnostics should be in
  qflist format; see ":h setqflist" for details."""
  vim.eval( 'setloclist( 0, {0} )'.format( json.dumps( diagnostics ) ) )


def OpenLocationList( focus = False, autoclose = False ):
  """Open the location list to full width at the bottom of the screen with its
  height automatically set to fit all entries. This behavior can be overridden
  by using the YcmLocationOpened autocommand. When focus is set to True, the
  location list window becomes the active window. When autoclose is set to True,
  the location list window is automatically closed after an entry is
  selected."""
  vim.command( 'botright lopen' )

  SetFittingHeightForCurrentWindow()

  if autoclose:
    # This autocommand is automatically removed when the location list window is
    # closed.
    vim.command( 'au WinLeave <buffer> q' )

  if VariableExists( '#User#YcmLocationOpened' ):
    vim.command( 'doautocmd User YcmLocationOpened' )

  if not focus:
    JumpToPreviousWindow()


def SetQuickFixList( quickfix_list ):
  """Populate the quickfix list and open it. List should be in qflist format:
  see ":h setqflist" for details."""
  vim.eval( 'setqflist( {0} )'.format( json.dumps( quickfix_list ) ) )


def OpenQuickFixList( focus = False, autoclose = False ):
  """Open the quickfix list to full width at the bottom of the screen with its
  height automatically set to fit all entries. This behavior can be overridden
  by using the YcmQuickFixOpened autocommand.
  See the OpenLocationList function for the focus and autoclose options."""
  vim.command( 'botright copen' )

  SetFittingHeightForCurrentWindow()

  if autoclose:
    # This autocommand is automatically removed when the quickfix window is
    # closed.
    vim.command( 'au WinLeave <buffer> q' )

  if VariableExists( '#User#YcmQuickFixOpened' ):
    vim.command( 'doautocmd User YcmQuickFixOpened' )

  if not focus:
    JumpToPreviousWindow()


def SetFittingHeightForCurrentWindow():
  window_width = GetIntValue( 'winwidth( 0 )' )
  fitting_height = 0
  for line in vim.current.buffer:
    fitting_height += len( line ) // window_width + 1
  vim.command( '{0}wincmd _'.format( fitting_height ) )


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
      'bufnr' : GetBufferNumberForFilename( location[ 'filepath' ] ),
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
  return bool( int( GetBufferOption( buffer_object, 'hid' ) ) )


def BufferIsUsable( buffer_object ):
  return not BufferModified( buffer_object ) or HiddenEnabled( buffer_object )


def EscapedFilepath( filepath ):
  return filepath.replace( ' ' , r'\ ' )


# Both |line| and |column| need to be 1-based
def TryJumpLocationInOpenedTab( filename, line, column ):
  filepath = os.path.realpath( filename )

  for tab in vim.tabpages:
    for win in tab.windows:
      if win.buffer.name == filepath:
        vim.current.tabpage = tab
        vim.current.window = win
        vim.current.window.cursor = ( line, column - 1 )

        # Center the screen on the jumped-to location
        vim.command( 'normal! zz' )
        return True
  # 'filename' is not opened in any tab pages
  return False


# Maps User command to vim command
def GetVimCommand( user_command, default = 'edit' ):
  vim_command = BUFFER_COMMAND_MAP.get( user_command, default )
  if vim_command == 'edit' and not BufferIsUsable( vim.current.buffer ):
    vim_command = 'split'
  return vim_command


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

    if user_command == 'new-or-existing-tab':
      if TryJumpLocationInOpenedTab( filename, line, column ):
        return
      user_command = 'new-tab'

    vim_command = GetVimCommand( user_command )
    try:
      vim.command( 'keepjumps {0} {1}'.format( vim_command,
                                               EscapedFilepath( filename ) ) )
    # When the file we are trying to jump to has a swap file
    # Vim opens swap-exists-choices dialog and throws vim.error with E325 error,
    # or KeyboardInterrupt after user selects one of the options.
    except vim.error as e:
      if 'E325' not in str( e ):
        raise
      # Do nothing if the target file is still not opened (user chose (Q)uit)
      if filename != GetCurrentBufferFilepath():
        return
    # Thrown when user chooses (A)bort in .swp message box
    except KeyboardInterrupt:
      return
  vim.current.window.cursor = ( line, column - 1 )

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
    if len( message ) > vim_width:
      message = message[ : vim_width - 4 ] + '...'

    old_ruler = GetIntValue( '&ruler' )
    old_showcmd = GetIntValue( '&showcmd' )
    vim.command( 'set noruler noshowcmd' )

    vim.command( "{0} '{1}'".format( echo_command,
                                     EscapeForVim( message ) ) )

    SetVariableValue( '&ruler', old_ruler )
    SetVariableValue( '&showcmd', old_showcmd )
  else:
    for line in message.split( '\n' ):
      vim.command( "{0} '{1}'".format( echo_command,
                                       EscapeForVim( line ) ) )

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
  to_eval = "confirm('{0}', '{1}', {2})".format(
    EscapeForVim( ToUnicode( message ) ),
    EscapeForVim( ToUnicode( "\n" .join( choices ) ) ),
    default_choice_index + 1 )
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

  Returns the 0-based index in the list |items| that the user selected, or a
  negative number if no valid item was selected.

  See also :help inputlist()."""

  vim_items = [ prompt ]
  vim_items.extend( [ "{0}: {1}".format( i + 1, item )
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


def CurrentFiletypes():
  return VimExpressionToPythonType( "&filetype" ).split( '.' )


def FiletypesForBuffer( buffer_object ):
  # NOTE: Getting &ft for other buffers only works when the buffer has been
  # visited by the user at least once, which is true for modified buffers
  return GetBufferOption( buffer_object, 'ft' ).split( '.' )


def VariableExists( variable ):
  return GetBoolValue( "exists( '{0}' )".format( EscapeForVim( variable ) ) )


def SetVariableValue( variable, value ):
  vim.command( "let {0} = {1}".format( variable, json.dumps( value ) ) )


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
        if not BufferIsVisible( GetBufferNumberForFilename( f, False ) ) ] )


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

  buffer_num = GetBufferNumberForFilename( filepath, False )

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
  buffer_num = GetBufferNumberForFilename( filepath, False )
  if not BufferIsVisible( buffer_num ):
    # This happens, for example, if there is a swap file and the user
    # selects the "Quit" or "Abort" options. We just raise an exception to
    # make it clear to the user that the abort has left potentially
    # partially-applied changes.
    raise RuntimeError(
        'Unable to open file: {0}\nFixIt/Refactor operation '
        'aborted prior to completion. Your files have not been '
        'fully updated. Please use undo commands to revert the '
        'applied changes.'.format( filepath ) )

  # We opened this file in a split
  return ( buffer_num, True )


def ReplaceChunks( chunks ):
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

  # We apply the edits file-wise for efficiency, and because we must track the
  # file-wise offset deltas (caused by the modifications to the text).
  chunks_by_file = _SortChunksByFile( chunks )

  # We sort the file list simply to enable repeatable testing
  sorted_file_list = sorted( iterkeys( chunks_by_file ) )

  # Make sure the user is prepared to have her screen mutilated by the new
  # buffers
  num_files_to_open = _GetNumNonVisibleFiles( sorted_file_list )

  if num_files_to_open > 0:
    if not Confirm(
            FIXIT_OPENING_BUFFERS_MESSAGE_FORMAT.format( num_files_to_open ) ):
      return

  # Store the list of locations where we applied changes. We use this to display
  # the quickfix window showing the user where we applied changes.
  locations = []

  for filepath in sorted_file_list:
    ( buffer_num, close_window ) = _OpenFileInSplitIfNeeded( filepath )

    ReplaceChunksInBuffer( chunks_by_file[ filepath ],
                           vim.buffers[ buffer_num ],
                           locations )

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
  if locations:
    SetQuickFixList( locations )
    OpenQuickFixList()

  PostVimMessage( 'Applied {0} changes'.format( len( chunks ) ),
                  warning = False )


def ReplaceChunksInBuffer( chunks, vim_buffer, locations ):
  """Apply changes in |chunks| to the buffer-like object |buffer|. Append each
  chunk's start to the list |locations|"""

  # We need to track the difference in length, but ensuring we apply fixes
  # in ascending order of insertion point.
  chunks.sort( key = lambda chunk: (
    chunk[ 'range' ][ 'start' ][ 'line_num' ],
    chunk[ 'range' ][ 'start' ][ 'column_num' ]
  ) )

  # Remember the line number we're processing. Negative line number means we
  # haven't processed any lines yet (by nature of being not equal to any
  # real line number).
  last_line = -1

  line_delta = 0
  for chunk in chunks:
    if chunk[ 'range' ][ 'start' ][ 'line_num' ] != last_line:
      # If this chunk is on a different line than the previous chunk,
      # then ignore previous deltas (as offsets won't have changed).
      last_line = chunk[ 'range' ][ 'end' ][ 'line_num' ]
      char_delta = 0

    ( new_line_delta, new_char_delta ) = ReplaceChunk(
      chunk[ 'range' ][ 'start' ],
      chunk[ 'range' ][ 'end' ],
      chunk[ 'replacement_text' ],
      line_delta, char_delta,
      vim_buffer,
      locations )
    line_delta += new_line_delta
    char_delta += new_char_delta


# Replace the chunk of text specified by a contiguous range with the supplied
# text.
# * start and end are objects with line_num and column_num properties
# * the range is inclusive
# * indices are all 1-based
# * the returned character delta is the delta for the last line
#
# returns the delta (in lines and characters) that any position after the end
# needs to be adjusted by.
#
# NOTE: Works exclusively with bytes() instances and byte offsets as returned
# by ycmd and used within the Vim buffers
def ReplaceChunk( start, end, replacement_text, line_delta, char_delta,
                  vim_buffer, locations = None ):
  # ycmd's results are all 1-based, but vim's/python's are all 0-based
  # (so we do -1 on all of the values)
  start_line = start[ 'line_num' ] - 1 + line_delta
  end_line = end[ 'line_num' ] - 1 + line_delta

  source_lines_count = end_line - start_line + 1
  start_column = start[ 'column_num' ] - 1 + char_delta
  end_column = end[ 'column_num' ] - 1
  if source_lines_count == 1:
    end_column += char_delta

  # NOTE: replacement_text is unicode, but all our offsets are byte offsets,
  # so we convert to bytes
  replacement_lines = ToBytes( replacement_text ).splitlines( False )
  if not replacement_lines:
    replacement_lines = [ bytes( b'' ) ]
  replacement_lines_count = len( replacement_lines )

  # NOTE: Vim buffers are a list of byte objects on Python 2 but unicode
  # objects on Python 3.
  end_existing_text = ToBytes( vim_buffer[ end_line ] )[ end_column : ]
  start_existing_text = ToBytes( vim_buffer[ start_line ] )[ : start_column ]

  new_char_delta = ( len( replacement_lines[ -1 ] )
                     - ( end_column - start_column ) )
  if replacement_lines_count > 1:
    new_char_delta -= start_column

  replacement_lines[ 0 ] = start_existing_text + replacement_lines[ 0 ]
  replacement_lines[ -1 ] = replacement_lines[ -1 ] + end_existing_text

  vim_buffer[ start_line : end_line + 1 ] = replacement_lines[:]

  if locations is not None:
    locations.append( {
      'bufnr': vim_buffer.number,
      'filename': vim_buffer.name,
      # line and column numbers are 1-based in qflist
      'lnum': start_line + 1,
      'col': start_column + 1,
      'text': replacement_text,
      'type': 'F',
    } )

  new_line_delta = replacement_lines_count - source_lines_count
  return ( new_line_delta, new_char_delta )


def InsertNamespace( namespace ):
  if VariableExists( 'g:ycm_csharp_insert_namespace_expr' ):
    expr = GetVariableValue( 'g:ycm_csharp_insert_namespace_expr' )
    if expr:
      SetVariableValue( "g:ycm_namespace_to_insert", namespace )
      vim.eval( expr )
      return

  pattern = '^\s*using\(\s\+[a-zA-Z0-9]\+\s\+=\)\?\s\+[a-zA-Z0-9.]\+\s*;\s*'
  existing_indent = ''
  line = SearchInCurrentBuffer( pattern )
  if line:
    existing_line = LineTextInCurrentBuffer( line )
    existing_indent = re.sub( r"\S.*", "", existing_line )
  new_line = "{0}using {1};\n\n".format( existing_indent, namespace )
  replace_pos = { 'line_num': line + 1, 'column_num': 1 }
  ReplaceChunk( replace_pos, replace_pos, new_line, 0, 0, vim.current.buffer )
  PostVimMessage( 'Add namespace: {0}'.format( namespace ), warning = False )


def SearchInCurrentBuffer( pattern ):
  """ Returns the 1-indexed line on which the pattern matches
  (going UP from the current position) or 0 if not found """
  return GetIntValue( "search('{0}', 'Wcnb')".format( EscapeForVim( pattern )))


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
  vim.command( 'silent! tabn {0}'.format( tab_number ) )


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

    vim.current.buffer[:] = message.splitlines()

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
  buffer_number = GetBufferNumberForFilename( filename, False )
  return BufferIsVisible( buffer_number )


def CloseBuffersForFilename( filename ):
  """Close all buffers for a specific file."""
  buffer_number = GetBufferNumberForFilename( filename, False )
  while buffer_number != -1:
    vim.command( 'silent! bwipeout! {0}'.format( buffer_number ) )
    new_buffer_number = GetBufferNumberForFilename( filename, False )
    if buffer_number == new_buffer_number:
      raise RuntimeError( "Buffer {0} for filename '{1}' should already be "
                          "wiped out.".format( buffer_number, filename ) )
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
  Choices are start and end."""

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
    vim.command( '{0}{1} {2}'.format( size, command, filename ) )
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

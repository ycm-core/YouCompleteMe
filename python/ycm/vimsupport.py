#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
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


def TextAfterCursor():
  """Returns the text after CurrentColumn."""
  return vim.current.line[ CurrentColumn(): ]


# Note the difference between buffer OPTIONS and VARIABLES; the two are not
# the same.
def GetBufferOption( buffer_object, option ):
  # The 'options' property is only available in recent (7.4+) Vim builds
  if hasattr( buffer_object, 'options' ):
    return buffer_object.options[ option ]

  to_eval = 'getbufvar({0}, "&{1}")'.format( buffer_object.number, option )
  return GetVariableValue( to_eval )


def GetUnsavedAndCurrentBufferData():
  def BufferModified( buffer_object ):
    return bool( int( GetBufferOption( buffer_object, 'mod' ) ) )

  buffers_data = {}
  for buffer_object in vim.buffers:
    if not ( BufferModified( buffer_object ) or
             buffer_object == vim.current.buffer ):
      continue

    buffers_data[ buffer_object.name ] = {
      'contents': '\n'.join( buffer_object ),
      'filetypes': FiletypesForBuffer( buffer_object )
    }

  return buffers_data


# Both |line| and |column| need to be 1-based
def JumpToLocation( filename, line, column ):
  # Add an entry to the jumplist
  vim.command( "normal! m'" )

  if filename != vim.current.buffer.name:
    # We prefix the command with 'keepjumps' so that opening the file is not
    # recorded in the jumplist. So when we open the file and move the cursor to
    # a location in it, the user can use CTRL-O to jump back to the original
    # location, not to the start of the newly opened file.
    # Sadly this fails on random occasions and the undesired jump remains in the
    # jumplist.
    vim.command( 'keepjumps edit {0}'.format( filename ) )
  vim.current.window.cursor = ( line, column - 1 )

  # Center the screen on the jumped-to location
  vim.command( 'normal! zz' )


def NumLinesInBuffer( buffer_object ):
  # This is actually less than obvious, that's why it's wrapped in a function
  return len( buffer_object )


def PostVimMessage( message ):
  # TODO: Check are we on the main thread or not, and if not, force a crash
  # here. This should make it impossible to accidentally call this from a
  # non-GUI thread which *sometimes* crashes Vim because Vim is not thread-safe.
  # A consistent crash should force us to notice the error.
  vim.command( "echohl WarningMsg | echomsg '{0}' | echohl None"
               .format( EscapeForVim( message ) ) )


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


def EchoText( text ):
  def EchoLine( text ):
    vim.command( "echom '{0}'".format( EscapeForVim( text ) ) )

  for line in text.split( '\n' ):
    EchoLine( line )


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

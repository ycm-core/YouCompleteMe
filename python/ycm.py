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

import re
import vim
import indexer

min_num_chars = int( vim.eval( "g:ycm_min_num_of_chars_for_completion" ) )


class CompletionSystem( object ):
  def __init__( self ):
    self.completer = indexer.Completer()
    self.completer.EnableThreading()
    self.pattern = re.compile( r"[_a-zA-Z]\w*" )
    self.future = None


  def CandidatesForQueryAsync( self, query ):
    filetype = vim.eval( "&filetype" )
    self.future = self.completer.CandidatesForQueryAndTypeAsync(
      SanitizeQuery( query ),
      filetype )


  def AsyncCandidateRequestReady( self ):
    return self.future.ResultsReady()


  def CandidatesFromStoredRequest( self ):
    if not self.future:
      return []

    return self.future.GetResults()


  def AddIdentifier( self, identifier ):
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )

    if not filetype or not filepath or not identifier:
      return

    vector = indexer.StringVec()
    vector.append( identifier )
    self.completer.AddCandidatesToDatabase( vector,
                                            filetype,
                                            filepath,
                                            False )


  def AddPreviousIdentifier( self ):
    self.AddIdentifier( PreviousIdentifier() )


  def AddBufferIdentifiers( self ):
    text = "\n".join( vim.current.buffer )
    text = RemoveIdentFreeText( text )

    idents = re.findall( self.pattern, text )
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )

    if not filetype or not filepath:
      return

    vector = indexer.StringVec()
    vector.extend( idents )
    self.completer.AddCandidatesToDatabase( vector,
                                            filetype,
                                            filepath,
                                            True )


def CurrentColumn():
  """Do NOT access the CurrentColumn in vim.current.line. It doesn't exist yet.
  Only the chars befor the current column exist in vim.current.line."""

  # vim's columns start at 1 while vim.current.line columns start at 0
  return int( vim.eval( "col('.')" ) ) - 1


def CurrentLineAndColumn():
  result = vim.eval( "getpos('.')")
  line_num = int( result[ 1 ] ) - 1
  column_num = int( result[ 2 ] ) - 1
  return line_num, column_num


def IsIdentifierChar( char ):
  return char.isalnum() or char == '_'


def CompletionStartColumn():
  line = vim.current.line
  current_column = CurrentColumn()
  start_column = current_column

  while start_column > 0 and IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1

  if current_column - start_column < min_num_chars:
    # for vim, -2 means not found but don't trigger an error message
    # see :h complete-functions
    return -2

  return start_column


def EscapeForVim( text ):
  return text.replace( "'", "''" )


def PreviousIdentifier():
  line_num, column_num = CurrentLineAndColumn()
  buffer = vim.current.buffer
  line = buffer[ line_num ]

  end_column = column_num

  while end_column > 0 and not IsIdentifierChar( line[ end_column - 1 ] ):
    end_column -= 1

  # Look at the previous line if we reached the end of the current one
  if end_column == 0:
    try:
      line = buffer[ line_num - 1]
    except:
      return ""
    end_column = len( line )
    while end_column > 0 and not IsIdentifierChar( line[ end_column - 1 ] ):
      end_column -= 1
    print end_column, line

  start_column = end_column
  while start_column > 0 and IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1

  if end_column - start_column < min_num_chars:
    return ""

  return line[ start_column : end_column ]


def CurrentCursorText():
  start_column = CompletionStartColumn()
  current_column = CurrentColumn()

  if current_column - start_column < min_num_chars:
    return ""

  return vim.current.line[ start_column : current_column ]


def CurrentCursorTextVim():
  return EscapeForVim( CurrentCursorText() )


def ShouldAddIdentifier():
  current_column = CurrentColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return True
  line = vim.current.line
  try:
    previous_char = line[ previous_char_index ]
  except IndexError:
    return False

  if IsIdentifierChar( previous_char ):
    return False

  if ( not IsIdentifierChar( previous_char ) and
       previous_char_index > 0 and
       IsIdentifierChar( line[ previous_char_index - 1 ] ) ):
    return True
  else:
    return line[ : current_column ].isspace()


def SanitizeQuery( query ):
  return query.strip()


def RemoveIdentFreeText( text ):
  """Removes commented-out code and code in quotes."""

  # TODO: do we still need this sub-func?
  def replacer( match ):
    s = match.group( 0 )
    if s.startswith( '/' ):
      return ""
    else:
      return s

  pattern = re.compile(
    r'//.*?$|#.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE )

  return re.sub( pattern, replacer, text )


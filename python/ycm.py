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
    self.pattern = re.compile( r"[_a-zA-Z]\w*" )

  def CompletionCandidatesForQuery( self, query ):
    candidates = []
    self.completer.GetCandidatesForQuery( SanitizeQuery( query ), candidates )
    return candidates

  def AddBufferIdentifiers( self ):
    text = "\n".join( vim.current.buffer )
    text = RemoveIdentFreeText( text )

    idents = re.findall( self.pattern, text )
    filepath = vim.eval( "expand('%:p')" )
    self.completer.AddCandidatesToDatabase( idents, filepath )

def CurrentColumn():
  # vim's columns start at 1 while vim.current.line columns start at 0
  return int( vim.eval( "col('.')" ) ) - 1

def CompletionStartColumn():
  line = vim.current.line
  current_column = CurrentColumn()
  start_column = current_column

  while start_column > 0 and line[ start_column - 1 ].isalnum():
    start_column -= 1

  if current_column - start_column < min_num_chars:
    return -1

  return start_column

def EscapeForVim( text ):
  return text.replace( "'", "''" )

def CurrentCursorText():
  start_column = CompletionStartColumn()
  current_column = CurrentColumn()

  if current_column - start_column < min_num_chars:
    return ""

  cursor_text = vim.current.line[ start_column : current_column ]
  return EscapeForVim( cursor_text )


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


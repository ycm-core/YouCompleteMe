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

from completers.completer import Completer
import vim
import vimsupport
import ycm_core
import ycm_utils as utils

MAX_IDENTIFIER_COMPLETIONS_RETURNED = 10
MIN_NUM_CHARS = int( vimsupport.GetVariableValue(
  "g:ycm_min_num_of_chars_for_completion" ) )


class IdentifierCompleter( Completer ):
  def __init__( self ):
    super( IdentifierCompleter, self ).__init__()
    self.completer = ycm_core.IdentifierCompleter()
    self.completer.EnableThreading()


  def SupportedFiletypes( self ):
    # magic token meaning all filetypes
    return set( [ 'ycm_all' ] )


  def ShouldUseNow( self, start_column ):
    query_length = vimsupport.CurrentColumn() - start_column
    return query_length >= MIN_NUM_CHARS


  def CandidatesForQueryAsync( self, query ):
    filetype = vim.eval( "&filetype" )
    self.completions_future = self.completer.CandidatesForQueryAndTypeAsync(
      utils.SanitizeQuery( query ),
      filetype )


  def AddIdentifier( self, identifier ):
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )

    if not filetype or not filepath or not identifier:
      return

    vector = ycm_core.StringVec()
    vector.append( identifier )
    self.completer.AddCandidatesToDatabase( vector,
                                            filetype,
                                            filepath )


  def AddPreviousIdentifier( self ):
    self.AddIdentifier( PreviousIdentifier() )


  def AddIdentifierUnderCursor( self ):
    cursor_identifier = vim.eval( 'expand("<cword>")' )
    if not cursor_identifier:
      return

    stripped_cursor_identifier = ''.join( ( x for x in
                                            cursor_identifier if
                                            utils.IsIdentifierChar( x ) ) )
    if not stripped_cursor_identifier:
      return

    self.AddIdentifier( stripped_cursor_identifier )


  def AddBufferIdentifiers( self ):
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )
    collect_from_comments_and_strings = vimsupport.GetBoolValue(
      "g:ycm_collect_identifiers_from_comments_and_strings" )

    if not filetype or not filepath:
      return

    text = "\n".join( vim.current.buffer )
    self.completer.AddCandidatesToDatabaseFromBufferAsync(
      text,
      filetype,
      filepath,
      collect_from_comments_and_strings )


  def OnFileReadyToParse( self ):
    self.AddBufferIdentifiers()


  def OnInsertLeave( self ):
    self.AddIdentifierUnderCursor()


  def OnCurrentIdentifierFinished( self ):
    self.AddPreviousIdentifier()


  def CandidatesFromStoredRequest( self ):
    if not self.completions_future:
      return []
    completions = self.completions_future.GetResults()[
      : MAX_IDENTIFIER_COMPLETIONS_RETURNED ]

    # We will never have duplicates in completions so with 'dup':1 we tell Vim
    # to add this candidate even if it's a duplicate of an existing one (which
    # will never happen). This saves us some expensive string matching
    # operations in Vim.
    return [ { 'word': x, 'dup': 1 } for x in completions ]


def PreviousIdentifier():
  line_num, column_num = vimsupport.CurrentLineAndColumn()
  buffer = vim.current.buffer
  line = buffer[ line_num ]

  end_column = column_num

  while end_column > 0 and not utils.IsIdentifierChar( line[ end_column - 1 ] ):
    end_column -= 1

  # Look at the previous line if we reached the end of the current one
  if end_column == 0:
    try:
      line = buffer[ line_num - 1]
    except:
      return ""
    end_column = len( line )
    while end_column > 0 and not utils.IsIdentifierChar(
      line[ end_column - 1 ] ):
      end_column -= 1

  start_column = end_column
  while start_column > 0 and utils.IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1

  if end_column - start_column < MIN_NUM_CHARS:
    return ""

  return line[ start_column : end_column ]


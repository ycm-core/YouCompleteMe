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

import os
import vim
import ycm_core
from collections import defaultdict
from ycm.completers.general_completer import GeneralCompleter
from ycm.completers.general import syntax_parse
from ycm import vimsupport
from ycm import utils

MAX_IDENTIFIER_COMPLETIONS_RETURNED = 10
SYNTAX_FILENAME = 'YCM_PLACEHOLDER_FOR_SYNTAX'


class IdentifierCompleter( GeneralCompleter ):
  def __init__( self, user_options ):
    super( IdentifierCompleter, self ).__init__( user_options )
    self.completer = ycm_core.IdentifierCompleter()
    self.completer.EnableThreading()
    self.tags_file_last_mtime = defaultdict( int )
    self.filetypes_with_keywords_loaded = set()


  def ShouldUseNow( self, start_column, unused_current_line ):
    return self.QueryLengthAboveMinThreshold( start_column )


  def CandidatesForQueryAsync( self, query, unused_start_column ):
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
    self.completer.AddIdentifiersToDatabase( vector,
                                             filetype,
                                             filepath )


  def AddPreviousIdentifier( self ):
    self.AddIdentifier( _PreviousIdentifier( self.user_options[
      'min_num_of_chars_for_completion' ] ) )


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
    # TODO: use vimsupport.GetFiletypes; also elsewhere in file
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )
    collect_from_comments_and_strings = bool( self.user_options[
      'collect_identifiers_from_comments_and_strings' ] )

    if not filetype or not filepath:
      return

    text = "\n".join( vim.current.buffer )
    self.completer.AddIdentifiersToDatabaseFromBufferAsync(
      text,
      filetype,
      filepath,
      collect_from_comments_and_strings )


  def AddIdentifiersFromTagFiles( self ):
    tag_files = vim.eval( 'tagfiles()' )
    current_working_directory = os.getcwd()
    absolute_paths_to_tag_files = ycm_core.StringVec()
    for tag_file in tag_files:
      absolute_tag_file = os.path.join( current_working_directory,
                                        tag_file )
      try:
        current_mtime = os.path.getmtime( absolute_tag_file )
      except:
        continue
      last_mtime = self.tags_file_last_mtime[ absolute_tag_file ]

      # We don't want to repeatedly process the same file over and over; we only
      # process if it's changed since the last time we looked at it
      if current_mtime <= last_mtime:
        continue

      self.tags_file_last_mtime[ absolute_tag_file ] = current_mtime
      absolute_paths_to_tag_files.append( absolute_tag_file )

    if not absolute_paths_to_tag_files:
      return

    self.completer.AddIdentifiersToDatabaseFromTagFilesAsync(
      absolute_paths_to_tag_files )


  def AddIdentifiersFromSyntax( self ):
    filetype = vim.eval( "&filetype" )
    if filetype in self.filetypes_with_keywords_loaded:
      return

    self.filetypes_with_keywords_loaded.add( filetype )

    keyword_set = syntax_parse.SyntaxKeywordsForCurrentBuffer()
    keywords = ycm_core.StringVec()
    for keyword in keyword_set:
      keywords.append( keyword )

    filepath = SYNTAX_FILENAME + filetype
    self.completer.AddIdentifiersToDatabase( keywords,
                                             filetype,
                                             filepath )


  def OnFileReadyToParse( self ):
    self.AddBufferIdentifiers()

    if self.user_options[ 'collect_identifiers_from_tags_files' ]:
      self.AddIdentifiersFromTagFiles()

    if self.user_options[ 'seed_identifiers_with_syntax' ]:
      self.AddIdentifiersFromSyntax()


  def OnInsertLeave( self ):
    self.AddIdentifierUnderCursor()


  def OnCurrentIdentifierFinished( self ):
    self.AddPreviousIdentifier()


  def CandidatesFromStoredRequest( self ):
    if not self.completions_future:
      return []
    completions = self.completions_future.GetResults()[
      : MAX_IDENTIFIER_COMPLETIONS_RETURNED ]

    completions = _RemoveSmallCandidates(
      completions, self.user_options[ 'min_num_identifier_candidate_chars' ] )

    # We will never have duplicates in completions so with 'dup':1 we tell Vim
    # to add this candidate even if it's a duplicate of an existing one (which
    # will never happen). This saves us some expensive string matching
    # operations in Vim.
    return [ { 'word': x, 'dup': 1 } for x in completions ]


def _PreviousIdentifier( min_num_completion_start_chars ):
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

  if end_column - start_column < min_num_completion_start_chars:
    return ""

  return line[ start_column : end_column ]


def _RemoveSmallCandidates( candidates, min_num_candidate_size_chars ):
  if min_num_candidate_size_chars == 0:
    return candidates

  return [ x for x in candidates if len( x ) >= min_num_candidate_size_chars ]


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

import os
import logging
import ycm_core
from collections import defaultdict
from ycmd.completers.general_completer import GeneralCompleter
from ycmd import utils
from ycmd.utils import ToUtf8IfNeeded
from ycmd import responses

MAX_IDENTIFIER_COMPLETIONS_RETURNED = 10
SYNTAX_FILENAME = 'YCM_PLACEHOLDER_FOR_SYNTAX'


class IdentifierCompleter( GeneralCompleter ):
  def __init__( self, user_options ):
    super( IdentifierCompleter, self ).__init__( user_options )
    self._completer = ycm_core.IdentifierCompleter()
    self._tags_file_last_mtime = defaultdict( int )
    self._logger = logging.getLogger( __name__ )


  def ShouldUseNow( self, request_data ):
    return self.QueryLengthAboveMinThreshold( request_data )


  def ComputeCandidates( self, request_data ):
    if not self.ShouldUseNow( request_data ):
      return []

    completions = self._completer.CandidatesForQueryAndType(
      ToUtf8IfNeeded( utils.SanitizeQuery( request_data[ 'query' ] ) ),
      ToUtf8IfNeeded( request_data[ 'filetypes' ][ 0 ] ) )

    completions = completions[ : MAX_IDENTIFIER_COMPLETIONS_RETURNED ]
    completions = _RemoveSmallCandidates(
      completions, self.user_options[ 'min_num_identifier_candidate_chars' ] )

    return [ responses.BuildCompletionData( x ) for x in completions ]


  def AddIdentifier( self, identifier, request_data ):
    filetype = request_data[ 'filetypes' ][ 0 ]
    filepath = request_data[ 'filepath' ]

    if not filetype or not filepath or not identifier:
      return

    vector = ycm_core.StringVec()
    vector.append( ToUtf8IfNeeded( identifier ) )
    self._logger.info( 'Adding ONE buffer identifier for file: %s', filepath )
    self._completer.AddIdentifiersToDatabase( vector,
                                             ToUtf8IfNeeded( filetype ),
                                             ToUtf8IfNeeded( filepath ) )


  def AddPreviousIdentifier( self, request_data ):
    self.AddIdentifier(
      _PreviousIdentifier(
        self.user_options[ 'min_num_of_chars_for_completion' ],
        request_data ),
      request_data )


  def AddIdentifierUnderCursor( self, request_data ):
    cursor_identifier = _GetCursorIdentifier( request_data )
    if not cursor_identifier:
      return

    self.AddIdentifier( cursor_identifier, request_data )


  def AddBufferIdentifiers( self, request_data ):
    filetype = request_data[ 'filetypes' ][ 0 ]
    filepath = request_data[ 'filepath' ]
    collect_from_comments_and_strings = bool( self.user_options[
      'collect_identifiers_from_comments_and_strings' ] )

    if not filetype or not filepath:
      return

    text = request_data[ 'file_data' ][ filepath ][ 'contents' ]
    self._logger.info( 'Adding buffer identifiers for file: %s', filepath )
    self._completer.AddIdentifiersToDatabaseFromBuffer(
      ToUtf8IfNeeded( text ),
      ToUtf8IfNeeded( filetype ),
      ToUtf8IfNeeded( filepath ),
      collect_from_comments_and_strings )


  def AddIdentifiersFromTagFiles( self, tag_files ):
    absolute_paths_to_tag_files = ycm_core.StringVec()
    for tag_file in tag_files:
      try:
        current_mtime = os.path.getmtime( tag_file )
      except:
        continue
      last_mtime = self._tags_file_last_mtime[ tag_file ]

      # We don't want to repeatedly process the same file over and over; we only
      # process if it's changed since the last time we looked at it
      if current_mtime <= last_mtime:
        continue

      self._tags_file_last_mtime[ tag_file ] = current_mtime
      absolute_paths_to_tag_files.append( ToUtf8IfNeeded( tag_file ) )

    if not absolute_paths_to_tag_files:
      return

    self._completer.AddIdentifiersToDatabaseFromTagFiles(
      absolute_paths_to_tag_files )


  def AddIdentifiersFromSyntax( self, keyword_list, filetypes ):
    keyword_vector = ycm_core.StringVec()
    for keyword in keyword_list:
      keyword_vector.append( ToUtf8IfNeeded( keyword ) )

    filepath = SYNTAX_FILENAME + filetypes[ 0 ]
    self._completer.AddIdentifiersToDatabase( keyword_vector,
                                             ToUtf8IfNeeded( filetypes[ 0 ] ),
                                             ToUtf8IfNeeded( filepath ) )


  def OnFileReadyToParse( self, request_data ):
    self.AddBufferIdentifiers( request_data )
    if 'tag_files' in request_data:
      self.AddIdentifiersFromTagFiles( request_data[ 'tag_files' ] )
    if 'syntax_keywords' in request_data:
      self.AddIdentifiersFromSyntax( request_data[ 'syntax_keywords' ],
                                     request_data[ 'filetypes' ] )


  def OnInsertLeave( self, request_data ):
    self.AddIdentifierUnderCursor( request_data )


  def OnCurrentIdentifierFinished( self, request_data ):
    self.AddPreviousIdentifier( request_data )


def _PreviousIdentifier( min_num_completion_start_chars, request_data ):
  line_num = request_data[ 'line_num' ] - 1
  column_num = request_data[ 'column_num' ] - 1
  filepath = request_data[ 'filepath' ]
  contents_per_line = (
    request_data[ 'file_data' ][ filepath ][ 'contents' ].split( '\n' ) )
  line = contents_per_line[ line_num ]

  end_column = column_num

  while end_column > 0 and not utils.IsIdentifierChar( line[ end_column - 1 ] ):
    end_column -= 1

  # Look at the previous line if we reached the end of the current one
  if end_column == 0:
    try:
      line = contents_per_line[ line_num - 1 ]
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


# This is meant to behave like 'expand("<cword")' in Vim, thus starting at the
# cursor column and returning the "cursor word". If the cursor is not on a valid
# character, it searches forward until a valid identifier is found.
def _GetCursorIdentifier( request_data ):
  def FindFirstValidChar( line, column ):
    current_column = column
    while not utils.IsIdentifierChar( line[ current_column ] ):
      current_column += 1
    return current_column


  def FindIdentifierStart( line, valid_char_column ):
    identifier_start = valid_char_column
    while identifier_start > 0 and utils.IsIdentifierChar( line[
      identifier_start - 1 ] ):
      identifier_start -= 1
    return identifier_start


  def FindIdentifierEnd( line, valid_char_column ):
    identifier_end = valid_char_column
    while identifier_end < len( line ) - 1 and utils.IsIdentifierChar( line[
      identifier_end + 1 ] ):
      identifier_end += 1
    return identifier_end + 1

  column_num = request_data[ 'column_num' ] - 1
  line = request_data[ 'line_value' ]

  try:
    valid_char_column = FindFirstValidChar( line, column_num )
    return line[ FindIdentifierStart( line, valid_char_column ) :
                 FindIdentifierEnd( line, valid_char_column ) ]
  except:
    return ''


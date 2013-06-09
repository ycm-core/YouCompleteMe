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
import re
import ycm_core
from collections import defaultdict
from ycm.completers.general_completer import GeneralCompleter
from ycm.completers.general import syntax_parse
from ycm import vimsupport
from ycm import utils

MAX_IDENTIFIER_COMPLETIONS_RETURNED = 10
MIN_NUM_CHARS = int( vimsupport.GetVariableValue(
  "g:ycm_min_num_of_chars_for_completion" ) )
SYNTAX_FILENAME = 'YCM_PLACEHOLDER_FOR_SYNTAX'
DISTANCE_RANGE = 10000

class IdentifierCompleter( GeneralCompleter ):
  def __init__( self ):
    super( IdentifierCompleter, self ).__init__()
    self.completer = ycm_core.IdentifierCompleter()
    self.completer.EnableThreading()
    self.tags_file_last_mtime = defaultdict( int )
    self.filetypes_with_keywords_loaded = set()
    self.identifier_regex = re.compile( "[_a-zA-Z]\\w*" )


  def ShouldUseNow( self, start_column ):
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
    # TODO: use vimsupport.GetFiletypes; also elsewhere in file
    filetype = vim.eval( "&filetype" )
    filepath = vim.eval( "expand('%:p')" )
    collect_from_comments_and_strings = vimsupport.GetBoolValue(
      "g:ycm_collect_identifiers_from_comments_and_strings" )

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

    if vimsupport.GetBoolValue( 'g:ycm_collect_identifiers_from_tags_files' ):
      self.AddIdentifiersFromTagFiles()

    if vimsupport.GetBoolValue( 'g:ycm_seed_identifiers_with_syntax' ):
      self.AddIdentifiersFromSyntax()


  def OnInsertLeave( self ):
    self.AddIdentifierUnderCursor()


  def OnCurrentIdentifierFinished( self ):
    self.AddPreviousIdentifier()

  def CandidatesFromStoredRequest( self ):
    if not self.completions_future:
      return []

    lines = vim.current.buffer
    line_num, cursor = vimsupport.CurrentLineAndColumn()

    for i in range( 0, line_num - 1 ):
      cursor += len( lines[ i ] ) + 1 # that +1 is for the "\n" char

    count = 0
    positions = {}
    text = "\n".join( lines )

    if cursor > DISTANCE_RANGE:
      text = text[ cursor - DISTANCE_RANGE : ]
      cursor = DISTANCE_RANGE

    if len(text) > cursor + DISTANCE_RANGE:
      text = text[ : cursor + DISTANCE_RANGE ]

    for match in self.identifier_regex.finditer( text ):
      count += 1
      identifier = match.group()
      position = match.start() + ( len( identifier ) / 2 )
      if identifier in positions:
        positions[ identifier ].append( position )
      else:
        positions[ identifier ] = [ position ]

    completions = self.completions_future.GetResults() # all

    completions_with_distance = []
    rest = []

    for word in completions:
      if word in positions:
        distance = min( [ abs( cursor - pos ) for pos in positions[ word ] ] )
        count_factor = ( len( positions[ word ] ) ) / float( count )
        distance -= distance * count_factor
        completions_with_distance.append( ( word, distance ) )
      else:
        rest.append( word )

    sorted_completions = sorted( completions_with_distance,
                                 key=lambda pair: pair[ 1 ] )
    completions = [ pair[ 0 ] for pair in sorted_completions ] + rest

    # We will never have duplicates in completions so with 'dup':1 we tell Vim
    # to add this candidate even if it's a duplicate of an existing one (which
    # will never happen). This saves us some expensive string matching
    # operations in Vim.
    return [ { 'word': x, 'dup': 1 } for x in completions[
        : MAX_IDENTIFIER_COMPLETIONS_RETURNED ] ]


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


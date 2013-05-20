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

import abc
import vim
import ycm_core
from ycm import vimsupport
from collections import defaultdict

NO_USER_COMMANDS = 'This completer does not define any commands.'

MIN_NUM_CHARS = int( vimsupport.GetVariableValue(
  "g:ycm_min_num_of_chars_for_completion" ) )

class Completer( object ):
  """A base class for all Completers in YCM.

  Here's several important things you need to know if you're writing a custom
  Completer. The following are functions that the Vim part of YCM will be
  calling on your Completer:

  ShouldUseNow() is called with the start column of where a potential completion
  string should start. For instance, if the user's input is 'foo.bar' and the
  cursor is on the 'r' in 'bar', start_column will be the 0-based index of 'b'
  in the line. Your implementation of ShouldUseNow() should return True if your
  semantic completer should be used and False otherwise.

  This is important to get right. You want to return False if you can't provide
  completions because then the identifier completer will kick in, and that's
  better than nothing.

  Note that it's HIGHLY likely that you want to override the ShouldUseNowInner()
  function instead of ShouldUseNow() directly (although chances are that you
  probably won't have any need to override either). ShouldUseNow() will call
  your *Inner version of the function and will also make sure that the
  completion cache is taken into account. You'll see this pattern repeated
  throughout the Completer API; YCM calls the "main" version of the function and
  that function calls the *Inner version while taking into account the cache.

  The cache is important and is a nice performance boost. When the user types in
  "foo.", your completer will return a list of all member functions and
  variables that can be accessed on the "foo" object. The Completer API caches
  this list. The user will then continue typing, let's say "foo.ba". On every
  keystroke after the dot, the Completer API will take the cache into account
  and will NOT re-query your completer but will in fact provide fuzzy-search on
  the candidate strings that were stored in the cache.

  CandidatesForQueryAsync() is the main entry point when the user types. For
  "foo.bar", the user query is "bar" and completions matching this string should
  be shown. The job of CandidatesForQueryAsync() is to merely initiate this
  request, which will hopefully be processed in a background thread.

  AsyncCandidateRequestReady() is the function that is repeatedly polled until
  it returns True. If CandidatesForQueryAsync() started a background task of
  collecting the required completions, AsyncCandidateRequestReady() would check
  the state of that task and return False until it was completed.

  CandidatesFromStoredRequest() should return the list of candidates. This is
  what YCM calls after AsyncCandidateRequestReady() returns True. The format of
  the result can be a list of strings or a more complicated list of
  dictionaries. See ':h complete-items' for the format, and clang_completer.py
  to see how its used in practice.

  You also need to implement the SupportedFiletypes() function which should
  return a list of strings, where the strings are Vim filetypes your completer
  supports.

  clang_completer.py is a good example of a "complicated" completer that
  maintains its own internal cache and therefore directly overrides the "main"
  functions in the API instead of the *Inner versions. A good example of a
  simple completer that does not do this is omni_completer.py.

  If you're confident your completer doesn't need a background task (think
  again, you probably do) because you can "certainly" furnish a response in
  under 10ms, then you can perform your backend processing in a synchronous
  fashion. You may also need to do this because of technical restrictions (much
  like omni_completer.py has to do it because accessing Vim internals is not
  thread-safe). But even if you're certain, still try to do the processing in a
  background thread. Your completer is unlikely to be merged if it does not,
  because synchronous processing will block Vim's GUI thread and that's a very,
  VERY bad thing (so try not to do it!).

  The On* functions are provided for your convenience. They are called when
  their specific events occur. For instance, the identifier completer collects
  all the identifiers in the file in OnFileReadyToParse() which gets called when
  the user stops typing for 2 seconds (Vim's CursorHold and CursorHoldI events).

  One special function is OnUserCommand. It is called when the user uses the
  command :YcmCompleter and is passed all extra arguments used on command
  invocation (e.g. OnUserCommand(['first argument', 'second'])).  This can be
  used for completer-specific commands such as reloading external
  configuration.
  When the command is called with no arguments you should print a short summary
  of the supported commands or point the user to the help section where this
  information can be found."""

  __metaclass__ = abc.ABCMeta

  def __init__( self ):
    self.triggers_for_filetype = TriggersForFiletype()
    self.completions_future = None
    self.completions_cache = None
    self.completion_start_column = None


  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def ShouldUseNow( self, start_column ):
    inner_says_yes = self.ShouldUseNowInner( start_column )
    if not inner_says_yes:
      self.completions_cache = None

    previous_results_were_empty = ( self.completions_cache and
                                    self.completions_cache.CacheValid(
                                      start_column ) and
                                    not self.completions_cache.raw_completions )
    return inner_says_yes and not previous_results_were_empty


  def ShouldUseNowInner( self, start_column ):
    line = vim.current.line
    line_length = len( line )
    if not line_length or start_column - 1 >= line_length:
      return False

    filetype = self._CurrentFiletype()
    triggers = self.triggers_for_filetype[ filetype ]

    for trigger in triggers:
      index = -1
      trigger_length = len( trigger )
      while True:
        line_index = start_column + index
        if line_index < 0 or line[ line_index ] != trigger[ index ]:
          break

        if abs( index ) == trigger_length:
          return True
        index -= 1
    return False


  def QueryLengthAboveMinThreshold( self, start_column ):
    query_length = vimsupport.CurrentColumn() - start_column
    return query_length >= MIN_NUM_CHARS

  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def CandidatesForQueryAsync( self, query, start_column ):
    self.completion_start_column = start_column

    if query and self.completions_cache and self.completions_cache.CacheValid(
      start_column ):
      self.completions_cache.filtered_completions = (
        self.FilterAndSortCandidates(
          self.completions_cache.raw_completions,
          query ) )
    else:
      self.completions_cache = None
      self.CandidatesForQueryAsyncInner( query, start_column )


  def DefinedSubcommands( self ):
    return []


  def EchoUserCommandsHelpMessage( self ):
    subcommands = self.DefinedSubcommands()
    if subcommands:
      vimsupport.EchoText( 'Supported commands are:\n' +
                           '\n'.join( subcommands ) +
                           '\nSee the docs for information on what they do.' )
    else:
      vimsupport.EchoText( 'No supported subcommands' )


  def FilterAndSortCandidates( self, candidates, query ):
    if not candidates:
      return []

    if hasattr( candidates, 'words' ):
      candidates = candidates.words
    items_are_objects = 'word' in candidates[ 0 ]

    matches = ycm_core.FilterAndSortCandidates(
      candidates,
      'word' if items_are_objects else '',
      query )

    return matches


  def CandidatesForQueryAsyncInner( self, query, start_column ):
    pass


  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def AsyncCandidateRequestReady( self ):
    if self.completions_cache:
      return True
    else:
      return self.AsyncCandidateRequestReadyInner()


  def AsyncCandidateRequestReadyInner( self ):
    if not self.completions_future:
      # We return True so that the caller can extract the default value from the
      # future
      return True
    return self.completions_future.ResultsReady()


  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def CandidatesFromStoredRequest( self ):
    if self.completions_cache:
      return self.completions_cache.filtered_completions
    else:
      self.completions_cache = CompletionsCache()
      self.completions_cache.raw_completions = self.CandidatesFromStoredRequestInner()
      self.completions_cache.line, _ = vimsupport.CurrentLineAndColumn()
      self.completions_cache.column = self.completion_start_column
      return self.completions_cache.raw_completions


  def CandidatesFromStoredRequestInner( self ):
    if not self.completions_future:
      return []
    return self.completions_future.GetResults()


  def OnFileReadyToParse( self ):
    pass


  def OnCursorMovedInsertMode( self ):
    pass


  def OnCursorMovedNormalMode( self ):
    pass


  def OnBufferVisit( self ):
    pass


  def OnBufferUnload( self, deleted_buffer_file ):
    pass


  def OnCursorHold( self ):
    pass


  def OnInsertLeave( self ):
    pass


  def OnUserCommand( self, arguments ):
    vimsupport.PostVimMessage( NO_USER_COMMANDS )


  def OnCurrentIdentifierFinished( self ):
    pass


  def DiagnosticsForCurrentFileReady( self ):
    return False


  def GetDiagnosticsForCurrentFile( self ):
    return []


  def ShowDetailedDiagnostic( self ):
    pass


  def GettingCompletions( self ):
    return False


  def _CurrentFiletype( self ):
    filetypes = vimsupport.CurrentFiletypes()
    supported = self.SupportedFiletypes()

    for filetype in filetypes:
      if filetype in supported:
        return filetype

    return filetypes[0]


  @abc.abstractmethod
  def SupportedFiletypes( self ):
    pass


  def DebugInfo( self ):
    return ''


class CompletionsCache( object ):
  def __init__( self ):
    self.line = -1
    self.column = -1
    self.raw_completions = []
    self.filtered_completions = []


  def CacheValid( self, start_column ):
    completion_line, _ = vimsupport.CurrentLineAndColumn()
    completion_column = start_column
    return completion_line == self.line and completion_column == self.column


def TriggersForFiletype():
  triggers = vim.eval( 'g:ycm_semantic_triggers' )
  triggers_for_filetype = defaultdict( list )

  for key, value in triggers.iteritems():
    filetypes = key.split( ',' )
    for filetype in filetypes:
      triggers_for_filetype[ filetype ].extend( value )

  return triggers_for_filetype


#!/usr/bin/env python
#
# Copyright (C) 2011, 2012, 2013  Google Inc.
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
import threading
from collections import defaultdict
from ycm.utils import ToUtf8IfNeeded, ForceSemanticCompletion, RunningInsideVim

if RunningInsideVim():
  from ycm_client_support import FilterAndSortCandidates
else:
  from ycm_core import FilterAndSortCandidates

from ycm.completers.completer_utils import TriggersForFiletype
from ycm.server.responses import NoDiagnosticSupport

NO_USER_COMMANDS = 'This completer does not define any commands.'

class Completer( object ):
  """A base class for all Completers in YCM.

  Here's several important things you need to know if you're writing a custom
  Completer. The following are functions that the Vim part of YCM will be
  calling on your Completer:

  ShouldUseNow() is called with the start column of where a potential completion
  string should start and the current line (string) the cursor is on. For
  instance, if the user's input is 'foo.bar' and the cursor is on the 'r' in
  'bar', start_column will be the 0-based index of 'b' in the line. Your
  implementation of ShouldUseNow() should return True if your semantic completer
  should be used and False otherwise.

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

  ComputeCandidates() is the main entry point when the user types. For
  "foo.bar", the user query is "bar" and completions matching this string should
  be shown. It should return the list of candidates.  The format of the result
  can be a list of strings or a more complicated list of dictionaries. Use
  ycm.server.responses.BuildCompletionData to build the detailed response. See
  clang_completer.py to see how its used in practice.

  Again, you probably want to override ComputeCandidatesInner().

  You also need to implement the SupportedFiletypes() function which should
  return a list of strings, where the strings are Vim filetypes your completer
  supports.

  clang_completer.py is a good example of a "complicated" completer. A good
  example of a simple completer is ultisnips_completer.py.

  The On* functions are provided for your convenience. They are called when
  their specific events occur. For instance, the identifier completer collects
  all the identifiers in the file in OnFileReadyToParse() which gets called when
  the user stops typing for 2 seconds (Vim's CursorHold and CursorHoldI events).

  One special function is OnUserCommand. It is called when the user uses the
  command :YcmCompleter and is passed all extra arguments used on command
  invocation (e.g. OnUserCommand(['first argument', 'second'])).  This can be
  used for completer-specific commands such as reloading external configuration.
  When the command is called with no arguments you should print a short summary
  of the supported commands or point the user to the help section where this
  information can be found.

  Override the Shutdown() member function if your Completer subclass needs to do
  custom cleanup logic on server shutdown."""

  __metaclass__ = abc.ABCMeta

  def __init__( self, user_options ):
    self.user_options = user_options
    self.min_num_chars = user_options[ 'min_num_of_chars_for_completion' ]
    self.triggers_for_filetype = (
        TriggersForFiletype( user_options[ 'semantic_triggers' ] )
        if user_options[ 'auto_trigger' ] else defaultdict( set ) )
    self._completions_cache = CompletionsCache()


  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def ShouldUseNow( self, request_data ):
    if not self.ShouldUseNowInner( request_data ):
      self._completions_cache.Invalidate()
      return False

    # We have to do the cache valid check and get the completions as part of one
    # call because we have to ensure a different thread doesn't change the cache
    # data.
    cache_completions = self._completions_cache.GetCompletionsIfCacheValid(
        request_data[ 'line_num' ],
        request_data[ 'start_column' ] )

    # If None, then the cache isn't valid and we know we should return true
    if cache_completions is None:
      return True
    else:
      previous_results_were_valid = bool( cache_completions )
      return previous_results_were_valid


  def ShouldUseNowInner( self, request_data ):
    current_line = request_data[ 'line_value' ]
    start_column = request_data[ 'start_column' ]
    line_length = len( current_line )
    if not line_length or start_column - 1 >= line_length:
      return False

    filetype = self._CurrentFiletype( request_data[ 'filetypes' ] )
    triggers = self.triggers_for_filetype[ filetype ]

    for trigger in triggers:
      index = -1
      trigger_length = len( trigger )
      while True:
        line_index = start_column + index
        if line_index < 0 or current_line[ line_index ] != trigger[ index ]:
          break

        if abs( index ) == trigger_length:
          return True
        index -= 1
    return False


  def QueryLengthAboveMinThreshold( self, request_data ):
    query_length = request_data[ 'column_num' ] - request_data[ 'start_column' ]
    return query_length >= self.min_num_chars


  # It's highly likely you DON'T want to override this function but the *Inner
  # version of it.
  def ComputeCandidates( self, request_data ):
    if ( not ForceSemanticCompletion( request_data ) and
         not self.ShouldUseNow( request_data ) ):
      return []

    candidates = self._GetCandidatesFromSubclass( request_data )
    if request_data[ 'query' ]:
      candidates = self.FilterAndSortCandidates( candidates,
                                                 request_data[ 'query' ] )
    return candidates


  def _GetCandidatesFromSubclass( self, request_data ):
    cache_completions = self._completions_cache.GetCompletionsIfCacheValid(
          request_data[ 'line_num' ],
          request_data[ 'start_column' ] )

    if cache_completions:
      return cache_completions
    else:
      raw_completions = self.ComputeCandidatesInner( request_data )
      self._completions_cache.Update(
          request_data[ 'line_num' ],
          request_data[ 'start_column' ],
          raw_completions )
      return raw_completions


  def ComputeCandidatesInner( self, request_data ):
    pass


  def DefinedSubcommands( self ):
    return []


  def UserCommandsHelpMessage( self ):
    subcommands = self.DefinedSubcommands()
    if subcommands:
      return ( 'Supported commands are:\n' +
               '\n'.join( subcommands ) +
               '\nSee the docs for information on what they do.' )
    else:
      return 'This Completer has no supported subcommands.'


  def FilterAndSortCandidates( self, candidates, query ):
    if not candidates:
      return []

    # We need to handle both an omni_completer style completer and a server
    # style completer
    if 'words' in candidates:
      candidates = candidates[ 'words' ]

    sort_property = ''
    if 'word' in candidates[ 0 ]:
      sort_property = 'word'
    elif 'insertion_text' in candidates[ 0 ]:
      sort_property = 'insertion_text'

    matches = FilterAndSortCandidates( candidates,
                                       sort_property,
                                       ToUtf8IfNeeded( query ) )

    return matches


  def OnFileReadyToParse( self, request_data ):
    pass


  def OnBufferVisit( self, request_data ):
    pass


  def OnBufferUnload( self, request_data ):
    pass


  def OnInsertLeave( self, request_data ):
    pass


  def OnUserCommand( self, arguments, request_data ):
    raise NotImplementedError( NO_USER_COMMANDS )


  def OnCurrentIdentifierFinished( self, request_data ):
    pass


  def GetDiagnosticsForCurrentFile( self, request_data ):
    raise NoDiagnosticSupport


  def GetDetailedDiagnostic( self, request_data ):
    raise NoDiagnosticSupport


  def _CurrentFiletype( self, filetypes ):
    supported = self.SupportedFiletypes()

    for filetype in filetypes:
      if filetype in supported:
        return filetype

    return filetypes[0]


  @abc.abstractmethod
  def SupportedFiletypes( self ):
    pass


  def DebugInfo( self, request_data ):
    return ''


  def Shutdown( self ):
    pass


class CompletionsCache( object ):
  def __init__( self ):
    self._access_lock = threading.Lock()
    self.Invalidate()


  def Invalidate( self ):
    with self._access_lock:
      self._line = -1
      self._column = -1
      self._completions = []


  def Update( self, line, column, completions ):
    with self._access_lock:
      self._line = line
      self._column = column
      self._completions = completions


  def GetCompletions( self ):
    with self._access_lock:
      return self._completions


  def GetCompletionsIfCacheValid( self, current_line, start_column ):
    with self._access_lock:
      if not self._CacheValidNoLock( current_line, start_column ):
        return None
      return self._completions


  def CacheValid( self, current_line, start_column ):
    with self._access_lock:
      return self._CacheValidNoLock( current_line, start_column )


  def _CacheValidNoLock( self, current_line, start_column ):
    return current_line == self._line and start_column == self._column


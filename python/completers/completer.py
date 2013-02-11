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
import vimsupport
import ycm_core


class CompletionsCache( object ):
  def __init__( self ):
    self.line = -1
    self.column = -1
    self.raw_completions = []
    self.filtered_completions = []


  def CacheValid( self ):
    completion_line, _ = vimsupport.CurrentLineAndColumn()
    completion_column = int( vim.eval( "s:completion_start_column" ) )
    return completion_line == self.line and completion_column == self.column


class Completer( object ):
  __metaclass__ = abc.ABCMeta


  def __init__( self ):
    self.completions_future = None
    self.completions_cache = None


  def ShouldUseNow( self, start_column ):
    inner_says_yes = self.ShouldUseNowInner( start_column )
    previous_results_were_empty = ( self.completions_cache and
                                    not self.completions_cache.raw_completions )
    return inner_says_yes and not previous_results_were_empty


  def ShouldUseNowInner( self, start_column ):
    pass


  def CandidatesForQueryAsync( self, query ):
    if query and self.completions_cache and self.completions_cache.CacheValid():
      self.completions_cache.filtered_completions = (
        self.FilterAndSortCandidates(
          self.completions_cache.raw_completions,
          query ) )
    else:
      self.completions_cache = None
      self.CandidatesForQueryAsyncInner( query )


  def FilterAndSortCandidates( self, candidates, query ):
    if not candidates:
      return []

    if hasattr( candidates, 'words' ):
      candidates = candidates.words
    items_are_objects = 'word' in candidates[ 0 ]

    return ycm_core.FilterAndSortCandidates(
      candidates,
      'word' if items_are_objects else '',
      query )


  def CandidatesForQueryAsyncInner( self, query ):
    pass


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


  def CandidatesFromStoredRequest( self ):
    if self.completions_cache:
      return self.completions_cache.filtered_completions
    else:
      self.completions_cache = CompletionsCache()
      self.completions_cache.raw_completions = self.CandidatesFromStoredRequestInner()
      self.completions_cache.line, _ = vimsupport.CurrentLineAndColumn()
      self.completions_cache.column = int(
        vim.eval( "s:completion_start_column" ) )
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


  def OnCursorHold( self ):
    pass


  def OnInsertLeave( self ):
    pass


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


  @abc.abstractmethod
  def SupportedFiletypes( self ):
    pass


  def DebugInfo( self ):
    return ''

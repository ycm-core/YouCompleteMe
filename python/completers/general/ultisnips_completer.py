#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
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

from completers.completer import Completer, CompletionsCache
from UltiSnips import UltiSnips_Manager
import vimsupport

MIN_NUM_CHARS = int( vimsupport.GetVariableValue(
  "g:ycm_min_num_of_chars_for_completion" ) )

class UltiSnipsCompleter( Completer ):
  """
  General completer that provides UltiSnips snippet names in completions.

  This completer makes a cache of all snippets for filetype because each
  call to _snips() is quite long and it is much faster to cache all snippets
  once and then filter them. Cache is invalidated on buffer switching.
  """

  def __init__( self ):
    super( UltiSnipsCompleter, self ).__init__()
    self._candidates = None


  def ShouldUseNow( self, start_column ):
    inner_says_yes = self.ShouldUseNowInner( start_column )

    previous_results_were_empty = ( self.completions_cache and
                                    not self.completions_cache.raw_completions )
    return inner_says_yes and not previous_results_were_empty


  def ShouldUseNowInner( self, start_column ):
    query_length = vimsupport.CurrentColumn() - start_column
    return query_length >= MIN_NUM_CHARS


  def SupportedFiletypes( self ):
    # magic token meaning all filetypes
    return set( [ 'ycm_all' ] )


  def CandidatesForQueryAsync( self, query, start_column ):
    self.completion_start_column = start_column

    if self.completions_cache:
      self.completions_cache.filtered_completions = (
        self.FilterAndSortCandidates(
          self.completions_cache.raw_completions,
          query ) )
    else:
      self.completions_cache = None
      self.CandidatesForQueryAsyncInner( query, start_column )


  def CandidatesForQueryAsyncInner( self, query, start_column ):
    self._query = query


  def AsyncCandidateRequestReadyInner( self ):
    return self.flag


  # We need to override this because we need to store all snippets but return
  # filtered results on first call.
  def CandidatesFromStoredRequest( self ):
    if self.completions_cache:
      return self.completions_cache.filtered_completions
    else:
      self.completions_cache = CompletionsCache()
      self.completions_cache.raw_completions = self.CandidatesFromStoredRequestInner()
      self.completions_cache.line, _ = vimsupport.CurrentLineAndColumn()
      self.completions_cache.column = self.completion_start_column
      return self.FilterAndSortCandidates( self._candidates, self._query )


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates


  def SetCandidates( self ):
    try:
      # get all snippets for filetype
      rawsnips = UltiSnips_Manager._snips( '', 1 )
      self._candidates = [ { 'word': str( snip.trigger ),
                              'menu': str( '<snip> ' + snip.description ) }
                          for snip in rawsnips ]
    except:
      self._candidates = []
    self.flag = True


  def OnFileReadyToParse( self ):
    # Invalidate cache on buffer switch
    self.completions_cache = None
    self.SetCandidates()

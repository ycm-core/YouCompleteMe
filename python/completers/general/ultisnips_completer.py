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

from completers.completer import GeneralCompleter, CompletionsCache
from UltiSnips import UltiSnips_Manager
import vimsupport


class UltiSnipsCompleter( GeneralCompleter ):
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
    return self.QueryLengthAboveMinThreshold( start_column )


  # We need to override this because Completer version invalidates cache on
  # empty query and we want to invalidate cache only on buffer switch.
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


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates


  def SetCandidates( self ):
    try:
      rawsnips = UltiSnips_Manager._snips( '', 1 )

      # UltiSnips_Manager._snips() returns a class instance where:
      # class.trigger - name of snippet trigger word ( e.g. defn or testcase )
      # class.description - description of the snippet
      self._candidates = [ { 'word': str( snip.trigger ),
                              'menu': str( '<snip> ' + snip.description ) }
                          for snip in rawsnips ]
    except:
      self._candidates = []
    self.flag = True


  def OnFileReadyToParse( self ):
    # Invalidate cache on buffer switch
    self.completions_cache = CompletionsCache()
    self.SetCandidates()
    self.completions_cache.raw_completions = self._candidates

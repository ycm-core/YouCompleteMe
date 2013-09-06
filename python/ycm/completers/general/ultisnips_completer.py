#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
#                    Strahinja Val Markovic  <val@markovic.io>
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

from ycm.completers.general_completer import GeneralCompleter
from UltiSnips import UltiSnips_Manager
from ycm import server_responses


class UltiSnipsCompleter( GeneralCompleter ):
  """
  General completer that provides UltiSnips snippet names in completions.
  """

  def __init__( self, user_options ):
    super( UltiSnipsCompleter, self ).__init__( user_options )
    self._candidates = None
    self._filtered_candidates = None


  def ShouldUseNowInner( self, request_data ):
    return self.QueryLengthAboveMinThreshold( request_data )


  def CandidatesForQueryAsync( self, request_data ):
    self._filtered_candidates = self.FilterAndSortCandidates(
      self._candidates, request_data[ 'query' ] )


  def AsyncCandidateRequestReady( self ):
    return True


  def CandidatesFromStoredRequest( self ):
    return self._filtered_candidates if self._filtered_candidates else []


  def OnBufferVisit( self ):
    self._candidates = _GetCandidates()


def _GetCandidates():
  try:
    rawsnips = UltiSnips_Manager._snips( '', 1 )

    # UltiSnips_Manager._snips() returns a class instance where:
    # class.trigger - name of snippet trigger word ( e.g. defn or testcase )
    # class.description - description of the snippet
    return [ server_responses.BuildCompletionData(
              str( snip.trigger ),
              str( '<snip> ' + snip.description.encode( 'utf-8' ) ) )
            for snip in rawsnips ]
  except:
    return []

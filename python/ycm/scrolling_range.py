# Copyright (C) 2023, YouCompleteMe Contributors
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

from ycm import vimsupport


class ScrollingBufferRange( object ):
  """Abstraction used by inlay hints and semantic tokens to only request visible
  ranges"""

  # FIXME: Send a request per-disjoint range for this buffer rather than the
  # maximal range. then collaate the results when all responses are returned
  def __init__( self, bufnr ):
    self._bufnr = bufnr
    self._tick = -1
    self._request = None
    self._last_requested_range = None


  def Ready( self ):
    return self._request is not None and self._request.Done()


  def Request( self, force=False ):
    if self._request and not self.Ready():
      return True

    # Check to see if the buffer ranges would actually change anything visible.
    # This avoids a round-trip for every single line scroll event
    if ( not force and
         self._tick == vimsupport.GetBufferChangedTick( self._bufnr ) and
         vimsupport.VisibleRangeOfBufferOverlaps(
           self._bufnr,
           self._last_requested_range ) ):
      return False # don't poll

    # FIXME: This call is duplicated in the call to VisibleRangeOfBufferOverlaps
    #  - remove the expansion param
    #  - look up the actual visible range, then call this function
    #  - if not overlapping, do the factor expansion and request
    self._last_requested_range = vimsupport.RangeVisibleInBuffer( self._bufnr )
    # If this is false, either the self._bufnr is not a valid buffer number or
    # the buffer is not visible in any window.
    # Since this is called asynchronously, a user may bwipeout a buffer with
    # self._bufnr number between polls.
    if self._last_requested_range is None:
      return False

    self._tick = vimsupport.GetBufferChangedTick( self._bufnr )

    # We'll never use the last response again, so clear it
    self._latest_response = None
    self._request = self._NewRequest( self._last_requested_range )
    self._request.Start()
    return True


  def Update( self ):
    if not self._request:
      # Nothing to update
      return True

    assert self.Ready()

    # We're ready to use this response. Clear the request (to avoid repeatedly
    # re-polling).
    self._latest_response = self._request.Response()
    self._request = None

    if self._tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # Buffer has changed, we should ignore the data and retry
      self.Request( force=True )
      return False # poll again

    self._Draw()

    # No need to re-poll
    return True


  def Refresh( self ):
    if self._tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # stale data
      return

    if self._request is not None:
      # request in progress; we''l handle refreshing when it's done.
      return

    self._Draw()


  def GrowRangeIfNeeded( self, rng ):
    """When processing results, we may receive a wider range than requested. In
    that case, grow our 'last requested' range to minimise requesting more
    frequently than we need to."""
    # Note: references (pointers) so no need to re-assign
    rmin = self._last_requested_range[ 'start' ]
    rmax = self._last_requested_range[ 'end' ]

    start = rng[ 'start' ]
    end = rng[ 'end' ]

    if rmin[ 'line_num' ] is None or start[ 'line_num' ] < rmin[ 'line_num' ]:
      rmin[ 'line_num' ] = start[ 'line_num' ]
      rmin[ 'column_num' ] = start[ 'column_num' ]
    elif start[ 'line_num' ] == rmin[ 'line_num' ]:
      rmin[ 'column_num' ] = min( start[ 'column_num' ],
                                  rmin[ 'column_num' ] )

    if rmax[ 'line_num' ] is None or end[ 'line_num' ] > rmax[ 'line_num' ]:
      rmax[ 'line_num' ] = end[ 'line_num' ]
      rmax[ 'column_num' ] = end[ 'column_num' ]
    elif end[ 'line_num' ] == rmax[ 'line_num' ]:
      rmax[ 'column_num' ] = max( end[ 'column_num' ], rmax[ 'column_num' ] )


  # API; just implement the following, using self._bufnr and
  # self._latest_response as required

  @abc.abstractmethod
  def _NewRequest( self, request_range ):
    # prepare a new request_data and return it
    pass


  @abc.abstractmethod
  def _Draw( self ):
    # actuall paint the properties
    pass

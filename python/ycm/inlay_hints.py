# Copyright (C) 2022, YouCompleteMe Contributors
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


from ycm.client.inlay_hints_request import InlayHintsRequest
from ycm.client.base_request import BuildRequestData
from ycm import vimsupport
from ycm import text_properties as tp
import vim
from ycmd.utils import ToBytes


HIGHLIGHT_GROUP = {
  # 1-based inedexes
  0: '',
  1: 'Comment',        # Type
  2: 'Comment'   # Parameter
}
REPORTED_MISSING_TYPES = set()


def Initialise():
  if not vimsupport.VimSupportsVirtualText():
    return False

  props = tp.GetTextPropertyTypes()
  if 'YCM_INLAY_UNKNOWN' not in props:
    tp.AddTextPropertyType( 'YCM_INLAY_UNKNOWN', highlight = 'Comment' )

  for token_type, group in HIGHLIGHT_GROUP.items():
    prop = f'YCM_INLAY_{ token_type }'
    if prop not in props and vimsupport.GetIntValue(
        f"hlexists( '{ vimsupport.EscapeForVim( group ) }' )" ):
      tp.AddTextPropertyType( prop, highlight = group )

  return True

class InlayHints:
  """Stores the inlay hints state for a Vim buffer"""

  # FIXME: Send a request per-disjoint range for this buffer rather than the
  # maximal range. then collaate the results when all responses are returned
  def __init__( self, bufnr, user_options ):
    self._request = None
    self._bufnr = bufnr
    self._prop_ids = set()
    self.tick = -1
    self._latest_inlay_hints = []


  def Request( self ):
    if self._request and not self.Ready():
      return

    # We're requesting changes, so the existing results are now invalid
    self._latest_inlay_hints = []
    self.tick = vimsupport.GetBufferChangedTick( self._bufnr )

    # TODO: How to determine the range to display ? Should we do the range
    # visible in "all" windows? We're doing this per-buffer, but perhaps it
    # should actually be per-window; that might ultimately be a better model
    # but the resulting properties are per-buffer, not per-window.
    #
    # Perhaps the maximal range of visible windows or something.
    request_data = BuildRequestData( self._bufnr )
    request_data.update( {
      'range': vimsupport.RangeVisibleInBuffer( self._bufnr )
    } )
    self._request = InlayHintsRequest( request_data )
    self._request.Start()


  def Ready( self ):
    return self._request is not None and self._request.Done()


  def Clear( self ):
    for prop_id in self._prop_ids:
      tp.ClearTextProperties( self._bufnr, prop_id )
    self._prop_ids.clear()


  def Update( self ):
    if not self._request:
      # Nothing to update
      return True

    assert self.Ready()

    # We're ready to use this response. Clear it (to avoid repeatedly
    # re-polling).
    self._latest_inlay_hints = [] ;# in case there was an error in request
    self._latest_inlay_hints = self._request.Response()
    self._request = None

    if self.tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # Buffer has changed, we should ignore the data and retry
      self.Request()
      return False # poll again

    self._Draw()

    # No need to re-poll
    return True


  def Refresh( self ):
    if self.tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # state data
      return

    if self._request is not None:
      # request in progress; we''l handle refreshing when it's done.
      return

    self._Draw()


  def _Draw( self ):
    self.Clear()

    for inlay_hint in self._latest_inlay_hints:
      if 'kind' not in inlay_hint:
        prop_type = 'YCM_INLAY_UNKNOWN'
      elif inlay_hint[ 'kind' ] not in HIGHLIGHT_GROUP:
        prop_type = 'YCM_INLAY_UNKNOWN'
      else:
        prop_type = 'YCM_INLAY_' + str( inlay_hint[ 'kind' ] )

      self._prop_ids.add(
        tp.AddTextProperty( self._bufnr,
                            None,
                            prop_type,
                            {
                              'start': inlay_hint[ 'position' ],
                              'end': inlay_hint[ 'position' ],
                            },
                            {
                              'text': inlay_hint[ 'label' ]
                            } ) )


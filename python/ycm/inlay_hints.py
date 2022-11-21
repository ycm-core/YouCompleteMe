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


HIGHLIGHT_GROUP = {
  'Type':      'YcmInlayHint',
  'Parameter': 'YcmInlayHint',
  'Enum':      'YcmInlayHint',
}
REPORTED_MISSING_TYPES = set()


def Initialise():
  if not vimsupport.VimSupportsVirtualText():
    return False

  props = tp.GetTextPropertyTypes()
  if 'YCM_INLAY_UNKNOWN' not in props:
    tp.AddTextPropertyType( 'YCM_INLAY_UNKNOWN',
                            highlight = 'YcmInlayHint',
                            start_incl = 1 )
  if 'YCM_INLAY_PADDING' not in props:
    tp.AddTextPropertyType( 'YCM_INLAY_PADDING',
                            highlight = 'YcmInvisible',
                            start_incl = 1 )

  for token_type, group in HIGHLIGHT_GROUP.items():
    prop = f'YCM_INLAY_{ token_type }'
    if prop not in props and vimsupport.GetIntValue(
        f"hlexists( '{ vimsupport.EscapeForVim( group ) }' )" ):
      tp.AddTextPropertyType( prop,
                              highlight = group,
                              start_incl = 1 )

  return True


class InlayHints:
  """Stores the inlay hints state for a Vim buffer"""

  # FIXME: Send a request per-disjoint range for this buffer rather than the
  # maximal range. then collaate the results when all responses are returned
  def __init__( self, bufnr, user_options ):
    self._request = None
    self._bufnr = bufnr
    self.tick = -1
    self._latest_inlay_hints = []
    self._last_requested_range = None


  def Request( self, force=False ):
    if self._request and not self.Ready():
      return True

    # Check to see if the buffer ranges would actually change anything visible.
    # This avoids a round-trip for every single line scroll event
    if ( not force and
         self.tick == vimsupport.GetBufferChangedTick( self._bufnr ) and
         vimsupport.VisibleRangeOfBufferOverlaps(
           self._bufnr,
           self._last_requested_range ) ):
      return False # don't poll

    # We're requesting changes, so the existing results are now invalid
    self._latest_inlay_hints = []
    # FIXME: This call is duplicated in the call to VisibleRangeOfBufferOverlaps
    #  - remove the expansion param
    #  - look up the actual visible range, then call this function
    #  - if not overlapping, do the factor expansion and request
    self._last_requested_range = vimsupport.RangeVisibleInBuffer( self._bufnr )
    self.tick = vimsupport.GetBufferChangedTick( self._bufnr )

    request_data = BuildRequestData( self._bufnr )
    request_data.update( {
      'range': self._last_requested_range
    } )
    self._request = InlayHintsRequest( request_data )
    self._request.Start()
    return True


  def Ready( self ):
    return self._request is not None and self._request.Done()


  def Clear( self ):
    # ClearTextProperties is slow as it must scan the whole buffer
    # we shouldn't use _last_requested_range, because the server is free to
    # return a larger range, so we pick the first/last from the latest results
    types = [ 'YCM_INLAY_UNKNOWN', 'YCM_INLAY_PADDING' ] + [
      f'YCM_INLAY_{ prop_type }' for prop_type in HIGHLIGHT_GROUP.keys()
    ]

    tp.ClearTextProperties( self._bufnr, prop_types = types )

  def Update( self ):
    if not self._request:
      # Nothing to update
      return True

    assert self.Ready()

    # We're ready to use this response. Clear it (to avoid repeatedly
    # re-polling).
    self._latest_inlay_hints = self._request.Response()
    self._request = None

    if self.tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # Buffer has changed, we should ignore the data and retry
      self.Request( force=True )
      return False # poll again

    self._Draw()

    # No need to re-poll
    return True


  def Refresh( self ):
    if self.tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # stale data
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
        prop_type = 'YCM_INLAY_' + inlay_hint[ 'kind' ]

      if inlay_hint.get( 'paddingLeft', False ):
        tp.AddTextProperty( self._bufnr,
                            None,
                            'YCM_INLAY_PADDING',
                            {
                              'start': inlay_hint[ 'position' ],
                            },
                            {
                              'text': ' '
                            } )

      tp.AddTextProperty( self._bufnr,
                          None,
                          prop_type,
                          {
                            'start': inlay_hint[ 'position' ],
                          },
                          {
                            'text': inlay_hint[ 'label' ]
                          } )

      if inlay_hint.get( 'paddingRight', False ):
        tp.AddTextProperty( self._bufnr,
                            None,
                            'YCM_INLAY_PADDING',
                            {
                              'start': inlay_hint[ 'position' ],
                            },
                            {
                              'text': ' '
                            } )

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
from ycm import scrolling_range as sr


HIGHLIGHT_GROUP = {
  'Type':      'YcmInlayHint',
  'Parameter': 'YcmInlayHint',
  'Enum':      'YcmInlayHint',
}
REPORTED_MISSING_TYPES = set()


def Initialise():
  if vimsupport.VimIsNeovim():
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


class InlayHints( sr.ScrollingBufferRange ):
  """Stores the inlay hints state for a Vim buffer"""


  def _NewRequest( self, request_range ):
    request_data = BuildRequestData( self._bufnr )
    request_data[ 'range' ] = request_range
    return InlayHintsRequest( request_data )


  def Clear( self ):
    types = [ 'YCM_INLAY_UNKNOWN', 'YCM_INLAY_PADDING' ] + [
      f'YCM_INLAY_{ prop_type }' for prop_type in HIGHLIGHT_GROUP.keys()
    ]

    tp.ClearTextProperties( self._bufnr, prop_types = types )


  def _Draw( self ):
    self.Clear()

    for inlay_hint in self._latest_response:
      if 'kind' not in inlay_hint:
        prop_type = 'YCM_INLAY_UNKNOWN'
      elif inlay_hint[ 'kind' ] not in HIGHLIGHT_GROUP:
        prop_type = 'YCM_INLAY_UNKNOWN'
      else:
        prop_type = 'YCM_INLAY_' + inlay_hint[ 'kind' ]

      self.GrowRangeIfNeeded( {
        'start': inlay_hint[ 'position' ],
        'end': {
          'line_num': inlay_hint[ 'position' ][ 'line_num' ],
          'column_num': inlay_hint[ 'position' ][ 'column_num' ] + len(
            inlay_hint[ 'label' ] )
        }
      } )

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

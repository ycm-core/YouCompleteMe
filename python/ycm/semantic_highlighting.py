# Copyright (C) 2020, YouCompleteMe Contributors
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


from ycm.client.semantic_tokens_request import SemanticTokensRequest
from ycm.client.base_request import BuildRequestData
from ycm import vimsupport
from ycm import text_properties as tp


HIGHLIGHT_GROUP = {
  'namespace': 'Type',
  'type': 'Type',
  'class': 'Structure',
  'enum': 'Structure',
  'interface': 'Structure',
  'struct': 'Structure',
  'typeParameter': 'Identifier',
  'parameter': 'Identifier',
  'variable': 'Identifier',
  'property': 'Identifier',
  'enumMember': 'Identifier',
  'enumConstant': 'Constant',
  'event': 'Identifier',
  'function': 'Function',
  'member': 'Identifier',
  'macro': 'Macro',
  'method': 'Function',
  'keyword': 'Keyword',
  'modifier': 'Keyword',
  'comment': 'Comment',
  'string': 'String',
  'number': 'Number',
  'regexp': 'String',
  'operator': 'Operator',
  'unknown': 'Normal',
}
REPORTED_MISSING_TYPES = set()


def Initialise():
  if vimsupport.VimIsNeovim():
    return

  props = tp.GetTextPropertyTypes()
  if 'YCM_HL_UNKNOWN' not in props:
    tp.AddTextPropertyType( 'YCM_HL_UNKNOWN',
                            highlight = 'WarningMsg',
                            priority = 0 )

  for token_type, group in HIGHLIGHT_GROUP.items():
    prop = f'YCM_HL_{ token_type }'
    if prop not in props and vimsupport.GetIntValue(
        f"hlexists( '{ vimsupport.EscapeForVim( group ) }' )" ):
      tp.AddTextPropertyType( prop,
                              highlight = group,
                              priority = 0 )


# "arbitrary" base id
NEXT_TEXT_PROP_ID = 70784


def NextPropID():
  global NEXT_TEXT_PROP_ID
  try:
    return NEXT_TEXT_PROP_ID
  finally:
    NEXT_TEXT_PROP_ID += 1



class SemanticHighlighting:
  """Stores the semantic highlighting state for a Vim buffer"""

  def __init__( self, bufnr, user_options ):
    self._request = None
    self._bufnr = bufnr
    self._prop_id = NextPropID()
    self.tick = -1


  def SendRequest( self ):
    if self._request and not self.IsResponseReady():
      return

    self.tick = vimsupport.GetBufferChangedTick( self._bufnr )

    request: dict = BuildRequestData( self._bufnr )
    request.update( {
      'range': vimsupport.RangeVisibleInBuffer( self._bufnr )
    } )
    self._request = SemanticTokensRequest( request )
    self._request.Start()

  def IsResponseReady( self ):
    return self._request is not None and self._request.Done()

  def Update( self ):
    if not self._request:
      # Nothing to update
      return True

    assert self.IsResponseReady()

    # We're ready to use this response. Clear it (to avoid repeatedly
    # re-polling).
    response = self._request.Response()
    self._request = None

    if self.tick != vimsupport.GetBufferChangedTick( self._bufnr ):
      # Buffer has changed, we should ignore the data and retry
      self.SendRequest()
      return False # poll again

    # We requested a snapshot
    tokens = response.get( 'tokens', [] )

    prev_prop_id = self._prop_id
    self._prop_id = NextPropID()

    for token in tokens:
      if token[ 'type' ] not in HIGHLIGHT_GROUP:
        if token[ 'type' ] not in REPORTED_MISSING_TYPES:
          REPORTED_MISSING_TYPES.add( token[ 'type' ] )
          vimsupport.PostVimMessage(
            f"Missing property type for { token[ 'type' ] }" )
        continue
      prop_type = f"YCM_HL_{ token[ 'type' ] }"
      tp.AddTextProperty( self._bufnr,
                          self._prop_id,
                          prop_type,
                          token[ 'range' ] )

    tp.ClearTextProperties( self._bufnr, prop_id = prev_prop_id )

    # No need to re-poll
    return True

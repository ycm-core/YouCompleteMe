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
from ycm import scrolling_range as sr

import vim


HIGHLIGHT_GROUPS = [{
  'highlight': {
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
}]
REPORTED_MISSING_TYPES = set()


def AddHiForTokenType( bufnr, token_type, group ):
  prop = f'YCM_HL_{ token_type }'
  hi = group
  combine = 0
  filetypes = "(default)"
  if bufnr is not None:
    filetypes = vimsupport.GetBufferFiletypes(bufnr)

  if group is None or len( group ) == 0:
    hi = 'Normal'
    combine = 1

  if not vimsupport.GetIntValue(
      f"hlexists( '{ vimsupport.EscapeForVim( hi ) }' )" ):
    vimsupport.PostVimMessage(
        f"Higlight group { hi } is not difined for { filetypes }. "
        f"See :help youcompleteme-customising-highlight-groups" )
    return

  if bufnr is None:
    props = tp.GetTextPropertyTypes()
    if prop not in props:
      tp.AddTextPropertyType( prop,
                              highlight = hi,
                              priority = 0,
                              combine = combine )
  else:
    try:
      tp.AddTextPropertyType( prop,
                              highlight = hi,
                              priority = 0,
                              combine = combine,
                              bufnr = bufnr )
    except vim.error:
      # at YcmRestart we can get error about redefining properties, just ignore them
      pass



def Initialise():
  if vimsupport.VimIsNeovim():
    return

  global HIGHLIGHT_GROUPS

  if "ycm_semantic_highlight_groups" in vimsupport.GetVimGlobalsKeys():
    hi_groups: list[dict] = vimsupport.VimExpressionToPythonType(
        "g:ycm_semantic_highlight_groups" )
    hi_groups.extend( HIGHLIGHT_GROUPS[:] )
    HIGHLIGHT_GROUPS = hi_groups

  # init default highlight
  default_hi = None
  for groups in HIGHLIGHT_GROUPS:
    if 'filetypes' not in groups:
      if 'highlight' not in groups:
        continue

      if default_hi is None:
        default_hi = groups
      else:
        # merge all defaults
        for token_type, group in groups[ 'highlight' ].items():
          if token_type not in default_hi[ 'highlight' ]:
            default_hi[ 'highlight' ][ token_type ] = group

  if default_hi is None or 'highlight' not in default_hi:
    return

  # XXX define default settings globally for make it compatible with older
  # settings
  for token_type, group in default_hi[ 'highlight' ].items():
    AddHiForTokenType( None, token_type, group )


# "arbitrary" base id
NEXT_TEXT_PROP_ID = 70784


def NextPropID():
  global NEXT_TEXT_PROP_ID
  try:
    return NEXT_TEXT_PROP_ID
  finally:
    NEXT_TEXT_PROP_ID += 1



class SemanticHighlighting( sr.ScrollingBufferRange ):
  """Stores the semantic highlighting state for a Vim buffer"""

  def __init__( self, bufnr ):
    self._prop_id = NextPropID()
    super().__init__( bufnr )

    self._filetypes = vimsupport.GetBufferFiletypes( bufnr )

    default_hi = None
    target_groups = None
    for ft_groups in HIGHLIGHT_GROUPS:
      if 'filetypes' in ft_groups:
        for filetype in self._filetypes:
          if filetype in ft_groups[ 'filetypes' ]:
            target_groups = ft_groups
      elif default_hi is None:
        default_hi = ft_groups

    if target_groups is None and ( default_hi is None or 'highlight' not in default_hi ):
      self._do_highlight = False
      return
    elif target_groups is None:
      # default highlight should be defined globaly
      self._do_highlight = True
      return
    elif 'highlight' not in target_groups:
      self._do_highlight = False
      return

    for token_type, group in target_groups[ 'highlight' ].items():
      AddHiForTokenType( bufnr, token_type, group )

    self._do_highlight = True


  def _NewRequest( self, request_range ):
    request: dict = BuildRequestData( self._bufnr )
    request[ 'range' ] = request_range
    return SemanticTokensRequest( request )


  def _Draw( self ):
    if self._do_highlight == False:
      return

    # We requested a snapshot
    tokens = self._latest_response.get( 'tokens', [] )

    prev_prop_id = self._prop_id
    self._prop_id = NextPropID()

    for token in tokens:
      prop_type = f"YCM_HL_{ token[ 'type' ] }"
      rng = token[ 'range' ]
      self.GrowRangeIfNeeded( rng )

      try:
        tp.AddTextProperty( self._bufnr, self._prop_id, prop_type, rng )
      except vim.error as e:
        if 'E971:' in str( e ): # Text property doesn't exist
          if token[ 'type' ] not in REPORTED_MISSING_TYPES:
            REPORTED_MISSING_TYPES.add( token[ 'type' ] )
            vimsupport.PostVimMessage(
              f"Token type { token[ 'type' ] } is not defined for { self._filetypes }. "
              f"See :help youcompleteme-customising-highlight-groups" )
        else:
          raise e

    tp.ClearTextProperties( self._bufnr, prop_id = prev_prop_id )

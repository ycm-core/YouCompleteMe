# Copyright (C) 2011-2018 YouCompleteMe contributors
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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import vim
import json
import logging
from operator import sub
from ycm import vimsupport
from ycm.vimsupport import GetIntValue

LOGGER = logging.getLogger( 'ycm' )


class SignatureHelpState( object ):
  ACTIVE = 'ACTIVE'
  INACTIVE = 'INACTIVE'

  def __init__( self,
                popup_win_id = None,
                state = INACTIVE ):
    self.popup_win_id = popup_win_id
    self.state = state
    self.anchor = None


def SetUpPopupWindow( popup_win_id, buf_lines ):
  # FIXME: For some reason the below does not seem to work.
  #
  # win = vim.windows[ GetIntValue( 'win_id2win( {} )'.format(
  #   popup_win_id ) ) ]
  # win.options[ 'signcolumn' ] = 'no'

  vim.eval( 'setwinvar( {}, "&signcolumn", "no" )'.format( popup_win_id ) )


def _SupportsPopupWindows():
  for required_method in [ 'popup_create',
                           'popup_move',
                           'popup_hide',
                           'popup_show',
                           'popup_close',
                           'prop_add',
                           'prop_type_add' ]:
    if not GetIntValue( vim.eval( 'exists( "*{}" )'.format(
      required_method ) ) ):
      return False
  return True


def _MakeSignatureHelpBuffer( signature_info ):
  active_signature = int( signature_info.get( 'activeSignature', 0 ) )
  active_parameter = int( signature_info.get( 'activeParameter', 0 ) )

  lines = []
  signatures = ( signature_info.get( 'signatures' ) or [] )

  for sig_index, signature in enumerate( signatures ):
    props = []

    sig_label = signature[ 'label' ]
    if sig_index == active_signature:
      props.append( {
        'col': 1,
        'length': len( sig_label ),
        'type': 'YCM-signature-help-current-signature'
      } )
    else:
      props.append( {
        'col': 1,
        'length': len( sig_label ),
        'type': 'YCM-signature-help-signature'
      } )

    parameters = ( signature.get( 'parameters' ) or [] )
    cur_param_idx = -1
    for param_index, parameter in enumerate( parameters ):
      param_label = parameter[ 'label' ]
      cur_param_idx = sig_label.find( param_label, cur_param_idx + 1 )
      if param_index == active_parameter:
        props.append( {
          'col': cur_param_idx + 1, # 1-based
          'length': len( param_label ),
          'type': 'YCM-signature-help-current-argument'
        } )

    lines.append( {
      'text': sig_label,
      'props': props
    } )

  return lines


def UpdateSignatureHelp( state, signature_info ):
  if not _SupportsPopupWindows():
    return state

  LOGGER.info( 'UpdateSignatureHelp: LINE: %s', vim.current.line )
  LOGGER.info( 'UpdateSignatureHelp: %s', signature_info )

  signatures = signature_info.get( 'signatures' ) or []

  if not signatures:
    if state.popup_win_id:
      vim.eval( "popup_close( {} )".format( state.popup_win_id ) )
    return SignatureHelpState( None, SignatureHelpState.INACTIVE )

  if state.state != SignatureHelpState.ACTIVE:
    state.anchor = vimsupport.CurrentLineAndColumn()

  state.state = SignatureHelpState.ACTIVE

  # FIXME: Remove this
  # For now, there is no resize for the popup, so we have to re-create it
  if state.popup_win_id:
    vim.eval( "popup_close( {} )".format( state.popup_win_id ) )
    state.popup_win_id = None
  # FIXME: Remove this

  # Generate the buffer as a list of lines
  buf_lines = _MakeSignatureHelpBuffer( signature_info )

  # Find the buffer position of the anchor and calculate it as an offset from
  # the cursor position.
  cur_pos = vimsupport.CurrentLineAndColumn()

  cursor_relative_pos = [ state.anchor[ 0 ] - cur_pos[ 0 ] - 1 ,
                          state.anchor[ 1 ] - cur_pos[ 1 ] ]

  # Use the cursor offset to find the actual screen position. It's surprisingly
  # difficult to calculate the real screen position of a mark, or other buffer
  # position.
  options = {
    "line": 'cursor{:+d}'.format( cursor_relative_pos[ 0 ] ),
    "col":  'cursor{:+d}'.format( cursor_relative_pos[ 1 ] ),
    "pos": "botleft",
    "wrap": 0,
    "flip": 1
  }

  if not state.popup_win_id:
    state.popup_win_id = GetIntValue( vim.eval( "popup_create( {}, {} )".format(
      json.dumps( buf_lines ),
      json.dumps( options ) ) ) )

  SetUpPopupWindow( state.popup_win_id, buf_lines )

  # Should do nothing if already visible
  # FIXME: Reinstate this, and/or find a way to update the buffer from the text
  # prop dicts.
  # vim.eval( 'popup_move( {}, {} )'.format( state.popup_win_id,
  #                                          json.dumps( options ) ) )
  # vim.eval( 'popup_show( {} )'.format( state.popup_win_id ) )

  return state

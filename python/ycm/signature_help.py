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

import vim
import json
from ycm import vimsupport
from ycmd import utils
from ycm.vimsupport import memoize, GetIntValue


class SignatureHelpState:
  ACTIVE = 'ACTIVE'
  INACTIVE = 'INACTIVE'

  def __init__( self,
                popup_win_id = None,
                state = INACTIVE ):
    self.popup_win_id = popup_win_id
    self.state = state
    self.anchor = None


def _MakeSignatureHelpBuffer( signature_info ):
  active_parameter = int( signature_info.get( 'activeParameter', 0 ) )

  lines = []
  signatures = ( signature_info.get( 'signatures' ) or [] )

  for sig_index, signature in enumerate( signatures ):
    props = []

    sig_label = signature[ 'label' ]
    parameters = ( signature.get( 'parameters' ) or [] )
    for param_index, parameter in enumerate( parameters ):
      param_label = parameter[ 'label' ]
      begin = int( param_label[ 0 ] )
      end = int( param_label[ 1 ] )
      if param_index == active_parameter:
        props.append( {
          'col': begin + 1, # 1-based
          'length': end - begin,
          'type': 'YCM-signature-help-current-argument'
        } )

    lines.append( {
      'text': sig_label,
      'props': props
    } )

  return lines


@memoize
def ShouldUseSignatureHelp():
  return ( vimsupport.VimHasFunctions( 'screenpos', 'pum_getpos' ) and
           vimsupport.VimSupportsPopupWindows() )


def UpdateSignatureHelp( state, signature_info ): # noqa
  if not ShouldUseSignatureHelp():
    return state

  signatures = signature_info.get( 'signatures' ) or []

  if not signatures:
    if state.popup_win_id:
      # TODO/FIXME: Should we use popup_hide() instead ?
      vim.eval( "popup_close( {} )".format( state.popup_win_id ) )
    return SignatureHelpState( None, SignatureHelpState.INACTIVE )

  if state.state != SignatureHelpState.ACTIVE:
    state.anchor = vimsupport.CurrentLineAndColumn()

  state.state = SignatureHelpState.ACTIVE

  # Generate the buffer as a list of lines
  buf_lines = _MakeSignatureHelpBuffer( signature_info )
  screen_pos = vimsupport.ScreenPositionForLineColumnInWindow(
    vim.current.window,
    state.anchor[ 0 ] + 1,  # anchor 0-based
    state.anchor[ 1 ] + 1 ) # anchor 0-based

  # Simulate 'flip' at the screen boundaries by using screenpos and hiding the
  # signature help menu if it overlaps the completion popup (pum).
  #
  # FIXME: revert to cursor-relative positioning and the 'flip' option when that
  # is implemented (if that is indeed better).

  # By default display above the anchor
  line = int( screen_pos[ 'row' ] ) - 1 # -1 to display above the cur line
  pos = "botleft"

  cursor_line = vimsupport.CurrentLineAndColumn()[ 0 ] + 1
  if int( screen_pos[ 'row' ] ) <= len( buf_lines ):
    # No room at the top, display below
    line = int( screen_pos[ 'row' ] ) + 1
    pos = "topleft"

  # Don't allow the popup to overlap the cursor
  if ( pos == 'topleft' and
       line < cursor_line and
       line + len( buf_lines ) >= cursor_line ):
    line = 0

  # Don't allow the popup to overlap the pum
  if line > 0 and GetIntValue( 'pumvisible()' ):
    pum_line = GetIntValue( 'pum_getpos().row' ) + 1
    if pos == 'botleft' and pum_line <= line:
      line = 0
    elif ( pos == 'topleft' and
           pum_line >= line and
           pum_line < ( line + len( buf_lines ) ) ):
      line = 0

  if line <= 0:
    # Nowhere to put it so hide it
    if state.popup_win_id:
      # TODO/FIXME: Should we use popup_hide() instead ?
      vim.eval( "popup_close( {} )".format( state.popup_win_id ) )
    return SignatureHelpState( None, SignatureHelpState.INACTIVE )

  if int( screen_pos[ 'curscol' ] ) <= 1:
    col = 1
  else:
    # -1 for padding,
    # -1 for the trigger character inserted (the anchor is set _after_ the
    # character is inserted, so we remove it).
    # FIXME: multi-byte characters would be wrong. Need to set anchor before
    # inserting the char ?
    col = int( screen_pos[ 'curscol' ] ) - 2

  if col <= 0:
    col = 1

  options = {
    "line": line,
    "col": col,
    "pos": pos,
    "wrap": 0,
    # NOTE: We *dont'* use "cursorline" here - that actually uses PMenuSel,
    # which is just too invasive for us (it's more selected item than actual
    # cursorline. So instead, we manually set 'cursorline' in the popup window
    # and enable sytax based on the current file syntax)
    "flip": 1,
    "padding": [ 0, 1, 0, 1 ], # Pad 1 char in X axis to match completion menu
  }

  if not state.popup_win_id:
    state.popup_win_id = GetIntValue( "popup_create( {}, {} )".format(
      json.dumps( buf_lines ),
      json.dumps( options ) ) )
  else:
    vim.eval( 'popup_settext( {}, {} )'.format(
      state.popup_win_id,
      json.dumps( buf_lines ) ) )

  # Should do nothing if already visible
  vim.eval( 'popup_move( {}, {} )'.format( state.popup_win_id,
                                           json.dumps( options ) ) )
  vim.eval( 'popup_show( {} )'.format( state.popup_win_id ) )

  active_signature = int( signature_info.get( 'activeSignature', 0 ) )
  vim.eval( "win_execute( {}, 'set syntax={} cursorline | "
            "call cursor( [ {}, 1 ] )' )".format(
              state.popup_win_id,
              utils.ToUnicode( vim.current.buffer.options[ 'syntax' ] ),
              active_signature + 1 ) )

  return state

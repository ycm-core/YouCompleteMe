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


from ycm import vimsupport
from ycmd import utils

import vim
import json


# FIXME/TODO: Merge this with vimsupport funcitons, added after these were
# written. It's not trivial, as those vimsupport functions are a bit fiddly.
# They also support neovim, but we don't.
def AddTextPropertyType( name, **kwargs ):
  props = {
    'highlight': 'Ignore',
    'combine': False,
    'start_incl': False,
    'end_incl': False,
    'priority': 10
  }
  props.update( kwargs )

  vim.eval( f"prop_type_add( '{ vimsupport.EscapeForVim( name ) }', "
            f"               { json.dumps( kwargs ) } )" )


def GetTextPropertyTypes( *args, **kwargs ):
  return [ utils.ToUnicode( p ) for p in vim.eval( 'prop_type_list()' ) ]


def AddTextProperty( bufnr,
                     prop_id,
                     prop_type,
                     range,
                     extra_args: dict = None ):
  props = {
    'end_lnum': range[ 'end' ][ 'line_num' ],
    'end_col': range[ 'end' ][ 'column_num' ],
    'bufnr': bufnr,
    'type': prop_type
  }
  if prop_id is not None:
    props[ 'id' ]: prop_id
  if extra_args:
    props.update( extra_args )
  return vim.eval( f"prop_add( { range[ 'start' ][ 'line_num' ] },"
                   f"          { range[ 'start' ][ 'column_num' ] },"
                   f"          { json.dumps( props ) } )" )


def ClearTextProperties( bufnr, prop_id ):
  props = {
    'id': prop_id,
    'bufnr': bufnr,
    'all': 1,
  }
  vim.eval( f"prop_remove( { json.dumps( props ) } )" )

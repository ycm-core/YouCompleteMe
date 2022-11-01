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
from ycm.vimsupport import GetIntValue
from ycmd import utils

import vim
import json
import typing


# FIXME/TODO: Merge this with vimsupport funcitons, added after these were
# written. It's not trivial, as those vimsupport functions are a bit fiddly.
# They also support neovim, but we don't.
def AddTextPropertyType( name, **kwargs ):
  props = {
    'highlight': 'Ignore',
    'combine': 0,
    'override': 0,
    'start_incl': 0,
    'end_incl': 0,
    'priority': 10
  }
  props.update( kwargs )

  vim.eval( f"prop_type_add( '{ vimsupport.EscapeForVim( name ) }', "
            f"               { json.dumps( props ) } )" )


def GetTextPropertyTypes( *args, **kwargs ):
  return [ utils.ToUnicode( p ) for p in vim.eval( 'prop_type_list()' ) ]


def AddTextProperty( bufnr,
                     prop_id,
                     prop_type,
                     range,
                     extra_args: dict = None ):
  props = {
    'bufnr': bufnr,
    'type': prop_type
  }
  if prop_id is not None:
    props[ 'id' ] = prop_id
  if extra_args:
    props.update( extra_args )
  if 'end' in range:
    props.update( {
      'end_lnum': range[ 'end' ][ 'line_num' ],
      'end_col':  range[ 'end' ][ 'column_num' ],
    } )
  return vim.eval( f"prop_add( { range[ 'start' ][ 'line_num' ] },"
                   f"          { range[ 'start' ][ 'column_num' ] },"
                   f"          { json.dumps( props ) } )" )


def ClearTextProperties(
  bufnr,
  prop_id = None,
  prop_types: typing.Union[ typing.List[ str ], str ] = None,
  first_line = None,
  last_line = None ):

  props = {
    'bufnr': bufnr,
    'all': 1,
  }
  if prop_id is not None:
    props[ 'id' ] = prop_id

  if prop_id is not None and prop_types is not None:
    props[ 'both' ] = 1

  def prop_remove():
    if last_line is not None:
      return GetIntValue( f"prop_remove( { json.dumps( props ) },"
                                      f" { first_line },"
                                      f" { last_line } )" )
    elif first_line is not None:
      return GetIntValue( f"prop_remove( { json.dumps( props ) },"
                                      f" { first_line } )" )
    else:
      return GetIntValue( f"prop_remove( { json.dumps( props ) } )" )

  if prop_types is None:
    return prop_remove()

  if not isinstance( prop_types, list ):
    prop_types = [ prop_types ]

  # 9.0.233 added types list to prop_remove, so use that
  if vimsupport.VimVersionAtLeast( '9.0.233' ):
    props[ 'types' ] = prop_types
    return prop_remove()

  # Older versions we have to run prop_remove for each type
  removed = 0
  for prop_type in prop_types:
    props[ 'type' ] = prop_type
    removed += prop_remove()
  return removed

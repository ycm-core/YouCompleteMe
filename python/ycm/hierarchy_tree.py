# Copyright (C) 2024 YouCompleteMe contributors
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

from typing import Optional, List
from ycm import vimsupport
import os


class HierarchyNode:
  def __init__( self, data, distance : int ):
    self._references : Optional[List[int]] = None
    self._data = data
    self._distance_from_root = distance


  def ToLocation( self, subindex : int ):
    location = self._data[ 'locations' ][ subindex ]
    line = location[ 'line_num' ]
    column = location[ 'column_num' ]
    file = location[ 'filepath' ]
    return file, line, column



class HierarchyTree:
  def __init__( self ):
    self._up_nodes : List[HierarchyNode] = []
    self._down_nodes : List[HierarchyNode] = []
    self._kind : str = ''

  def SetRootNode( self, items, kind : str ):
    if items:
      assert len( items ) == 1
      self._root_node_indices = [ 0 ]
      self._down_nodes.append( HierarchyNode( items[ 0 ], 0 ) )
      self._up_nodes.append( HierarchyNode( items[ 0 ], 0 ) )
      self._kind = kind
      return self.HierarchyToLines()
    return []


  def UpdateHierarchy( self, handle : int, items, direction : str ):
    current_index = abs( handle ) // 1000000
    nodes = self._down_nodes if direction == 'down' else self._up_nodes
    if items:
      nodes.extend( [
        HierarchyNode( item,
                       nodes[ current_index ]._distance_from_root + 1 )
        for item in items ] )
      nodes[ current_index ]._references = list(
          range( len( nodes ) - len( items ),
                 len( nodes ) ) )
    else:
      nodes[ current_index ]._references = []


  def Reset( self ):
    self._down_nodes = []
    self._up_nodes = []
    self._kind = ''


  def _HierarchyToLinesHelper( self, refs, use_down_nodes ):
    partial_result = []
    nodes = self._down_nodes if use_down_nodes else self._up_nodes
    for i in refs:
      next_node = nodes[ i ]
      indent = 2 * next_node._distance_from_root
      if i == 0:
        can_expand = self._down_nodes[ 0 ]._references is None or self._up_nodes[ 0 ]._references is None
      else:
        can_expand = next_node._references is None
      symbol = '+' if can_expand else '-'
      name = next_node._data[ 'name' ]
      kind = next_node._data[ 'kind' ]
      if use_down_nodes:
        partial_result.extend( [
          ( ' ' * indent + symbol + kind + ': ' + name + '\t' +
              os.path.split( l[ 'filepath' ] )[ 1 ] + ':' +
              str( l[ 'line_num' ] ) + '\t' + l[ 'description' ],
            ( i * 1000000 + j ) )
          for j, l in enumerate( next_node._data[ 'locations' ] ) ] )
      else:
        partial_result.extend( [
          ( ' ' * indent + symbol + kind + ': ' + name + '\t' +
              os.path.split( l[ 'filepath' ] )[ 1 ] + ':' +
              str( l[ 'line_num' ] ) + '\t' + l[ 'description' ],
            ( i * 1000000 + j ) * -1 )
          for j, l in enumerate( next_node._data[ 'locations' ] ) ] )
      if next_node._references:
        partial_result.extend(
          self._HierarchyToLinesHelper( next_node._references, use_down_nodes ) )
    return partial_result

  def HierarchyToLines( self ):
    down_lines = self._HierarchyToLinesHelper( [ 0 ], True )
    up_lines = self._HierarchyToLinesHelper( [ 0 ], False )
    up_lines.reverse()
    return up_lines + down_lines[ 1: ]


  def JumpToItem( self, handle : int, command ):
    node_index = abs( handle ) // 1000000
    location_index = abs( handle ) % 1000000
    if handle >= 0:
      node = self._down_nodes[ node_index ]
    else:
      node = self._up_nodes[ node_index ]
    file, line, column = node.ToLocation( location_index )
    vimsupport.JumpToLocation( file, line, column, '', command )


  def ShouldResolveItem( self, handle : int, direction : str ):
    node_index = abs( handle ) // 1000000
    if direction == 'down':
      node = self._down_nodes[ node_index ]
    else:
      node = self._up_nodes[ node_index ]
    return node._references is None


  def ResolveArguments( self, handle : int, direction : str ):
    node_index = abs( handle ) // 1000000
    if self._kind == 'call':
      direction = 'outgoing' if direction == 'up' else 'incoming'
    else:
      direction = 'supertypes' if direction == 'up' else 'subtypes'
    if handle >= 0:
      node = self._down_nodes[ node_index ]
    else:
      node = self._up_nodes[ node_index ]
    return [
      f'Resolve{ self._kind.title() }HierarchyItem',
      node._data,
      direction
    ]

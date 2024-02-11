# Copyright (C) 2011-2024 YouCompleteMe contributors
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
    self._nodes : List[HierarchyNode] = []
    self._kind : str = ''
    self._direction : str = ''

  def SetRootNode( self, items, kind : str, direction : str ):
    if items:
      self._root_node_indices = list( range( 0, len( items ) ) )
      self._nodes.append( HierarchyNode( items[ 0 ], 0 ) )
      self._kind = kind
      self._direction = direction
      return self.HierarchyToLines( is_root_node = True )
    return []


  def UpdateHierarchy( self, handle : int, items ):
    current_index = handle // 1000000
    if items:
      self._nodes.extend( [
        HierarchyNode( item,
                       self._nodes[ current_index ]._distance_from_root + 1 )
        for item in items ] )
      self._nodes[ current_index ]._references = list(
          range( len( self._nodes ) - len( items ),
                 len( self._nodes ) ) )
    else:
      self._nodes[ current_index ]._references = []


  def Reset( self ):
    self._nodes = []


  def _HierarchyToLinesHelper( self, refs, is_root_node = False ):
    partial_result = []
    for i in refs:
      next_node = self._nodes[ i ]
      indent = 2 * next_node._distance_from_root
      can_expand = next_node._references is None
      symbol = '+' if can_expand else '-'
      name = next_node._data[ 'name' ]
      kind = next_node._data[ 'kind' ]
      partial_result.extend( [
        ( ' ' * indent + symbol + kind + ': ' + name + '\t' +
            os.path.split( l[ 'filepath' ] )[ 1 ] + ':' +
            str( l[ 'line_num' ] ) + '\t' + l[ 'description' ],
          i * 1000000 + j )
        for j, l in enumerate( next_node._data[ 'locations' ] ) ] )
      if next_node._references:
        partial_result.extend(
          self._HierarchyToLinesHelper( next_node._references, is_root_node ) )
    return partial_result

  def HierarchyToLines( self, is_root_node = False ):
    lines = []
    for i in self._root_node_indices:
      lines.extend( self._HierarchyToLinesHelper( [ i ], is_root_node ) )
    return lines


  def JumpToItem( self, handle : int, command ):
    node_index = handle // 1000000
    location_index = handle % 1000000
    node = self._nodes[ node_index ]
    file, line, column = node.ToLocation( location_index )
    vimsupport.JumpToLocation( file, line, column, '', command )


  def ShouldResolveItem( self, handle : int ):
    node_index = handle // 1000000
    return self._nodes[ node_index ]._references is None


  def ResolveArguments( self, handle : int ):
    node_index = handle // 1000000
    return [
      f'Resolve{ self._kind.title() }HierarchyItem',
      self._nodes[ node_index ]._data,
      self._direction
    ]

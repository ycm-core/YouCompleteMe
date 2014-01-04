#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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

from collections import defaultdict
from operator import itemgetter
from ycm import vimsupport


class DiagnosticInterface( object ):
  def __init__( self ):
    self._buffer_number_to_diags = {}
    self._next_sign_id = 1


  def UpdateWithNewDiagnostics( self, diags ):
    self._buffer_number_to_diags = ConvertDiagListToDict( diags )
    for buffer_number, buffer_diags in self._buffer_number_to_diags.iteritems():
      if not vimsupport.BufferIsVisible( buffer_number ):
        continue

      vimsupport.UnplaceAllSignsInBuffer( buffer_number )
      for diag in buffer_diags:
        vimsupport.PlaceSign( self._next_sign_id,
                              diag[ 'lnum' ],
                              buffer_number,
                              diag[ 'type' ] == 'E' )
        self._next_sign_id += 1


def ConvertDiagListToDict( diags ):
  buffer_to_diags = defaultdict( list )
  for diag in diags:
    buffer_to_diags[ diag[ 'bufnr' ] ].append( diag )
  for buffer_diags in buffer_to_diags.itervalues():
    # We also want errors to be listed before warnings so that errors aren't
    # hidden by the warnings; Vim won't place a sign oven an existing one.
    buffer_diags.sort( key = lambda diag: itemgetter( 'lnum', 'col', 'type' ) )
  return buffer_to_diags


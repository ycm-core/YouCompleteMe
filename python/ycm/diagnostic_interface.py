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
import vim


class DiagnosticInterface( object ):
  def __init__( self ):
    # Line and column numbers are 1-based
    self._buffer_number_to_line_to_diags = defaultdict(
      lambda: defaultdict( list ) )
    self._next_sign_id = 1
    self._previous_line_number = -1


  def OnCursorMoved( self ):
    line, _ = vimsupport.CurrentLineAndColumn()
    line += 1  # Convert to 1-based
    if line != self._previous_line_number:
      self._previous_line_number = line
      self._EchoDiagnosticForLine( line )


  def UpdateWithNewDiagnostics( self, diags ):
    self._buffer_number_to_line_to_diags = _ConvertDiagListToDict( diags )
    self._next_sign_id = _UpdateSigns( self._buffer_number_to_line_to_diags,
                                       self._next_sign_id )
    _UpdateSquiggles( self._buffer_number_to_line_to_diags )


  def _EchoDiagnosticForLine( self, line_num ):
    buffer_num = vim.current.buffer.number
    diags = self._buffer_number_to_line_to_diags[ buffer_num ][ line_num ]
    if not diags:
      # Clear any previous diag echo
      vimsupport.EchoText( '', False )
      return
    vimsupport.EchoTextVimWidth( diags[ 0 ][ 'text' ] )


def _UpdateSquiggles( buffer_number_to_line_to_diags ):
  vimsupport.ClearYcmSyntaxMatches()
  line_to_diags = buffer_number_to_line_to_diags[ vim.current.buffer.number ]

  for diags in line_to_diags.itervalues():
    for diag in diags:
      vimsupport.AddDiagnosticSyntaxMatch( diag[ 'lnum' ],
                                           diag[ 'col' ],
                                           _DiagnosticIsError( diag ) )


def _UpdateSigns( buffer_number_to_line_to_diags, next_sign_id ):
  vimsupport.UnplaceAllSignsInBuffer( vim.current.buffer.number )
  for buffer_number, line_to_diags in buffer_number_to_line_to_diags.iteritems():
    if not vimsupport.BufferIsVisible( buffer_number ):
      continue

    vimsupport.UnplaceAllSignsInBuffer( buffer_number )
    for line, diags in line_to_diags.iteritems():
      for diag in diags:
        vimsupport.PlaceSign( next_sign_id,
                              line,
                              buffer_number,
                              _DiagnosticIsError( diag ) )
        next_sign_id += 1
  return next_sign_id


def _ConvertDiagListToDict( diag_list ):
  buffer_to_line_to_diags = defaultdict( lambda: defaultdict( list ) )
  for diag in diag_list:
    buffer_to_line_to_diags[ diag[ 'bufnr' ] ][ diag[ 'lnum' ] ].append( diag )
  for line_to_diags in buffer_to_line_to_diags.itervalues():
    for diags in line_to_diags.itervalues():
      # We also want errors to be listed before warnings so that errors aren't
      # hidden by the warnings; Vim won't place a sign oven an existing one.
      diags.sort( key = lambda diag: itemgetter( 'col', 'type' ) )
  return buffer_to_line_to_diags


def _DiagnosticIsError( diag ):
  return diag[ 'type' ] == 'E'


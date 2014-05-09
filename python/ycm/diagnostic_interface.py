#!/usr/bin/env python
#
# Copyright (C) 2013  Google Inc.
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
from ycm import vimsupport
import vim


class DiagnosticInterface( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    # Line and column numbers are 1-based
    self._buffer_number_to_line_to_diags = defaultdict(
      lambda: defaultdict( list ) )
    self._next_sign_id = 1
    self._previous_line_number = -1
    self._diag_message_needs_clearing = False


  def OnCursorMoved( self ):
    line, _ = vimsupport.CurrentLineAndColumn()
    line += 1  # Convert to 1-based
    if line != self._previous_line_number:
      self._previous_line_number = line

      if self._user_options[ 'echo_current_diagnostic' ]:
        self._EchoDiagnosticForLine( line )


  def UpdateWithNewDiagnostics( self, diags ):
    self._buffer_number_to_line_to_diags = _ConvertDiagListToDict( diags )

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._next_sign_id = _UpdateSigns( self._buffer_number_to_line_to_diags,
                                         self._next_sign_id )

    if self._user_options[ 'enable_diagnostic_highlighting' ]:
      _UpdateSquiggles( self._buffer_number_to_line_to_diags )

    if self._user_options[ 'always_populate_location_list' ]:
      vimsupport.SetLocationList(
        vimsupport.ConvertDiagnosticsToQfList( diags ) )


  def _EchoDiagnosticForLine( self, line_num ):
    buffer_num = vim.current.buffer.number
    diags = self._buffer_number_to_line_to_diags[ buffer_num ][ line_num ]
    if not diags:
      if self._diag_message_needs_clearing:
        # Clear any previous diag echo
        vimsupport.EchoText( '', False )
        self._diag_message_needs_clearing = False
      return
    vimsupport.EchoTextVimWidth( diags[ 0 ][ 'text' ] )
    self._diag_message_needs_clearing = True


def _UpdateSquiggles( buffer_number_to_line_to_diags ):
  vimsupport.ClearYcmSyntaxMatches()
  line_to_diags = buffer_number_to_line_to_diags[ vim.current.buffer.number ]

  for diags in line_to_diags.itervalues():
    for diag in diags:
      location_extent = diag[ 'location_extent' ]
      is_error = _DiagnosticIsError( diag )

      if location_extent[ 'start' ][ 'line_num' ] < 0:
        location = diag[ 'location' ]
        vimsupport.AddDiagnosticSyntaxMatch(
            location[ 'line_num' ],
            location[ 'column_num' ] )
      else:
        vimsupport.AddDiagnosticSyntaxMatch(
          location_extent[ 'start' ][ 'line_num' ],
          location_extent[ 'start' ][ 'column_num' ],
          location_extent[ 'end' ][ 'line_num' ],
          location_extent[ 'end' ][ 'column_num' ],
          is_error = is_error )

      for diag_range in diag[ 'ranges' ]:
        vimsupport.AddDiagnosticSyntaxMatch(
          diag_range[ 'start' ][ 'line_num' ],
          diag_range[ 'start' ][ 'column_num' ],
          diag_range[ 'end' ][ 'line_num' ],
          diag_range[ 'end' ][ 'column_num' ],
          is_error = is_error )


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
    location = diag[ 'location' ]
    buffer_number = vimsupport.GetBufferNumberForFilename(
      location[ 'filepath' ] )
    line_number = location[ 'line_num' ]
    buffer_to_line_to_diags[ buffer_number ][ line_number ].append( diag )

  for line_to_diags in buffer_to_line_to_diags.itervalues():
    for diags in line_to_diags.itervalues():
      # We also want errors to be listed before warnings so that errors aren't
      # hidden by the warnings; Vim won't place a sign oven an existing one.
      diags.sort( key = lambda diag: ( diag[ 'location' ][ 'column_num' ],
                                       diag[ 'kind' ] ) )
  return buffer_to_line_to_diags


def _DiagnosticIsError( diag ):
  return diag[ 'kind' ] == 'E'


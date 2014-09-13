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

from collections import defaultdict, namedtuple
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
    self._placed_signs = []


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
      self._placed_signs, self._next_sign_id = _UpdateSigns(
        self._placed_signs,
        self._buffer_number_to_line_to_diags,
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


def _UpdateSigns( placed_signs, buffer_number_to_line_to_diags, next_sign_id ):
  new_signs, kept_signs, next_sign_id = _GetKeptAndNewSigns(
    placed_signs, buffer_number_to_line_to_diags, next_sign_id
  )
  # Dummy sign used to prevent "flickering" in vim when last mark gets
  # deleted from buffer. Dummy sign prevent vim to collapse sign column in
  # that case.
  # There also a vim "bug", which cause whole window to redraw in some
  # conditions (vim redraw logic is very complex). But, somehow, if we place
  # dummy sign before placing other real visible sign, it will not redraw the
  # buffer (patch to vim pending).
  dummy_sign_needed = False
  if kept_signs == [] and new_signs != []:
    dummy_sign_needed = True

  if dummy_sign_needed:
    vimsupport.PlaceDummySign( next_sign_id + 1, vim.current.buffer.number,
      new_signs[0].line )

  # Now we can place only that signs that are not placed yet.
  new_placed_signs = _PlaceNewSigns( kept_signs, new_signs )

  # We use incremental placement, so signs that already placed on right lines
  # will not be deleted and placed again, which should improve performance in
  # case of many diags.
  # Signs which are not exist in current diag should be deleted.
  _UnplaceRottenSigns( kept_signs, placed_signs )

  if dummy_sign_needed:
    vimsupport.UnPlaceDummySign( next_sign_id + 1, vim.current.buffer.number )

  return new_placed_signs, next_sign_id

def _GetKeptAndNewSigns( placed_signs, buffer_number_to_line_to_diags,
                         next_sign_id ):
  new_signs = []
  kept_signs = []
  for buffer_number, line_to_diags in buffer_number_to_line_to_diags.iteritems():
    if not vimsupport.BufferIsVisible( buffer_number ):
      continue

    for line, diags in line_to_diags.iteritems():
      for diag in diags:
        sign = _DiagSignPlacement( next_sign_id,
                                   line,
                                   buffer_number,
                                   _DiagnosticIsError( diag ) )
        if sign not in placed_signs:
          new_signs += [ sign ]
          next_sign_id += 1
        else:
          # We should use .index here because of `sign` contains new id, but
          # we need old id to unplace sign in future.
          kept_signs += [ placed_signs[ placed_signs.index( sign ) ] ]
  return new_signs, kept_signs, next_sign_id



def _PlaceNewSigns( kept_signs, new_signs ):
  placed_signs = kept_signs
  for sign in new_signs:
    # Do not add two signs at the same line, it will screw signs remembering.
    if sign in placed_signs:
      continue
    vimsupport.PlaceSign( sign.id, sign.line, sign.buffer, sign.is_err )
    placed_signs += [ sign ]
  return placed_signs


def _UnplaceRottenSigns( kept_signs, placed_signs ):
  for sign in placed_signs:
    if sign not in kept_signs:
      print("rotten", sign)
      vimsupport.UnplaceSignInBuffer( sign.buffer, sign.id )


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
  return diag[ 'kind' ] == 'ERROR'


class _DiagSignPlacement(namedtuple( "_DiagSignPlacement",
                                     [ 'id', 'line', 'buffer', 'is_err' ])):
  def __eq__(self, another_sign):
    if self.line != another_sign.line:
      return False
    if self.buffer != another_sign.buffer:
      return False
    if self.is_err != another_sign.is_err:
      return False
    return True

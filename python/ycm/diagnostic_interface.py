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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from future.utils import itervalues, iteritems
from collections import defaultdict, namedtuple
from ycm import vimsupport
from ycm.diagnostic_filter import DiagnosticFilter, CompileLevel
import vim


class DiagnosticInterface( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    self._diagnostics = []
    self._diag_filter = DiagnosticFilter.CreateFromOptions( user_options )
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


  def GetErrorCount( self ):
    return len( self._FilterDiagnostics( _DiagnosticIsError ) )


  def GetWarningCount( self ):
    return len( self._FilterDiagnostics( _DiagnosticIsWarning ) )


  def PopulateLocationList( self ):
    # Do nothing if loc list is already populated by diag_interface
    if not self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationList()
    return bool( self._diagnostics )


  def UpdateWithNewDiagnostics( self, diags ):
    self._diagnostics = [ _NormalizeDiagnostic( x ) for x in
                            self._ApplyDiagnosticFilter( diags ) ]
    self._buffer_number_to_line_to_diags = _ConvertDiagListToDict(
        self._diagnostics )

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._placed_signs, self._next_sign_id = _UpdateSigns(
        self._placed_signs,
        self._buffer_number_to_line_to_diags,
        self._next_sign_id )

    if self._user_options[ 'enable_diagnostic_highlighting' ]:
      _UpdateSquiggles( self._buffer_number_to_line_to_diags )

    if self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationList()


  def _ApplyDiagnosticFilter( self, diags, extra_predicate = None ):
    filetypes = vimsupport.CurrentFiletypes()
    diag_filter = self._diag_filter.SubsetForTypes( filetypes )
    predicate = diag_filter.IsAllowed
    if extra_predicate is not None:
      def Filter( diag ):
        return extra_predicate( diag ) and diag_filter.IsAllowed( diag )

      predicate = Filter

    return filter( predicate, diags )


  def _EchoDiagnosticForLine( self, line_num ):
    buffer_num = vim.current.buffer.number
    diags = self._buffer_number_to_line_to_diags[ buffer_num ][ line_num ]
    if not diags:
      if self._diag_message_needs_clearing:
        # Clear any previous diag echo
        vimsupport.PostVimMessage( '', warning = False )
        self._diag_message_needs_clearing = False
      return

    first_diag = diags[ 0 ]
    text = first_diag[ 'text' ]
    if first_diag.get( 'fixit_available', False ):
      text += ' (FixIt)'

    vimsupport.PostVimMessage( text, warning = False, truncate = True )
    self._diag_message_needs_clearing = True


  def _FilterDiagnostics( self, predicate ):
    matched_diags = []
    line_to_diags = self._buffer_number_to_line_to_diags[
      vim.current.buffer.number ]

    for diags in itervalues( line_to_diags ):
      matched_diags.extend( list(
        self._ApplyDiagnosticFilter( diags, predicate ) ) )
    return matched_diags


  def _UpdateLocationList( self ):
    vimsupport.SetLocationList(
      vimsupport.ConvertDiagnosticsToQfList( self._diagnostics ) )


def _UpdateSquiggles( buffer_number_to_line_to_diags ):
  vimsupport.ClearYcmSyntaxMatches()
  line_to_diags = buffer_number_to_line_to_diags[ vim.current.buffer.number ]

  for diags in itervalues( line_to_diags ):
    # Insert squiggles in reverse order so that errors overlap warnings.
    for diag in reversed( diags ):
      location_extent = diag[ 'location_extent' ]
      is_error = _DiagnosticIsError( diag )

      if location_extent[ 'start' ][ 'line_num' ] <= 0:
        location = diag[ 'location' ]
        vimsupport.AddDiagnosticSyntaxMatch(
          location[ 'line_num' ],
          location[ 'column_num' ],
          is_error = is_error )
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
  # Dummy sign used to prevent "flickering" in Vim when last mark gets
  # deleted from buffer. Dummy sign prevents Vim to collapsing the sign column
  # in that case.
  # There's also a vim bug which causes the whole window to redraw in some
  # conditions (vim redraw logic is very complex). But, somehow, if we place a
  # dummy sign before placing other "real" signs, it will not redraw the
  # buffer (patch to vim pending).
  dummy_sign_needed = not kept_signs and new_signs

  if dummy_sign_needed:
    vimsupport.PlaceDummySign( next_sign_id + 1,
                               vim.current.buffer.number,
                               new_signs[ 0 ].line )

  # We place only those signs that haven't been placed yet.
  new_placed_signs = _PlaceNewSigns( kept_signs, new_signs )

  # We use incremental placement, so signs that already placed on the correct
  # lines will not be deleted and placed again, which should improve performance
  # in case of many diags. Signs which don't exist in the current diag should be
  # deleted.
  _UnplaceObsoleteSigns( kept_signs, placed_signs )

  if dummy_sign_needed:
    vimsupport.UnPlaceDummySign( next_sign_id + 1, vim.current.buffer.number )

  return new_placed_signs, next_sign_id


def _GetKeptAndNewSigns( placed_signs, buffer_number_to_line_to_diags,
                         next_sign_id ):
  new_signs = []
  kept_signs = []
  for buffer_number, line_to_diags in iteritems(
                                            buffer_number_to_line_to_diags ):
    if not vimsupport.BufferIsVisible( buffer_number ):
      continue

    for line, diags in iteritems( line_to_diags ):
      # Only one sign is visible by line.
      first_diag = diags[ 0 ]
      sign = _DiagSignPlacement( next_sign_id,
                                 line,
                                 buffer_number,
                                 _DiagnosticIsError( first_diag ) )
      if sign not in placed_signs:
        new_signs.append( sign )
        next_sign_id += 1
      else:
        # We use .index here because `sign` contains a new id, but
        # we need the sign with the old id to unplace it later on.
        # We won't be placing the new sign.
        kept_signs.append( placed_signs[ placed_signs.index( sign ) ] )
  return new_signs, kept_signs, next_sign_id


def _PlaceNewSigns( kept_signs, new_signs ):
  placed_signs = kept_signs[:]
  for sign in new_signs:
    # Do not set two signs on the same line, it will screw up storing sign
    # locations.
    if sign in placed_signs:
      continue
    vimsupport.PlaceSign( sign.id, sign.line, sign.buffer, sign.is_error )
    placed_signs.append( sign )
  return placed_signs


def _UnplaceObsoleteSigns( kept_signs, placed_signs ):
  for sign in placed_signs:
    if sign not in kept_signs:
      vimsupport.UnplaceSignInBuffer( sign.buffer, sign.id )


def _ConvertDiagListToDict( diag_list ):
  buffer_to_line_to_diags = defaultdict( lambda: defaultdict( list ) )
  for diag in diag_list:
    location = diag[ 'location' ]
    buffer_number = vimsupport.GetBufferNumberForFilename(
      location[ 'filepath' ] )
    line_number = location[ 'line_num' ]
    buffer_to_line_to_diags[ buffer_number ][ line_number ].append( diag )

  for line_to_diags in itervalues( buffer_to_line_to_diags ):
    for diags in itervalues( line_to_diags ):
      # We want errors to be listed before warnings so that errors aren't hidden
      # by the warnings.
      diags.sort( key = lambda diag: ( diag[ 'kind' ],
                                       diag[ 'location' ][ 'column_num' ] ) )
  return buffer_to_line_to_diags


_DiagnosticIsError = CompileLevel( 'error' )
_DiagnosticIsWarning = CompileLevel( 'warning' )


def _NormalizeDiagnostic( diag ):
  def ClampToOne( value ):
    return value if value > 0 else 1

  location = diag[ 'location' ]
  location[ 'column_num' ] = ClampToOne( location[ 'column_num' ] )
  location[ 'line_num' ] = ClampToOne( location[ 'line_num' ] )
  return diag


class _DiagSignPlacement(
                    namedtuple( "_DiagSignPlacement",
                                [ 'id', 'line', 'buffer', 'is_error' ] ) ):
  # We want two signs that have different ids but the same location to compare
  # equal. ID doesn't matter.
  def __eq__( self, other ):
    return ( self.line == other.line and
             self.buffer == other.buffer and
             self.is_error == other.is_error )

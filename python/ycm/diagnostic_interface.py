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


class DiagnosticInterface( object ):
  def __init__( self, bufnr, user_options ):
    self._bufnr = bufnr
    self._user_options = user_options
    self._diagnostics = []
    self._diag_filter = DiagnosticFilter.CreateFromOptions( user_options )
    # Line and column numbers are 1-based
    self._line_to_diags = defaultdict( list )
    self._placed_signs = []
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


  def GetErrorCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsError )


  def GetWarningCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsWarning )


  def PopulateLocationList( self ):
    # Do nothing if loc list is already populated by diag_interface
    if not self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationList()
    return bool( self._diagnostics )


  def UpdateWithNewDiagnostics( self, diags ):
    self._diagnostics = [ _NormalizeDiagnostic( x ) for x in
                            self._ApplyDiagnosticFilter( diags ) ]
    self._ConvertDiagListToDict()

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._UpdateSigns()

    if self._user_options[ 'enable_diagnostic_highlighting' ]:
      self._UpdateSquiggles()

    if self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationList()


  def _ApplyDiagnosticFilter( self, diags ):
    filetypes = vimsupport.GetBufferFiletypes( self._bufnr )
    diag_filter = self._diag_filter.SubsetForTypes( filetypes )
    return filter( diag_filter.IsAllowed, diags )


  def _EchoDiagnosticForLine( self, line_num ):
    diags = self._line_to_diags[ line_num ]
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


  def _DiagnosticsCount( self, predicate ):
    count = 0
    for diags in itervalues( self._line_to_diags ):
      count += sum( 1 for d in diags if predicate( d ) )
    return count


  def _UpdateLocationList( self ):
    vimsupport.SetLocationList(
      vimsupport.ConvertDiagnosticsToQfList( self._diagnostics ) )


  def _UpdateSquiggles( self ):

    vimsupport.ClearYcmSyntaxMatches()

    for diags in itervalues( self._line_to_diags ):
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


  def _UpdateSigns( self ):
    new_signs, obsolete_signs = self._GetNewAndObsoleteSigns()

    self._PlaceNewSigns( new_signs )

    self._UnplaceObsoleteSigns( obsolete_signs )


  def _GetNewAndObsoleteSigns( self ):
    new_signs = []
    obsolete_signs = list( self._placed_signs )
    for line, diags in iteritems( self._line_to_diags ):
      # We always go for the first diagnostic on line,
      # because it is sorted giving priority to the Errors.
      diag = diags[ 0 ]
      sign = _DiagSignPlacement( self._next_sign_id,
                                 line, _DiagnosticIsError( diag ) )
      try:
        obsolete_signs.remove( sign )
      except ValueError:
        new_signs.append( sign )
        self._next_sign_id += 1
    return new_signs, obsolete_signs


  def _PlaceNewSigns( self, new_signs ):
    for sign in new_signs:
      vimsupport.PlaceSign( sign.id, sign.line, self._bufnr, sign.is_error )
      self._placed_signs.append( sign )


  def _UnplaceObsoleteSigns( self, obsolete_signs ):
    for sign in obsolete_signs:
      self._placed_signs.remove( sign )
      vimsupport.UnplaceSignInBuffer( self._bufnr, sign.id )


  def _ConvertDiagListToDict( self ):
    self._line_to_diags = defaultdict( list )
    for diag in self._diagnostics:
      location = diag[ 'location' ]
      bufnr = vimsupport.GetBufferNumberForFilename( location[ 'filepath' ] )
      if bufnr == self._bufnr:
        line_number = location[ 'line_num' ]
        self._line_to_diags[ line_number ].append( diag )

    for diags in itervalues( self._line_to_diags ):
      # We also want errors to be listed before warnings so that errors aren't
      # hidden by the warnings; Vim won't place a sign over an existing one.
      diags.sort( key = lambda diag: ( diag[ 'kind' ],
                                       diag[ 'location' ][ 'column_num' ] ) )


_DiagnosticIsError = CompileLevel( 'error' )
_DiagnosticIsWarning = CompileLevel( 'warning' )


def _NormalizeDiagnostic( diag ):
  def ClampToOne( value ):
    return value if value > 0 else 1

  location = diag[ 'location' ]
  location[ 'column_num' ] = ClampToOne( location[ 'column_num' ] )
  location[ 'line_num' ] = ClampToOne( location[ 'line_num' ] )
  return diag


class _DiagSignPlacement( namedtuple( "_DiagSignPlacement",
                                      [ 'id', 'line', 'is_error' ] ) ):
  # We want two signs that have different ids but the same location to compare
  # equal. ID doesn't matter.
  def __eq__( self, other ):
    return ( self.line == other.line and
             self.is_error == other.is_error )

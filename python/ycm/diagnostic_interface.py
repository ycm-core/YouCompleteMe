# Copyright (C) 2013-2018 YouCompleteMe contributors
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
from collections import defaultdict
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
    self._previous_diag_line_number = -1
    self._diag_message_needs_clearing = False


  def OnCursorMoved( self ):
    if self._user_options[ 'echo_current_diagnostic' ]:
      line, _ = vimsupport.CurrentLineAndColumn()
      line += 1  # Convert to 1-based
      if line != self._previous_diag_line_number:
        self._EchoDiagnosticForLine( line )


  def GetErrorCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsError )


  def GetWarningCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsWarning )


  def PopulateLocationList( self ):
    # Do nothing if loc list is already populated by diag_interface
    if not self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationLists()
    return bool( self._diagnostics )


  def UpdateWithNewDiagnostics( self, diags ):
    self._diagnostics = [ _NormalizeDiagnostic( x ) for x in
                            self._ApplyDiagnosticFilter( diags ) ]
    self._ConvertDiagListToDict()

    if self._user_options[ 'echo_current_diagnostic' ]:
      self._EchoDiagnostic()

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._UpdateSigns()

    self.UpdateMatches()

    if self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationLists()


  def _ApplyDiagnosticFilter( self, diags ):
    filetypes = vimsupport.GetBufferFiletypes( self._bufnr )
    diag_filter = self._diag_filter.SubsetForTypes( filetypes )
    return filter( diag_filter.IsAllowed, diags )


  def _EchoDiagnostic( self ):
    line, _ = vimsupport.CurrentLineAndColumn()
    line += 1  # Convert to 1-based
    self._EchoDiagnosticForLine( line )


  def _EchoDiagnosticForLine( self, line_num ):
    self._previous_diag_line_number = line_num

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


  def _UpdateLocationLists( self ):
    vimsupport.SetLocationListsForBuffer(
      self._bufnr,
      vimsupport.ConvertDiagnosticsToQfList( self._diagnostics ) )


  def UpdateMatches( self ):
    if not self._user_options[ 'enable_diagnostic_highlighting' ]:
      return

    with vimsupport.CurrentWindow():
      for window in vimsupport.GetWindowsForBufferNumber( self._bufnr ):
        vimsupport.SwitchWindow( window )

        matches_to_remove = vimsupport.GetDiagnosticMatchesInCurrentWindow()

        for diags in itervalues( self._line_to_diags ):
          # Insert squiggles in reverse order so that errors overlap warnings.
          for diag in reversed( diags ):
            group = ( 'YcmErrorSection' if _DiagnosticIsError( diag ) else
                      'YcmWarningSection' )

            for pattern in _ConvertDiagnosticToMatchPatterns( diag ):
              # The id doesn't matter for matches that we may add.
              match = vimsupport.DiagnosticMatch( 0, group, pattern )
              try:
                matches_to_remove.remove( match )
              except ValueError:
                vimsupport.AddDiagnosticMatch( match )

        for match in matches_to_remove:
          vimsupport.RemoveDiagnosticMatch( match )


  def _UpdateSigns( self ):
    signs_to_unplace = vimsupport.GetSignsInBuffer( self._bufnr )

    for line, diags in iteritems( self._line_to_diags ):
      if not diags:
        continue

      # We always go for the first diagnostic on the line because diagnostics
      # are sorted by errors in priority and Vim can only display one sign by
      # line.
      name = 'YcmError' if _DiagnosticIsError( diags[ 0 ] ) else 'YcmWarning'
      sign = vimsupport.CreateSign( line, name, self._bufnr )

      try:
        signs_to_unplace.remove( sign )
      except ValueError:
        vimsupport.PlaceSign( sign )

    for sign in signs_to_unplace:
      vimsupport.UnplaceSign( sign )


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


def _ConvertDiagnosticToMatchPatterns( diagnostic ):
  patterns = []

  location_extent = diagnostic[ 'location_extent' ]
  if location_extent[ 'start' ][ 'line_num' ] <= 0:
    location = diagnostic[ 'location' ]
    patterns.append( vimsupport.GetDiagnosticMatchPattern(
      location[ 'line_num' ],
      location[ 'column_num' ] ) )
  else:
    patterns.append( vimsupport.GetDiagnosticMatchPattern(
      location_extent[ 'start' ][ 'line_num' ],
      location_extent[ 'start' ][ 'column_num' ],
      location_extent[ 'end' ][ 'line_num' ],
      location_extent[ 'end' ][ 'column_num' ] ) )

  for diagnostic_range in diagnostic[ 'ranges' ]:
    patterns.append( vimsupport.GetDiagnosticMatchPattern(
      diagnostic_range[ 'start' ][ 'line_num' ],
      diagnostic_range[ 'start' ][ 'column_num' ],
      diagnostic_range[ 'end' ][ 'line_num' ],
      diagnostic_range[ 'end' ][ 'column_num' ] ) )

  return patterns

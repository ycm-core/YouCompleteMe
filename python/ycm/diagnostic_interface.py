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

from collections import defaultdict
from ycm import vimsupport
from ycm.diagnostic_filter import DiagnosticFilter, CompileLevel
from ycm import text_properties as tp
import vim
YCM_VIM_PROPERTY_ID = 1


class DiagnosticInterface:
  def __init__( self, bufnr, user_options ):
    self._bufnr = bufnr
    self._user_options = user_options
    self._diagnostics = []
    self._diag_filter = DiagnosticFilter.CreateFromOptions( user_options )
    # Line and column numbers are 1-based
    self._line_to_diags = defaultdict( list )
    self._previous_diag_line_number = -1
    self._diag_message_needs_clearing = False


  def ShouldUpdateDiagnosticsUINow( self ):
    return ( self._user_options[ 'update_diagnostics_in_insert_mode' ] or
             'i' not in vim.eval( 'mode()' ) )


  def OnCursorMoved( self ):
    if self._user_options[ 'echo_current_diagnostic' ]:
      line, _ = vimsupport.CurrentLineAndColumn()
      line += 1  # Convert to 1-based
      if ( not self.ShouldUpdateDiagnosticsUINow() and
           self._diag_message_needs_clearing ):
        # Clear any previously echo'd diagnostic in insert mode
        self._EchoDiagnosticText( line, None, None )
      elif line != self._previous_diag_line_number:
        self._EchoDiagnosticForLine( line )


  def GetErrorCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsError )


  def GetWarningCount( self ):
    return self._DiagnosticsCount( _DiagnosticIsWarning )


  def PopulateLocationList( self, open_on_edit = False ):
    # Do nothing if loc list is already populated by diag_interface
    if not self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationLists( open_on_edit )
    return bool( self._diagnostics )


  def UpdateWithNewDiagnostics( self, diags, open_on_edit = False ):
    self._diagnostics = [ _NormalizeDiagnostic( x ) for x in
                            self._ApplyDiagnosticFilter( diags ) ]
    self._ConvertDiagListToDict()

    if self.ShouldUpdateDiagnosticsUINow():
      self.RefreshDiagnosticsUI( open_on_edit )


  def RefreshDiagnosticsUI( self, open_on_edit = False ):
    if self._user_options[ 'echo_current_diagnostic' ]:
      self._EchoDiagnostic()

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._UpdateSigns()

    self.UpdateMatches()

    if self._user_options[ 'always_populate_location_list' ]:
      self._UpdateLocationLists( open_on_edit )


  def ClearDiagnosticsUI( self ):
    if self._user_options[ 'echo_current_diagnostic' ]:
      self._ClearCurrentDiagnostic()

    if self._user_options[ 'enable_diagnostic_signs' ]:
      self._ClearSigns()

    self._ClearMatches()


  def DiagnosticsForLine( self, line_number ):
    return self._line_to_diags[ line_number ]


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
    text = None
    first_diag = None
    if diags:
      first_diag = diags[ 0 ]
      text = first_diag[ 'text' ]
      if first_diag.get( 'fixit_available', False ):
        text += ' (FixIt)'

    self._EchoDiagnosticText( line_num, first_diag, text )


  def _ClearCurrentDiagnostic( self, will_be_replaced=False ):
    if not self._diag_message_needs_clearing:
      return

    if ( vimsupport.VimSupportsVirtualText() and
         self._user_options[ 'echo_current_diagnostic' ] == 'virtual-text' ):
      tp.ClearTextProperties( self._bufnr,
                              prop_types = [ 'YcmVirtDiagPadding',
                                             'YcmVirtDiagError',
                                             'YcmVirtDiagWarning' ] )
    else:
      if not will_be_replaced:
        vimsupport.PostVimMessage( '', warning = False )

    self._diag_message_needs_clearing = False


  def _EchoDiagnosticText( self, line_num, first_diag, text ):
    self._ClearCurrentDiagnostic( bool( text ) )

    if ( vimsupport.VimSupportsVirtualText() and
         self._user_options[ 'echo_current_diagnostic' ] == 'virtual-text' ):
      if not text:
        return

      def MakeVritualTextProperty( prop_type, text, position='after' ):
        vimsupport.AddTextProperty( self._bufnr,
                                    line_num,
                                    0,
                                    prop_type,
                                    {
                                      'text': text,
                                      'text_align': position,
                                      'text_wrap': 'wrap'
                                    } )

      if vim.options[ 'ambiwidth' ] != 'double':
        marker = '⚠'
      else:
        marker = '>'

      MakeVritualTextProperty(
        'YcmVirtDiagPadding',
        ' ' * vim.buffers[ self._bufnr ].options[ 'shiftwidth' ] ),
      MakeVritualTextProperty(
        'YcmVirtDiagError' if _DiagnosticIsError( first_diag )
                       else 'YcmVirtDiagWarning',
        marker + ' ' + [ line for line in text.splitlines() if line ][ 0 ] )
    else:
      if not text:
        # We already cleared it
        return

      vimsupport.PostVimMessage( text, warning = False, truncate = True )

    self._diag_message_needs_clearing = True


  def _DiagnosticsCount( self, predicate ):
    count = 0
    for diags in self._line_to_diags.values():
      count += sum( 1 for d in diags if predicate( d ) )
    return count


  def _UpdateLocationLists( self, open_on_edit = False ):
    vimsupport.SetLocationListsForBuffer(
      self._bufnr,
      vimsupport.ConvertDiagnosticsToQfList( self._diagnostics ),
      open_on_edit )


  def _ClearMatches( self ):
    props_to_remove = vimsupport.GetTextProperties( self._bufnr )
    for prop in props_to_remove:
      vimsupport.RemoveDiagnosticProperty( self._bufnr, prop )


  def UpdateMatches( self ):
    if not self._user_options[ 'enable_diagnostic_highlighting' ]:
      return

    props_to_remove = vimsupport.GetTextProperties( self._bufnr )
    for diags in self._line_to_diags.values():
      # Insert squiggles in reverse order so that errors overlap warnings.
      for diag in reversed( diags ):
        for line, column, name, extras in _ConvertDiagnosticToTextProperties(
            self._bufnr,
            diag ):
          global YCM_VIM_PROPERTY_ID

          # Note the following .remove() works because the __eq__ on
          # DiagnosticProperty does not actually check the IDs match...
          diag_prop = vimsupport.DiagnosticProperty(
              YCM_VIM_PROPERTY_ID,
              name,
              line,
              column,
              extras[ 'end_col' ] - column if 'end_col' in extras else column )
          try:
            props_to_remove.remove( diag_prop )
          except ValueError:
            extras.update( {
              'id': YCM_VIM_PROPERTY_ID
            } )
            vimsupport.AddTextProperty( self._bufnr,
                                        line,
                                        column,
                                        name,
                                        extras )
          YCM_VIM_PROPERTY_ID += 1
    for prop in props_to_remove:
      vimsupport.RemoveDiagnosticProperty( self._bufnr, prop )


  def _ClearSigns( self ):
    signs_to_unplace = vimsupport.GetSignsInBuffer( self._bufnr )
    vim.eval( f'sign_unplacelist( { signs_to_unplace } )' )


  def _UpdateSigns( self ):
    signs_to_unplace = vimsupport.GetSignsInBuffer( self._bufnr )
    signs_to_place = []
    for line, diags in self._line_to_diags.items():
      if not diags:
        continue

      # We always go for the first diagnostic on the line because diagnostics
      # are sorted by errors in priority and Vim can only display one sign by
      # line.
      name = 'YcmError' if _DiagnosticIsError( diags[ 0 ] ) else 'YcmWarning'
      sign = {
          'lnum': line,
          'name': name,
          'buffer': self._bufnr,
          'group': 'ycm_signs'
      }
      try:
        signs_to_unplace.remove( sign )
      except ValueError:
        signs_to_place.append( sign )
    vim.eval( f'sign_placelist( { signs_to_place } )' )
    vim.eval( f'sign_unplacelist( { signs_to_unplace } )' )


  def _ConvertDiagListToDict( self ):
    self._line_to_diags = defaultdict( list )
    for diag in self._diagnostics:
      location = diag[ 'location' ]
      bufnr = vimsupport.GetBufferNumberForFilename( location[ 'filepath' ] )
      if bufnr == self._bufnr:
        line_number = location[ 'line_num' ]
        self._line_to_diags[ line_number ].append( diag )

    for diags in self._line_to_diags.values():
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


def _ConvertDiagnosticToTextProperties( bufnr, diagnostic ):
  properties = []

  name = ( 'YcmErrorProperty' if _DiagnosticIsError( diagnostic ) else
            'YcmWarningProperty' )
  if vimsupport.VimIsNeovim():
    name = name.replace( 'Property', 'Section' )

  location_extent = diagnostic[ 'location_extent' ]
  if location_extent[ 'start' ][ 'line_num' ] <= 0:
    location = diagnostic[ 'location' ]
    line, column = vimsupport.LineAndColumnNumbersClamped(
      bufnr,
      location[ 'line_num' ],
      location[ 'column_num' ]
    )
    properties.append( ( line, column, name, {} ) )
  else:
    start_line, start_column = vimsupport.LineAndColumnNumbersClamped(
      bufnr,
      location_extent[ 'start' ][ 'line_num' ],
      location_extent[ 'start' ][ 'column_num' ]
    )
    end_line, end_column = vimsupport.LineAndColumnNumbersClamped(
      bufnr,
      location_extent[ 'end' ][ 'line_num' ],
      location_extent[ 'end' ][ 'column_num' ]
    )
    properties.append( (
      start_line,
      start_column,
      name,
      { 'end_lnum': end_line,
        'end_col': end_column } ) )

  for diagnostic_range in diagnostic[ 'ranges' ]:
    if ( diagnostic_range[ 'start' ][ 'line_num' ] == 0 or
         diagnostic_range[ 'end' ][ 'line_num' ] == 0 ):
      continue
    start_line, start_column = vimsupport.LineAndColumnNumbersClamped(
      bufnr,
      diagnostic_range[ 'start' ][ 'line_num' ],
      diagnostic_range[ 'start' ][ 'column_num' ]
    )
    end_line, end_column = vimsupport.LineAndColumnNumbersClamped(
      bufnr,
      diagnostic_range[ 'end' ][ 'line_num' ],
      diagnostic_range[ 'end' ][ 'column_num' ]
    )

    if not _IsValidRange( start_line, start_column, end_line, end_column ):
      continue

    properties.append( (
      start_line,
      start_column,
      name,
      { 'end_lnum': end_line,
        'end_col': end_column } ) )

  return properties


def _IsValidRange( start_line, start_column, end_line, end_column ):
  # End line before start line - invalid
  if start_line > end_line:
    return False

  # End line after start line - valid
  if start_line < end_line:
    return True

  # Same line, start colum after end column - invalid
  if start_column > end_column:
    return False

  # Same line, start column before or equal to end column - valid
  return True

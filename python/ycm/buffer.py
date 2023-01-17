# Copyright (C) 2016, Davit Samvelyan
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

from ycm import vimsupport
from ycm.client.event_notification import EventNotification
from ycm.diagnostic_interface import DiagnosticInterface
from ycm.semantic_highlighting import SemanticHighlighting
from ycm.inlay_hints import InlayHints


# Emulates Vim buffer
# Used to store buffer related information like diagnostics, latest parse
# request. Stores buffer change tick at the parse request moment, allowing
# to effectively determine whether reparse is needed for the buffer.
class Buffer:

  def __init__( self, bufnr, user_options, filetypes ):
    self._number = bufnr
    self._parse_tick = 0
    self._handled_tick = 0
    self._parse_request = None
    self._should_resend = False
    self._diag_interface = DiagnosticInterface( bufnr, user_options )
    self._open_loclist_on_ycm_diags = user_options[
                                        'open_loclist_on_ycm_diags' ]
    self._semantic_highlighting = SemanticHighlighting( bufnr, user_options )
    self.inlay_hints = InlayHints( bufnr, user_options )
    self.UpdateFromFileTypes( filetypes )


  def FileParseRequestReady( self, block = False ):
    return ( bool( self._parse_request ) and
             ( block or self._parse_request.Done() ) )


  def SendParseRequest( self, extra_data ):
    # Don't send a parse request if one is in progress
    if self._parse_request is not None and not self._parse_request.Done():
      self._should_resend = True
      return

    self._should_resend = False

    self._parse_request = EventNotification( 'FileReadyToParse',
                                             extra_data = extra_data )
    self._parse_request.Start()
    # Decrement handled tick to ensure correct handling when we are forcing
    # reparse on buffer visit and changed tick remains the same.
    self._handled_tick -= 1
    self._parse_tick = self._ChangedTick()


  def ParseRequestPending( self ):
    return bool( self._parse_request ) and not self._parse_request.Done()


  def NeedsReparse( self ):
    return self._parse_tick != self._ChangedTick()


  def ShouldResendParseRequest( self ):
    return ( self._should_resend
             or ( bool( self._parse_request )
                  and self._parse_request.ShouldResend() ) )


  def UpdateDiagnostics( self, force = False ):
    if force or not self._async_diags:
      self.UpdateWithNewDiagnostics( self._parse_request.Response(), False )
    else:
      # We need to call the response method, because it might throw an exception
      # or require extra config confirmation, even if we don't actually use the
      # diagnostics.
      self._parse_request.Response()


  def UpdateWithNewDiagnostics( self, diagnostics, async_message ):
    self._async_diags = async_message
    self._diag_interface.UpdateWithNewDiagnostics(
        diagnostics,
        not self._async_diags and self._open_loclist_on_ycm_diags )


  def UpdateMatches( self ):
    self._diag_interface.UpdateMatches()


  def PopulateLocationList( self, open_on_edit = False ):
    return self._diag_interface.PopulateLocationList( open_on_edit )


  def GetResponse( self ):
    return self._parse_request.Response()


  def IsResponseHandled( self ):
    return self._handled_tick == self._parse_tick


  def MarkResponseHandled( self ):
    self._handled_tick = self._parse_tick


  def OnCursorMoved( self ):
    self._diag_interface.OnCursorMoved()


  def GetErrorCount( self ):
    return self._diag_interface.GetErrorCount()


  def GetWarningCount( self ):
    return self._diag_interface.GetWarningCount()


  def RefreshDiagnosticsUI( self ):
    return self._diag_interface.RefreshDiagnosticsUI()


  def ClearDiagnosticsUI( self ):
    return self._diag_interface.ClearDiagnosticsUI()


  def DiagnosticsForLine( self, line_number ):
    return self._diag_interface.DiagnosticsForLine( line_number )


  def UpdateFromFileTypes( self, filetypes ):
    self._filetypes = filetypes
    # We will set this to true if we ever receive any diagnostics asyncronously.
    self._async_diags = False


  def SendSemanticTokensRequest( self ):
    self._semantic_highlighting.SendRequest()


  def SemanticTokensRequestReady( self ):
    return self._semantic_highlighting.IsResponseReady()


  def UpdateSemanticTokens( self ):
    return self._semantic_highlighting.Update()


  def _ChangedTick( self ):
    return vimsupport.GetBufferChangedTick( self._number )


class BufferDict( dict ):

  def __init__( self, user_options ):
    self._user_options = user_options


  def __missing__( self, key ):
    # Python does not allow to return assignment operation result directly
    new_value = self[ key ] = Buffer(
      key,
      self._user_options,
      vimsupport.GetBufferFiletypes( key ) )

    return new_value

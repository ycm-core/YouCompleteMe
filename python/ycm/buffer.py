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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm import vimsupport
from ycm.client.event_notification import EventNotification
from ycm.diagnostic_interface import DiagnosticInterface


class Buffer( object ):

  def __init__( self, bufnr, user_options ):
    self.number = bufnr
    self._parse_tick = 0
    self._handled_tick = 0
    self._parse_request = None
    self._diag_interface = DiagnosticInterface( user_options )


  def FileParseRequestReady( self, block = False ):
    return self._parse_tick == 0 or block or self._parse_request.Done()


  def SendParseRequest( self, extra_data ):
    self._parse_request = EventNotification( 'FileReadyToParse',
                                             extra_data = extra_data )
    self._parse_request.Start()
    self._parse_tick = self._ChangedTick()


  def NeedsReparse( self ):
    return self._parse_tick != self._ChangedTick()


  def UpdateDiagnostics( self ):
    diagnostics = self._parse_request.Response()
    self._diag_interface.UpdateWithNewDiagnostics( diagnostics )


  def PopulateLocationList( self ):
    return self._diag_interface.PopulateLocationList()


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


  def _ChangedTick( self ):
    return vimsupport.GetBufferChangedTick( self.number )


class BufferDict( dict ):

  def __init__( self, user_options ):
    self._user_options = user_options


  def __missing__( self, key ):
    value = self[ key ] = Buffer( key, self._user_options )
    return value

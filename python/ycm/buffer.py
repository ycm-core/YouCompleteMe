# Copyright (C) 2017, Davit Samvelyan
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
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycm import vimsupport
from ycm.client.event_notification import EventNotification


class Buffer( object ):

  def __init__( self, buffer_number ):
    self.number = buffer_number
    self._last_request_tick = 0
    self._parsed_tick = 0
    self._handled_tick = 0
    self._parse_requests = []
    self._diagnostics = []


  def SendParseRequest( self, extra_data ):
    buffer_changedtick = self._ChangedTick()
    request = EventNotification( 'FileReadyToParse',
                                 extra_data = extra_data,
                                 changedtick = buffer_changedtick )
    self._parse_requests.append( request )
    self._last_request_tick = buffer_changedtick
    request.Start()


  def NeedsReparse( self ):
    buffer_changedtick = self._ChangedTick()
    if self._parse_requests:
      return self._last_request_tick != buffer_changedtick
    return self._parsed_tick != buffer_changedtick


  def Diagnostics( self ):
    return self._diagnostics


  def ProcessParseRequests( self, block = False ):
    if not self._parse_requests:
      return

    successful = None
    remaining = []
    for request in self._parse_requests:
      if block or request.Done():
        # Call Response to check request for any exception or UnknownExtraConf
        # response, to allow the server to raise configuration warnings, etc.
        # to the user. We ignore any other supplied data.
        request.Response()
        if not request.ParseRequestIncomplete():
          successful = request
          # Ignore not finished requests prior to last successful one.
          remaining = []
      else:
        remaining.append( request )

    if successful:
      self._parsed_tick = successful.ChangedTick()
      self._diagnostics = successful.Response()

    self._parse_requests = remaining


  def IsResponseHandled( self ):
    return self._handled_tick == self._parsed_tick


  def MarkResponseHandled( self ):
    self._handled_tick = self._parsed_tick


  def _ChangedTick( self ):
    return vimsupport.GetBufferChangedTick( self.number )


class BufferDict( dict ):

  def __missing__( self, key ):
    value = self[ key ] = Buffer( key )
    return value

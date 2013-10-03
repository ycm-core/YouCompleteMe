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

from ycm import vimsupport
from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                     JsonFromFuture )

class EventNotification( BaseRequest ):
  def __init__( self, event_name, extra_data = None ):
    super( EventNotification, self ).__init__()
    self._event_name = event_name
    self._extra_data = extra_data
    self._cached_response = None


  def Start( self ):
    request_data = BuildRequestData()
    if self._extra_data:
      request_data.update( self._extra_data )
    request_data[ 'event_name' ] = self._event_name

    self._response_future = self.PostDataToHandlerAsync( request_data,
                                                         'event_notification' )


  def Done( self ):
    return self._response_future.done()


  def Response( self ):
    if self._cached_response:
      return self._cached_response

    if not self._response_future or self._event_name != 'FileReadyToParse':
      return []

    try:
      self._cached_response = [ _ConvertDiagnosticDataToVimData( x )
                                for x in JsonFromFuture(
                                    self._response_future ) ]
      return self._cached_response
    except Exception as e:
      vimsupport.PostVimMessage( str( e ) )
      return []


def _ConvertDiagnosticDataToVimData( diagnostic ):
  # see :h getqflist for a description of the dictionary fields
  # Note that, as usual, Vim is completely inconsistent about whether
  # line/column numbers are 1 or 0 based in its various APIs. Here, it wants
  # them to be 1-based.
  return {
    'bufnr' : vimsupport.GetBufferNumberForFilename( diagnostic[ 'filepath' ]),
    'lnum'  : diagnostic[ 'line_num' ] + 1,
    'col'   : diagnostic[ 'column_num' ] + 1,
    'text'  : diagnostic[ 'text' ],
    'type'  : diagnostic[ 'kind' ],
    'valid' : 1
  }


def SendEventNotificationAsync( event_name, extra_data = None ):
  event = EventNotification( event_name, extra_data )
  event.Start()


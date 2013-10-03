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

from ycm.client.base_request import BaseRequest, BuildRequestData


class EventNotification( BaseRequest ):
  def __init__( self, event_name, extra_data = None ):
    super( EventNotification, self ).__init__()
    self._event_name = event_name
    self._extra_data = extra_data


  def Start( self ):
    request_data = BuildRequestData()
    if self._extra_data:
      request_data.update( self._extra_data )
    request_data[ 'event_name' ] = self._event_name

    self.PostDataToHandlerAsync( request_data, 'event_notification' )


def SendEventNotificationAsync( event_name, extra_data = None ):
  event = EventNotification( event_name, extra_data )
  event.Start()


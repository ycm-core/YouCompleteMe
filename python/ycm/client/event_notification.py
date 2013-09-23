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

import traceback
from ycm import vimsupport
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

    # On occasion, Vim tries to send event notifications to the server before
    # it's up. This causes intrusive exception messages to interrupt the user.
    # While we do want to log these exceptions just in case, we post them
    # quietly to the Vim message log because nothing bad will happen if the
    # server misses some events and we don't want to annoy the user.
    try:
      self.PostDataToHandler( request_data, 'event_notification' )
    except:
      vimsupport.EchoText( traceback.format_exc() )


def SendEventNotificationAsync( event_name, extra_data = None ):
  event = EventNotification( event_name, extra_data )
  event.Start()


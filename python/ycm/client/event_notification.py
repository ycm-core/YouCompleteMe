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

from ycm.client.base_request import BaseRequest, BuildRequestData


class EventNotification( BaseRequest ):
  def __init__( self, event_name, buffer_number = None, extra_data = None ):
    super( EventNotification, self ).__init__()
    self._event_name = event_name
    self._buffer_number = buffer_number
    self._extra_data = extra_data
    self._response_future = None
    self._cached_response = None


  def Start( self ):
    request_data = BuildRequestData( self._buffer_number )
    if self._extra_data:
      request_data.update( self._extra_data )
    request_data[ 'event_name' ] = self._event_name

    self._response_future = self.PostDataToHandlerAsync( request_data,
                                                         'event_notification' )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Response( self ):
    if self._cached_response:
      return self._cached_response

    if not self._response_future or self._event_name != 'FileReadyToParse':
      return []

    self._cached_response = self.HandleFuture( self._response_future,
                                               truncate_message = True )

    return self._cached_response if self._cached_response else []


def SendEventNotificationAsync( event_name,
                                buffer_number = None,
                                extra_data = None ):
  event = EventNotification( event_name, buffer_number, extra_data )
  event.Start()

#!/usr/bin/env python
#
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

from ycm import vimsupport
from ycmd.responses import UnknownExtraConf
from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                     JsonFromFuture )


asked = False


class EventNotification( BaseRequest ):
  def __init__( self, event_name, request_data, extra_data = None ):
    super( EventNotification, self ).__init__()
    self.request_data = request_data
    self._event_name = event_name
    self._extra_data = extra_data
    self._cached_response = None


  def Start( self ):
    request_data = dict( self.request_data )
    if self._extra_data:
      request_data.update( self._extra_data )
    request_data[ 'event_name' ] = self._event_name

    self._response_future = self.PostDataToHandlerAsync( request_data,
                                                         'event_notification',
                                                         request = self )


  def Done( self ):
    return self._response_future.done()


  def Response( self ):
    global asked

    if self._cached_response:
      return self._cached_response

    if not self._response_future or self._event_name != 'FileReadyToParse':
      return []

    try:
      try:
        self._cached_response = JsonFromFuture( self._response_future )
      except UnknownExtraConf as e:
        if not asked:
          asked = True
          if vimsupport.Confirm( str( e ) ):
            _LoadExtraConfFile( e.extra_conf_file )
          else:
            _IgnoreExtraConfFile( e.extra_conf_file )
    except Exception as e:
      vimsupport.PostVimMessage( str( e ) )

    return self._cached_response if self._cached_response else []


def SendEventNotificationAsync( event_name, request_data, extra_data = None ):
  event = EventNotification( event_name, request_data, extra_data )
  event.Start()

def _LoadExtraConfFile( filepath ):
  BaseRequest.PostDataToHandler( { 'filepath': filepath },
                                 'load_extra_conf_file' )

def _IgnoreExtraConfFile( filepath ):
  BaseRequest.PostDataToHandler( { 'filepath': filepath },
                                 'ignore_extra_conf_file' )

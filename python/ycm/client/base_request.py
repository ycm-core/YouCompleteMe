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

import vim
import json
import requests
import urlparse
from retries import retries
from requests_futures.sessions import FuturesSession
from ycm.unsafe_thread_pool_executor import UnsafeThreadPoolExecutor
from ycm import vimsupport
from ycm.server.responses import ServerError, UnknownExtraConf

HEADERS = {'content-type': 'application/json'}
EXECUTOR = UnsafeThreadPoolExecutor( max_workers = 30 )
# Setting this to None seems to screw up the Requests/urllib3 libs.
DEFAULT_TIMEOUT_SEC = 30

class BaseRequest( object ):
  def __init__( self ):
    pass


  def Start( self ):
    pass


  def Done( self ):
    return True


  def Response( self ):
    return {}

  # This method blocks
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def GetDataFromHandler( handler, timeout = DEFAULT_TIMEOUT_SEC ):
    return JsonFromFuture( BaseRequest._TalkToHandlerAsync( '',
                                                            handler,
                                                            'GET',
                                                            timeout ) )


  # This is the blocking version of the method. See below for async.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def PostDataToHandler( data, handler, timeout = DEFAULT_TIMEOUT_SEC ):
    return JsonFromFuture( BaseRequest.PostDataToHandlerAsync( data,
                                                               handler,
                                                               timeout ) )


  # This returns a future! Use JsonFromFuture to get the value.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def PostDataToHandlerAsync( data, handler, timeout = DEFAULT_TIMEOUT_SEC ):
    return BaseRequest._TalkToHandlerAsync( data, handler, 'POST', timeout )


  # This returns a future! Use JsonFromFuture to get the value.
  # |method| is either 'POST' or 'GET'.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def _TalkToHandlerAsync( data,
                           handler,
                           method,
                           timeout = DEFAULT_TIMEOUT_SEC ):
    def SendRequest( data, handler, method, timeout ):
      if method == 'POST':
        return BaseRequest.session.post( _BuildUri( handler ),
                                        data = json.dumps( data ),
                                        headers = HEADERS,
                                        timeout = timeout )
      if method == 'GET':
        return BaseRequest.session.get( _BuildUri( handler ),
                                        headers = HEADERS,
                                        timeout = timeout )

    @retries( 5, delay = 0.5, backoff = 1.5 )
    def DelayedSendRequest( data, handler, method ):
      if method == 'POST':
        return requests.post( _BuildUri( handler ),
                              data = json.dumps( data ),
                              headers = HEADERS )
      if method == 'GET':
        return requests.get( _BuildUri( handler ),
                             headers = HEADERS )

    if not _CheckServerIsHealthyWithCache():
      return EXECUTOR.submit( DelayedSendRequest, data, handler, method )

    return SendRequest( data, handler, method, timeout )


  session = FuturesSession( executor = EXECUTOR )
  server_location = 'http://localhost:6666'


def BuildRequestData( start_column = None,
                      query = None,
                      include_buffer_data = True ):
  line, column = vimsupport.CurrentLineAndColumn()
  filepath = vimsupport.GetCurrentBufferFilepath()
  request_data = {
    'filetypes': vimsupport.CurrentFiletypes(),
    'line_num': line,
    'column_num': column,
    'start_column': start_column,
    'line_value': vim.current.line,
    'filepath': filepath
  }

  if include_buffer_data:
    request_data[ 'file_data' ] = vimsupport.GetUnsavedAndCurrentBufferData()
  if query:
    request_data[ 'query' ] = query

  return request_data


def JsonFromFuture( future ):
  response = future.result()
  if response.status_code == requests.codes.server_error:
    _RaiseExceptionForData( response.json() )

  # We let Requests handle the other status types, we only handle the 500
  # error code.
  response.raise_for_status()

  if response.text:
    return response.json()
  return None


def _BuildUri( handler ):
  return urlparse.urljoin( BaseRequest.server_location, handler )


SERVER_HEALTHY = False

def _CheckServerIsHealthyWithCache():
  global SERVER_HEALTHY

  def _ServerIsHealthy():
    response = requests.get( _BuildUri( 'healthy' ) )
    response.raise_for_status()
    return response.json()

  if SERVER_HEALTHY:
    return True

  try:
    SERVER_HEALTHY = _ServerIsHealthy()
    return SERVER_HEALTHY
  except:
    return False


def _RaiseExceptionForData( data ):
  if data[ 'exception' ][ 'TYPE' ] == UnknownExtraConf.__name__:
    raise UnknownExtraConf( data[ 'exception' ][ 'extra_conf_file' ] )

  raise ServerError( '{0}: {1}'.format( data[ 'exception' ][ 'TYPE' ],
                                        data[ 'message' ] ) )

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

import vim
import json
import requests
import urlparse
from retries import retries
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
from ycm import vimsupport
from ycm.server.responses import ServerError, UnknownExtraConf

HEADERS = {'content-type': 'application/json'}
EXECUTOR = ThreadPoolExecutor( max_workers = 10 )

class BaseRequest( object ):
  def __init__( self ):
    pass


  def Start( self ):
    pass


  def Done( self ):
    return True


  def Response( self ):
    return {}


  # This is the blocking version of the method. See below for async.
  @staticmethod
  def PostDataToHandler( data, handler ):
    return JsonFromFuture( BaseRequest.PostDataToHandlerAsync( data,
                                                               handler ) )


  # This returns a future! Use JsonFromFuture to get the value.
  @staticmethod
  def PostDataToHandlerAsync( data, handler ):
    def PostData( data, handler ):
      return BaseRequest.session.post( _BuildUri( handler ),
                                      data = json.dumps( data ),
                                      headers = HEADERS )

    @retries( 3, delay = 0.5 )
    def DelayedPostData( data, handler ):
      return requests.post( _BuildUri( handler ),
                            data = json.dumps( data ),
                            headers = HEADERS )

    if not _CheckServerIsHealthyWithCache():
      return EXECUTOR.submit( DelayedPostData, data, handler )

    return PostData( data, handler )


  session = FuturesSession( executor = EXECUTOR )
  server_location = 'http://localhost:6666'


def BuildRequestData( start_column = None, query = None ):
  line, column = vimsupport.CurrentLineAndColumn()
  filepath = vimsupport.GetCurrentBufferFilepath()
  request_data = {
    'filetypes': vimsupport.CurrentFiletypes(),
    'line_num': line,
    'column_num': column,
    'start_column': start_column,
    'line_value': vim.current.line,
    'filepath': filepath,
    'file_data': vimsupport.GetUnsavedAndCurrentBufferData()
  }

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

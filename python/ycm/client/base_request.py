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

import requests
import urlparse
from base64 import b64decode, b64encode
from retries import retries
from requests_futures.sessions import FuturesSession
from ycm.unsafe_thread_pool_executor import UnsafeThreadPoolExecutor
from ycm import vimsupport
from ycmd.utils import ToUtf8Json
from ycmd.hmac_utils import CreateRequestHmac, CreateHmac, SecureStringsEqual
from ycmd.responses import ServerError, UnknownExtraConf

_HEADERS = {'content-type': 'application/json'}
_EXECUTOR = UnsafeThreadPoolExecutor( max_workers = 30 )
# Setting this to None seems to screw up the Requests/urllib3 libs.
_DEFAULT_TIMEOUT_SEC = 30
_HMAC_HEADER = 'x-ycm-hmac'

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
  def GetDataFromHandler( handler, timeout = _DEFAULT_TIMEOUT_SEC ):
    return JsonFromFuture( BaseRequest._TalkToHandlerAsync( '',
                                                            handler,
                                                            'GET',
                                                            timeout ) )


  # This is the blocking version of the method. See below for async.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def PostDataToHandler( data, handler, timeout = _DEFAULT_TIMEOUT_SEC ):
    return JsonFromFuture( BaseRequest.PostDataToHandlerAsync( data,
                                                               handler,
                                                               timeout ) )


  # This returns a future! Use JsonFromFuture to get the value.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def PostDataToHandlerAsync( data, handler, timeout = _DEFAULT_TIMEOUT_SEC ):
    return BaseRequest._TalkToHandlerAsync( data, handler, 'POST', timeout )


  # This returns a future! Use JsonFromFuture to get the value.
  # |method| is either 'POST' or 'GET'.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def _TalkToHandlerAsync( data,
                           handler,
                           method,
                           timeout = _DEFAULT_TIMEOUT_SEC ):
    def SendRequest( data, handler, method, timeout ):
      request_uri = _BuildUri( handler )
      if method == 'POST':
        sent_data = ToUtf8Json( data )
        return BaseRequest.session.post(
            request_uri,
            data = sent_data,
            headers = BaseRequest._ExtraHeaders( method,
                                                 request_uri,
                                                 sent_data ),
            timeout = timeout )
      if method == 'GET':
        return BaseRequest.session.get(
            request_uri,
            headers = BaseRequest._ExtraHeaders( method, request_uri ),
            timeout = timeout )

    @retries( 5, delay = 0.5, backoff = 1.5 )
    def DelayedSendRequest( data, handler, method ):
      request_uri = _BuildUri( handler )
      if method == 'POST':
        sent_data = ToUtf8Json( data )
        return requests.post(
            request_uri,
            data = sent_data,
            headers = BaseRequest._ExtraHeaders( method,
                                                 request_uri,
                                                 sent_data ) )
      if method == 'GET':
        return requests.get(
            request_uri,
            headers = BaseRequest._ExtraHeaders( method, request_uri ) )

    if not _CheckServerIsHealthyWithCache():
      return _EXECUTOR.submit( DelayedSendRequest, data, handler, method )

    return SendRequest( data, handler, method, timeout )


  @staticmethod
  def _ExtraHeaders( method, request_uri, request_body = None ):
    if not request_body:
      request_body = ''
    headers = dict( _HEADERS )
    headers[ _HMAC_HEADER ] = b64encode(
        CreateRequestHmac( method,
                           urlparse.urlparse( request_uri ).path,
                           request_body,
                           BaseRequest.hmac_secret ) )
    return headers

  session = FuturesSession( executor = _EXECUTOR )
  server_location = ''
  hmac_secret = ''


def BuildRequestData( include_buffer_data = True ):
  line, column = vimsupport.CurrentLineAndColumn()
  filepath = vimsupport.GetCurrentBufferFilepath()
  request_data = {
    'line_num': line + 1,
    'column_num': column + 1,
    'filepath': filepath
  }

  if include_buffer_data:
    request_data[ 'file_data' ] = vimsupport.GetUnsavedAndCurrentBufferData()

  return request_data


def JsonFromFuture( future ):
  response = future.result()
  _ValidateResponseObject( response )
  if response.status_code == requests.codes.server_error:
    raise MakeServerException( response.json() )

  # We let Requests handle the other status types, we only handle the 500
  # error code.
  response.raise_for_status()

  if response.text:
    return response.json()
  return None


def HandleServerException( exception ):
  serialized_exception = str( exception )

  # We ignore the exception about the file already being parsed since it comes
  # up often and isn't something that's actionable by the user.
  if 'already being parsed' in serialized_exception:
    return
  vimsupport.PostVimMessage( serialized_exception )


def _ValidateResponseObject( response ):
  hmac = CreateHmac( response.content, BaseRequest.hmac_secret )
  if not SecureStringsEqual( hmac,
                             b64decode( response.headers[ _HMAC_HEADER ] ) ):
    raise RuntimeError( 'Received invalid HMAC for response!' )
  return True

def _BuildUri( handler ):
  return urlparse.urljoin( BaseRequest.server_location, handler )


SERVER_HEALTHY = False

def _CheckServerIsHealthyWithCache():
  global SERVER_HEALTHY

  def _ServerIsHealthy():
    request_uri = _BuildUri( 'healthy' )
    response = requests.get( request_uri,
                             headers = BaseRequest._ExtraHeaders(
                                 'GET', request_uri, '' ) )
    _ValidateResponseObject( response )
    response.raise_for_status()
    return response.json()

  if SERVER_HEALTHY:
    return True

  try:
    SERVER_HEALTHY = _ServerIsHealthy()
    return SERVER_HEALTHY
  except:
    return False

def MakeServerException( data ):
  if data[ 'exception' ][ 'TYPE' ] == UnknownExtraConf.__name__:
    return UnknownExtraConf( data[ 'exception' ][ 'extra_conf_file' ] )

  return ServerError( '{0}: {1}'.format( data[ 'exception' ][ 'TYPE' ],
                                         data[ 'message' ] ) )

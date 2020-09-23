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

import logging
import json
import vim
from base64 import b64decode, b64encode
from hmac import compare_digest
from urllib.parse import urljoin, urlparse
from ycm import vimsupport
from ycmd.utils import ToBytes, GetCurrentDirectory
from ycmd.hmac_utils import CreateRequestHmac, CreateHmac
from ycmd.responses import ServerError, UnknownExtraConf

_HEADERS = { 'content-type': 'application/json' }
_CONNECT_TIMEOUT_SEC = 0.01
# Setting this to None seems to screw up the Requests/urllib3 libs.
_READ_TIMEOUT_SEC = 30
_HMAC_HEADER = 'x-ycm-hmac'
_logger = logging.getLogger( __name__ )


class BaseRequest:
  _buffer_update_types = None
  def __init__( self ):
    self._should_resend = False


  def Start( self ):
    pass


  def Done( self ):
    return True


  def Response( self ):
    return {}


  def ShouldResend( self ):
    return self._should_resend


  def HandleFuture( self,
                    future,
                    display_message = True,
                    truncate_message = False ):
    """Get the server response from a |future| object and catch any exception
    while doing so. If an exception is raised because of a unknown
    .ycm_extra_conf.py file, load the file or ignore it after asking the user.
    An identical request should be sent again to the server. For other
    exceptions, log the exception and display its message to the user on the Vim
    status line. Unset the |display_message| parameter to hide the message from
    the user. Set the |truncate_message| parameter to avoid hit-enter prompts
    from this message."""
    try:
      try:
        return _JsonFromFuture( future )
      except UnknownExtraConf as e:
        if vimsupport.Confirm( str( e ) ):
          _LoadExtraConfFile( e.extra_conf_file )
        else:
          _IgnoreExtraConfFile( e.extra_conf_file )
        self._should_resend = True
    except BaseRequest.Requests().exceptions.ConnectionError as e:
      # We don't display this exception to the user since it is likely to happen
      # for each subsequent request (typically if the server crashed) and we
      # don't want to spam the user with it.
      _logger.error( e )
    except Exception as e:
      _logger.exception( 'Error while handling server response' )
      if display_message:
        DisplayServerException( e, truncate_message )

    return None


  @staticmethod
  def _IncrementalBufferUpdatesSupported( buffer_number ):
    from ycm.client.buffer_update_type_request import BufferUpdateTypeByFileType
    if BaseRequest._buffer_update_types is None:
      BaseRequest._buffer_update_types = BufferUpdateTypeByFileType()
    if buffer_number:
      filetypes = vimsupport.GetBufferFiletypes( buffer_number )
    else:
      filetypes = vimsupport.CurrentFiletypes()

    # TODO: Figure out what to do with mixed filetypes.
    # for filetype in filetypes:
    #   if not BaseRequest._buffer_update_types[ filetype ].Done():
    #     continue

    #   buffer_update_type = BaseRequest._buffer_update_types[ filetype ].Response()
    #   if buffer_update_type == 'Full':
    #     continue

    #   if buffer_update_type == 'PENDING':
    #     BaseRequest._buffer_update_types[ filetype ].Start( filetype )
    #     continue

    #   return True
    request = BaseRequest._buffer_update_types[ filetypes[ 0 ] ]
    if not request.Done():
      return False
    response = request.Response()
    if response == 'Full':
      return False
    if response == 'PENDING':
      BaseRequest._buffer_update_types[ filetypes[ 0 ] ].Start( filetypes[ 0 ] )
      return False
    return True


  # This method blocks
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  # See the HandleFuture method for the |display_message| and |truncate_message|
  # parameters.
  def GetDataFromHandler( self,
                          handler,
                          timeout = _READ_TIMEOUT_SEC,
                          display_message = True,
                          truncate_message = False,
                          payload = None ):
    return self.HandleFuture(
        self.GetDataFromHandlerAsync( handler, timeout, payload ),
        display_message,
        truncate_message )


  def GetDataFromHandlerAsync( self,
                               handler,
                               timeout = _READ_TIMEOUT_SEC,
                               payload = None ):
    return BaseRequest._TalkToHandlerAsync(
        '', handler, 'GET', timeout, payload )


  # This is the blocking version of the method. See below for async.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  # See the HandleFuture method for the |display_message| and |truncate_message|
  # parameters.
  def PostDataToHandler( self,
                         data,
                         handler,
                         timeout = _READ_TIMEOUT_SEC,
                         display_message = True,
                         truncate_message = False ):
    return self.HandleFuture(
        BaseRequest.PostDataToHandlerAsync( data, handler, timeout ),
        display_message,
        truncate_message )


  # This returns a future! Use HandleFuture to get the value.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def PostDataToHandlerAsync( data, handler, timeout = _READ_TIMEOUT_SEC ):
    return BaseRequest._TalkToHandlerAsync( data, handler, 'POST', timeout )


  # This returns a future! Use HandleFuture to get the value.
  # |method| is either 'POST' or 'GET'.
  # |timeout| is num seconds to tolerate no response from server before giving
  # up; see Requests docs for details (we just pass the param along).
  @staticmethod
  def _TalkToHandlerAsync( data,
                           handler,
                           method,
                           timeout = _READ_TIMEOUT_SEC,
                           payload = None ):
    request_uri = _BuildUri( handler )
    if method == 'POST':
      sent_data = _ToUtf8Json( data )
      headers = BaseRequest._ExtraHeaders( method,
                                           request_uri,
                                           sent_data )
      _logger.debug( 'POST %s\n%s\n%s', request_uri, headers, sent_data )

      return BaseRequest.Session().post(
        request_uri,
        data = sent_data,
        headers = headers,
        timeout = ( _CONNECT_TIMEOUT_SEC, timeout ) )

    headers = BaseRequest._ExtraHeaders( method, request_uri )

    _logger.debug( 'GET %s (%s)\n%s', request_uri, payload, headers )

    return BaseRequest.Session().get(
      request_uri,
      headers = headers,
      timeout = ( _CONNECT_TIMEOUT_SEC, timeout ),
      params = payload )


  @staticmethod
  def _ExtraHeaders( method, request_uri, request_body = None ):
    if not request_body:
      request_body = bytes( b'' )
    headers = dict( _HEADERS )
    headers[ _HMAC_HEADER ] = b64encode(
        CreateRequestHmac( ToBytes( method ),
                           ToBytes( urlparse( request_uri ).path ),
                           request_body,
                           BaseRequest.hmac_secret ) )
    return headers


  # These two methods exist to avoid importing the requests module at startup;
  # reducing loading time since this module is slow to import.
  @classmethod
  def Requests( cls ):
    try:
      return cls.requests
    except AttributeError:
      import requests
      cls.requests = requests
      return requests


  @classmethod
  def Session( cls ):
    try:
      return cls.session
    except AttributeError:
      from ycm.unsafe_thread_pool_executor import UnsafeThreadPoolExecutor
      from requests_futures.sessions import FuturesSession
      executor = UnsafeThreadPoolExecutor( max_workers = 30 )
      cls.session = FuturesSession( executor = executor )
      return cls.session


  server_location = ''
  hmac_secret = ''


def BuildRequestData( buffer_number = None ):
  """Build request for the current buffer or the buffer with number
  |buffer_number| if specified."""
  working_dir = GetCurrentDirectory()
  current_buffer = vim.current.buffer

  # TODO: Don't assume that the server can do incremental buffer changes.
  vim.Function( 'listener_flush' )()
  incremental = BaseRequest._IncrementalBufferUpdatesSupported( buffer_number )
  if buffer_number and current_buffer.number != buffer_number:
    # Cursor position is irrelevant when filepath is not the current buffer.
    buffer_object = vim.buffers[ buffer_number ]
    filepath = vimsupport.GetBufferFilepath( buffer_object )
    return {
      'filepath': filepath,
      'line_num': 1,
      'column_num': 1,
      'working_dir': working_dir,
      'file_data': vimsupport.GetUnsavedAndSpecifiedBufferData( buffer_object,
                                                                filepath,
                                                                incremental )
    }

  current_filepath = vimsupport.GetBufferFilepath( current_buffer )
  line, column = vimsupport.CurrentLineAndColumn()

  return {
    'filepath': current_filepath,
    'line_num': line + 1,
    'column_num': column + 1,
    'working_dir': working_dir,
    'file_data': vimsupport.GetUnsavedAndSpecifiedBufferData( current_buffer,
                                                              current_filepath,
                                                              incremental )
  }


def _JsonFromFuture( future ):
  response = future.result()
  _logger.debug( 'RX: %s\n%s', response, response.text )
  _ValidateResponseObject( response )
  if response.status_code == BaseRequest.Requests().codes.server_error:
    raise MakeServerException( response.json() )

  # We let Requests handle the other status types, we only handle the 500
  # error code.
  response.raise_for_status()

  if response.text:
    return response.json()
  return None


def _LoadExtraConfFile( filepath ):
  BaseRequest().PostDataToHandler( { 'filepath': filepath },
                                   'load_extra_conf_file' )


def _IgnoreExtraConfFile( filepath ):
  BaseRequest().PostDataToHandler( { 'filepath': filepath },
                                   'ignore_extra_conf_file' )


def DisplayServerException( exception, truncate_message = False ):
  serialized_exception = str( exception )

  # We ignore the exception about the file already being parsed since it comes
  # up often and isn't something that's actionable by the user.
  if 'already being parsed' in serialized_exception:
    return
  vimsupport.PostVimMessage( serialized_exception, truncate = truncate_message )


def _ToUtf8Json( data ):
  return ToBytes( json.dumps( data ) if data else None )


def _ValidateResponseObject( response ):
  our_hmac = CreateHmac( response.content, BaseRequest.hmac_secret )
  their_hmac = ToBytes( b64decode( response.headers[ _HMAC_HEADER ] ) )
  if not compare_digest( our_hmac, their_hmac ):
    raise RuntimeError( 'Received invalid HMAC for response!' )
  return True


def _BuildUri( handler ):
  return ToBytes( urljoin( BaseRequest.server_location, handler ) )


def MakeServerException( data ):
  if data[ 'exception' ][ 'TYPE' ] == UnknownExtraConf.__name__:
    return UnknownExtraConf( data[ 'exception' ][ 'extra_conf_file' ] )

  return ServerError( f'{ data[ "exception" ][ "TYPE" ] }: '
                      f'{ data[ "message" ] }' )

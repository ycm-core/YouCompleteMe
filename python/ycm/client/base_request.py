# Copyright (C) 2013-2020 YouCompleteMe contributors
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
from urllib.parse import urljoin, urlparse, urlencode
from ycm import vimsupport
from ycmd.utils import ToBytes, GetCurrentDirectory, ToUnicode
from ycmd.hmac_utils import CreateRequestHmac, CreateHmac
from ycmd.responses import ServerError, UnknownExtraConf

HTTP_SERVER_ERROR = 500

_HEADERS = { 'content-type': 'application/json' }
_READ_TIMEOUT_SEC = 30
_HMAC_HEADER = 'x-ycm-hmac'
_logger = logging.getLogger( __name__ )

class YCMConnectionError( Exception ):
  pass


class BaseRequest:

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
    except YCMConnectionError as e:
      _logger.debug( 'Failed to establish connection for %s: %s',
                     future.context,
                     e )
    except Exception as e:
      _logger.exception( 'Error while handling server response' )
      if display_message:
        DisplayServerException( e, truncate_message )

    return None


  # This method blocks
  #
  # |timeout| is num seconds to tolerate no response from
  # server before giving up
  #
  # See the HandleFuture method for the |display_message| and
  # |truncate_message| parameters.
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
  # up.
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
  # up.
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
      request_id  = vimsupport.Call( 'youcompleteme#http#POST',
                                     BaseRequest.server_host,
                                     BaseRequest.server_port,
                                     request_uri,
                                     headers,
                                     sent_data )
    else:
      query_string = ''
      if payload:
        query_string = urlencode( payload )

      headers = BaseRequest._ExtraHeaders( method, request_uri )
      _logger.debug( 'GET %s (%s)\n%s', request_uri, query_string, headers )
      request_id  = vimsupport.Call( 'youcompleteme#http#GET',
                                     BaseRequest.server_host,
                                     BaseRequest.server_port,
                                     request_uri,
                                     query_string,
                                     headers )

    future = Future( request_id, request_uri, timeout )
    if request_id is None:
      future.reject( YCMConnectionError( "Unable to connect to server" ) )
    return future


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


  server_location = ''
  server_host = ''
  server_port = 0
  hmac_secret = ''


class Future:
  requests = {}

  def __init__( self, request_id, context, timeout ):
    self.request_id = request_id
    self.context = context

    self._done = False
    self._result = None
    self._exception = None
    self._on_complete_handlers = []
    self._timeout = timeout
    Future.requests[ request_id ] = self


  def done( self ):
    return self._done


  def result( self ):
    if not self.done():
      vimsupport.Call( 'youcompleteme#http#Block',
                       self.request_id,
                       self._timeout * 1000 )

    assert self.done()

    if self._result is None:
      if isinstance( self._exception, Exception ):
        raise self._exception

      raise RuntimeError( self._exception )

    return self._result


  def add_complete_handler( self, handler ):
    self._on_complete_handlers.append( handler )


  def resolve( self, status_code, header_map, data ):
    self._result = Response( status_code, header_map, data )
    self._done = True
    for f in self._on_complete_handlers:
      f( self )


  def reject( self, why ):
    self._result = None
    self._exception = why
    self._done = True


  def __str__( self ):
    return str( self._result )

  def __repr__( self ):
    return repr( self._result )


class Response:
  def __init__( self, status_code, header_map, data ):
    self.text = vimsupport.ToUnicode( data )
    self.content = vimsupport.ToBytes( data )
    self.status_code = status_code
    self.headers = header_map


  # If the response is an error, throw
  def raise_for_status( self ):
    if self.status_code != 200:
      raise RuntimeError(
        "Sever rejected with status: {}".format( self.status_code ) )


  # Returns the json payload
  def json( self ):
    return json.loads( self.text )

  def __str__( self ):
    return str( {
      'content': self.text,
      'status_code': self.status_code,
      'headers': self.headers
    } )


def BuildRequestData( buffer_number = None ):
  """Build request for the current buffer or the buffer with number
  |buffer_number| if specified."""
  working_dir = GetCurrentDirectory()
  current_buffer = vim.current.buffer

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
                                                                filepath )
    }

  current_filepath = vimsupport.GetBufferFilepath( current_buffer )
  line, column = vimsupport.CurrentLineAndColumn()

  return {
    'filepath': current_filepath,
    'line_num': line + 1,
    'column_num': column + 1,
    'working_dir': working_dir,
    'file_data': vimsupport.GetUnsavedAndSpecifiedBufferData( current_buffer,
                                                              current_filepath )
  }



HTTP_SERVER_ERRROR = 500


def _JsonFromFuture( future ):
  # Blocks here if necessary
  response = future.result()
  _logger.debug( 'RX: %s\n%s', response, response.text )
  _ValidateResponseObject( response, ToBytes( response.text ) )
  if response.status_code == HTTP_SERVER_ERRROR:
    raise MakeServerException( response.json() )

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


def _ValidateResponseObject( response, response_text ):
  if not response_text:
    return
  our_hmac = CreateHmac( response_text, BaseRequest.hmac_secret )
  their_hmac = ToBytes( b64decode( response.headers[ _HMAC_HEADER ] ) )
  if not compare_digest( our_hmac, their_hmac ):
    raise RuntimeError( 'Received invalid HMAC for response!' )


def _BuildUri( handler ):
  return ToBytes( urljoin( BaseRequest.server_location, handler ) )


def MakeServerException( data ):
  if data[ 'exception' ][ 'TYPE' ] == UnknownExtraConf.__name__:
    return UnknownExtraConf( data[ 'exception' ][ 'extra_conf_file' ] )

  return ServerError( f'{ data[ "exception" ][ "TYPE" ] }: '
                      f'{ data[ "message" ] }' )

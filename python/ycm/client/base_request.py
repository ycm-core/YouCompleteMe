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
from urllib.parse import urljoin, urlparse, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from ycm import vimsupport
from ycmd.utils import ToBytes, GetCurrentDirectory, ToUnicode
from ycmd.hmac_utils import CreateRequestHmac, CreateHmac
from ycmd.responses import ServerError, UnknownExtraConf

HTTP_SERVER_ERROR = 500

_HEADERS = { 'content-type': 'application/json' }
_CONNECT_TIMEOUT_SEC = 0.01
# Setting this to None seems to screw up the Requests/urllib3 libs.
_READ_TIMEOUT_SEC = 30
_HMAC_HEADER = 'x-ycm-hmac'
_logger = logging.getLogger( __name__ )


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
    except URLError as e:
      # We don't display this exception to the user since it is likely to happen
      # for each subsequent request (typically if the server crashed) and we
      # don't want to spam the user with it.
      _logger.error( e )

    except Exception as e:
      _logger.exception( 'Error while handling server response' )
      if display_message:
        DisplayServerException( e, truncate_message )

    return None


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
    def _MakeRequest( data, handler, method, timeout, payload ):
      request_uri = _BuildUri( handler )

      if method == 'POST':
        sent_data = _ToUtf8Json( data )
        headers = BaseRequest._ExtraHeaders( method,
                                             request_uri,
                                             sent_data )
        _logger.debug( 'POST %s\n%s\n%s', request_uri, headers, sent_data )
      else:
        headers = BaseRequest._ExtraHeaders( method, request_uri )
        if payload:
          request_uri += ToBytes( f'?{urlencode( payload )}' )

        _logger.debug( 'GET %s (%s)\n%s', request_uri, payload, headers )
      return urlopen(
        Request(
          ToUnicode( request_uri ),
          data = sent_data if data else None,
          headers = headers,
          method = method ),
        timeout = max( _CONNECT_TIMEOUT_SEC, timeout ) )


    return BaseRequest.Executor().submit(
      _MakeRequest,
      data,
      handler,
      method,
      timeout,
      payload )


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


  # This method exists to avoid importing the requests module at startup;
  # reducing loading time since this module is slow to import.
  @classmethod
  def Executor( cls ):
    try:
      return cls.executor
    except AttributeError:
      from ycm.unsafe_thread_pool_executor import UnsafeThreadPoolExecutor
      cls.executor = UnsafeThreadPoolExecutor( max_workers = 30 )
      return cls.executor


  server_location = ''
  hmac_secret = ''


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


def _JsonFromFuture( future ):
  try:
    response = future.result()
    response_text = response.read()
    _ValidateResponseObject( response, response_text )
    response.close()

    if response_text:
      return json.loads( response_text )
    return None
  except HTTPError as response:
    if response.code == HTTP_SERVER_ERROR:
      response_text = response.read()
      response.close()
      if response_text:
        raise MakeServerException( json.loads( response_text ) )
      else:
        return None
    raise


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

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

from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm import vimsupport

DEFAULT_BUFFER_COMMAND = 'same-buffer'


def _EnsureBackwardsCompatibility( arguments ):
  if arguments and arguments[ 0 ] == 'GoToDefinitionElseDeclaration':
    arguments[ 0 ] = 'GoTo'
  return arguments


class CommandRequest( BaseRequest ):
  def __init__( self, arguments, extra_data = None, silent = False ):
    super( CommandRequest, self ).__init__()
    self._arguments = _EnsureBackwardsCompatibility( arguments )
    self._command = arguments and arguments[ 0 ]
    self._extra_data = extra_data
    self._response = None
    self._request_data = None
    self._response_future = None
    self._silent = silent
    self._bufnr = extra_data.pop( 'bufnr', None ) if extra_data else None


  def Start( self ):
    if self._bufnr is not None:
      self._request_data = BuildRequestData( self._bufnr )
    else:
      self._request_data = BuildRequestData()

    if self._extra_data:
      self._request_data.update( self._extra_data )
    self._request_data.update( {
      'command_arguments': self._arguments
    } )
    self._response_future = self.PostDataToHandlerAsync(
      self._request_data,
      'run_completer_command' )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Response( self ):
    if self._response is None and self._response_future is not None:
      # Block
      self._response = self.HandleFuture( self._response_future,
                                          display_message = not self._silent )

    return self._response


  def RunPostCommandActionsIfNeeded( self,
                                     modifiers,
                                     buffer_command = DEFAULT_BUFFER_COMMAND ):

    # This is a blocking call if not Done()
    self.Response()

    if self._response is None:
      # An exception was raised and handled.
      return

    # If not a dictionary or a list, the response is necessarily a
    # scalar: boolean, number, string, etc. In this case, we print
    # it to the user.
    if not isinstance( self._response, ( dict, list ) ):
      return self._HandleBasicResponse()

    if 'fixits' in self._response:
      return self._HandleFixitResponse()

    if 'message' in self._response:
      return self._HandleMessageResponse()

    if 'detailed_info' in self._response:
      return self._HandleDetailedInfoResponse()

    # The only other type of response we understand is GoTo, and that is the
    # only one that we can't detect just by inspecting the response (it should
    # either be a single location or a list)
    return self._HandleGotoResponse( buffer_command, modifiers )


  def StringResponse( self ):
    # Retuns a supporable public API version of the response. The reason this
    # exists is that the ycmd API here is wonky as it originally only supported
    # text-responses and now has things like fixits and such.
    #
    # The supportable public API is basically any text-only response. All other
    # response types are returned as empty strings

    # This is a blocking call if not Done()
    self.Response()

    # Completer threw an error ?
    if self._response is None:
      return ""

    # If not a dictionary or a list, the response is necessarily a
    # scalar: boolean, number, string, etc. In this case, we print
    # it to the user.
    if not isinstance( self._response, ( dict, list ) ):
      return str( self._response )

    if 'message' in self._response:
      return self._response[ 'message' ]

    if 'detailed_info' in self._response:
      return self._response[ 'detailed_info' ]

    # The only other type of response we understand is 'fixits' and GoTo. We
    # don't provide string versions of them.
    return ""


  def _HandleGotoResponse( self, buffer_command, modifiers ):
    if isinstance( self._response, list ):
      vimsupport.SetQuickFixList(
        [ vimsupport.BuildQfListItem( x ) for x in self._response ] )
      vimsupport.OpenQuickFixList( focus = True, autoclose = True )
    elif self._response.get( 'file_only' ):
      vimsupport.JumpToLocation( self._response[ 'filepath' ],
                                 None,
                                 None,
                                 modifiers,
                                 buffer_command )
    else:
      vimsupport.JumpToLocation( self._response[ 'filepath' ],
                                 self._response[ 'line_num' ],
                                 self._response[ 'column_num' ],
                                 modifiers,
                                 buffer_command )


  def _HandleFixitResponse( self ):
    if not len( self._response[ 'fixits' ] ):
      vimsupport.PostVimMessage( 'No fixits found for current line',
                                 warning = False )
    else:
      try:
        fixit_index = 0

        # If there is more than one fixit, we need to ask the user which one
        # should be applied.
        #
        # If there's only one, triggered by the FixIt subcommand (as opposed to
        # `RefactorRename`, for example) and whose `kind` is not `quicfix`, we
        # still need to as the user for confirmation.
        fixits = self._response[ 'fixits' ]
        if ( len( fixits ) > 1 or
             ( len( fixits ) == 1 and
               self._command == 'FixIt' and
               fixits[ 0 ].get( 'kind' ) != 'quickfix' ) ):
          fixit_index = vimsupport.SelectFromList(
            "FixIt suggestion(s) available at this location. "
            "Which one would you like to apply?",
            [ fixit[ 'text' ] for fixit in fixits ] )
        chosen_fixit = fixits[ fixit_index ]
        if chosen_fixit[ 'resolve' ]:
          self._request_data.update( { 'fixit': chosen_fixit } )
          response = self.PostDataToHandler( self._request_data,
                                             'resolve_fixit' )
          if response is None:
            return
          fixits = response[ 'fixits' ]
          assert len( fixits ) == 1
          chosen_fixit = fixits[ 0 ]

        vimsupport.ReplaceChunks(
          chosen_fixit[ 'chunks' ],
          silent = self._command == 'Format' )
      except RuntimeError as e:
        vimsupport.PostVimMessage( str( e ) )


  def _HandleBasicResponse( self ):
    vimsupport.PostVimMessage( self._response, warning = False )


  def _HandleMessageResponse( self ):
    vimsupport.PostVimMessage( self._response[ 'message' ], warning = False )


  def _HandleDetailedInfoResponse( self ):
    vimsupport.WriteToPreviewWindow( self._response[ 'detailed_info' ] )


def SendCommandRequestAsync( arguments, extra_data = None, silent = True ):
  request = CommandRequest( arguments,
                            extra_data = extra_data,
                            silent = silent )
  request.Start()
  # Don't block
  return request


def SendCommandRequest( arguments,
                        modifiers,
                        buffer_command = DEFAULT_BUFFER_COMMAND,
                        extra_data = None ):
  request = SendCommandRequestAsync( arguments,
                                     extra_data = extra_data,
                                     silent = False )
  # Block here to get the response
  request.RunPostCommandActionsIfNeeded( modifiers, buffer_command )
  return request.Response()


def GetCommandResponse( arguments, extra_data = None ):
  request = SendCommandRequestAsync( arguments,
                                     extra_data = extra_data,
                                     silent = True )
  # Block here to get the response
  return request.StringResponse()

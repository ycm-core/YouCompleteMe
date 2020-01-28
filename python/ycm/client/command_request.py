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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm import vimsupport
from ycmd.utils import ToUnicode


def _EnsureBackwardsCompatibility( arguments ):
  if arguments and arguments[ 0 ] == 'GoToDefinitionElseDeclaration':
    arguments[ 0 ] = 'GoTo'
  return arguments


class CommandRequest( BaseRequest ):
  def __init__( self,
                arguments,
                buffer_command = 'same-buffer',
                extra_data = None ):
    super( CommandRequest, self ).__init__()
    self._arguments = _EnsureBackwardsCompatibility( arguments )
    self._command = arguments and arguments[ 0 ]
    self._extra_data = extra_data
    self._response = None
    self._request_data = None
    self._response_future = None


  def Start( self ):
    self._request_data = BuildRequestData()
    if self._extra_data:
      self._request_data.update( self._extra_data )
    self._request_data.update( {
      'command_arguments': self._arguments
    } )
    self._response_future = self.PostDataToHandlerAsync(
      self._request_data,
      'run_completer_command' )
    return self._response_future


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Response( self ):
    if self._response is None and self._response_future is not None:
      # Block
      self._response = self.HandleFuture( self._response_future )
      self._response_future = None

    return self._response


  def GetResponseTextOnly( self ):
    if self._response is None and self._response_future is not None:
      # This is a blocking call if not Done()
      self.Response()

    if self._response is None:
      # An exception was raised and handled.
      return

    # If not a dictionary or a list, the response is necessarily a
    # scalar: boolean, number, string, etc. In this case, we print
    # it to the user.
    if not isinstance( self._response, ( dict, list ) ):
      return self._response

    if 'message' in self._response:
      return self._response[ 'message' ]

    if 'detailed_info' in self._response:
      return self._response[ 'detailed_info' ]

    return '[No data]'


  def RunPostCommandActionsIfNeeded( self,
                                     buffer_command,
                                     modifiers ):

    if self._response is None and self._response_future is not None:
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


  def _HandleGotoResponse( self, buffer_command, modifiers ):
    if isinstance( self._response, list ):
      vimsupport.SetQuickFixList(
        [ _BuildQfListItem( x ) for x in self._response ] )
      vimsupport.OpenQuickFixList( focus = True, autoclose = True )
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

        # When there are multiple fixit suggestions, present them as a list to
        # the user hand have her choose which one to apply.
        fixits = self._response[ 'fixits' ]
        if len( fixits ) > 1:
          fixit_index = vimsupport.SelectFromList(
            "Multiple FixIt suggestions are available at this location. "
            "Which one would you like to apply?",
            [ fixit[ 'text' ] for fixit in fixits ] )
        chosen_fixit = fixits[ fixit_index ]
        if chosen_fixit[ 'resolve' ]:
          self._request_data.update( { 'fixit': chosen_fixit } )
          response = self.PostDataToHandler( self._request_data,
                                             'resolve_fixit' )
          fixits = response[ 'fixits' ]
          assert len( fixits ) == 1
          chosen_fixit = fixits[ 0 ]

        vimsupport.ReplaceChunks(
          chosen_fixit[ 'chunks' ],
          silent = self._command == 'Format' )
      except RuntimeError as e:
        vimsupport.PostVimMessage( str( e ) )


  def _HandleBasicResponse( self ):
    vimsupport.PostVimMessage( self._response,
                               warning = False,
                               popup = True )


  def _HandleMessageResponse( self ):
    vimsupport.PostVimMessage( self._response[ 'message' ],
                               warning = False,
                               popup = True )


  def _HandleDetailedInfoResponse( self ):
    vimsupport.WriteToPreviewWindow( self._response[ 'detailed_info' ] )


def SendCommandRequest( arguments,
                        modifiers,
                        buffer_command,
                        extra_data = None ):
  request = CommandRequest( arguments, extra_data )
  request.Start()
  # Block here to get the response
  request.RunPostCommandActionsIfNeeded( buffer_command, modifiers )
  return request.Response()


def _BuildQfListItem( goto_data_item ):
  qf_item = {}
  if 'filepath' in goto_data_item:
    qf_item[ 'filename' ] = ToUnicode( goto_data_item[ 'filepath' ] )
  if 'description' in goto_data_item:
    qf_item[ 'text' ] = ToUnicode( goto_data_item[ 'description' ] )
  if 'line_num' in goto_data_item:
    qf_item[ 'lnum' ] = goto_data_item[ 'line_num' ]
  if 'column_num' in goto_data_item:
    # ycmd returns columns 1-based, and QuickFix lists require "byte offsets".
    # See :help getqflist and equivalent comment in
    # vimsupport.ConvertDiagnosticsToQfList.
    #
    # When the Vim help says "byte index", it really means "1-based column
    # number" (which is somewhat confusing). :help getqflist states "first
    # column is 1".
    qf_item[ 'col' ] = goto_data_item[ 'column_num' ]

  return qf_item

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
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from requests.exceptions import ReadTimeout
import vim

from ycmd.responses import ServerError
from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                      HandleServerException )
from ycm import vimsupport
from ycmd.utils import ToUnicode


def _EnsureBackwardsCompatibility( arguments ):
  if arguments and arguments[ 0 ] == 'GoToDefinitionElseDeclaration':
    arguments[ 0 ] = 'GoTo'
  return arguments


class CommandRequest( BaseRequest ):
  def __init__( self, arguments, completer_target = None ):
    super( CommandRequest, self ).__init__()
    self._arguments = _EnsureBackwardsCompatibility( arguments )
    self._completer_target = ( completer_target if completer_target
                               else 'filetype_default' )
    self._response = None


  def Start( self, request_data = None ):
    if request_data is None:
      request_data = BuildRequestData()
    request_data.update( {
      'completer_target': self._completer_target,
      'command_arguments': self._arguments
    } )
    try:
      self._response = self.PostDataToHandler( request_data,
                                               'run_completer_command' )
    except ( ServerError, ReadTimeout ) as e:
      HandleServerException( e )


  def Response( self ):
    return self._response


  def RunPostCommandActionsIfNeeded( self ):
    if not self.Done() or self._response is None:
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
    return self._HandleGotoResponse()


  def _HandleGotoResponse( self ):
    if isinstance( self._response, list ):
      vimsupport.SetQuickFixList(
              [ _BuildQfListItem( x ) for x in self._response ] )
      vim.eval( 'youcompleteme#OpenGoToList()' )
    else:
      vimsupport.JumpToLocation( self._response[ 'filepath' ],
                                 self._response[ 'line_num' ],
                                 self._response[ 'column_num' ] )


  def _HandleFixitResponse( self ):
    if not len( self._response[ 'fixits' ] ):
      vimsupport.EchoText( "No fixits found for current line" )
    else:
      chunks = self._response[ 'fixits' ][ 0 ][ 'chunks' ]
      try:
        vimsupport.ReplaceChunks( chunks )
      except RuntimeError as e:
        vimsupport.PostMultiLineNotice( str( e ) )


  def _HandleBasicResponse( self ):
    vimsupport.EchoText( self._response )


  def _HandleMessageResponse( self ):
    vimsupport.EchoText( self._response[ 'message' ] )


  def _HandleDetailedInfoResponse( self ):
    vimsupport.WriteToPreviewWindow( self._response[ 'detailed_info' ] )


def SendCommandRequest( arguments, completer, request_data = None, run_post_actions = True ):
  request = CommandRequest( arguments, completer )
  # This is a blocking call.
  request.Start( request_data )
  if run_post_actions:
    request.RunPostCommandActionsIfNeeded()
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

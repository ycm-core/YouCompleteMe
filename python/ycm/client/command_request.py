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

import time
from ycm.client.base_request import BaseRequest, BuildRequestData


class CommandRequest( BaseRequest ):
  class ServerResponse( object ):
    def __init__( self ):
      pass

    def Valid( self ):
      return True

  def __init__( self, arguments, completer_target = None ):
    super( CommandRequest, self ).__init__()
    self._arguments = arguments
    self._completer_target = ( completer_target if completer_target
                               else 'filetype_default' )
    # TODO: Handle this case.
    # if completer_target == 'omni':
    #   completer = SERVER_STATE.GetOmniCompleter()

  def Start( self ):
    request_data = BuildRequestData()
    request_data.update( {
      'completer_target': self._completer_target,
      'command_arguments': self._arguments
    } )
    self._response = self.PostDataToHandler( request_data,
                                             'run_completer_command' )


  def Response( self ):
    # TODO: Call vimsupport.JumpToLocation if the user called a GoTo command...
    # we may want to have specific subclasses of CommandRequest so that a
    # GoToRequest knows it needs to jump after the data comes back.
    #
    # Also need to run the following on GoTo data:
    #
    # CAREFUL about line/column number 0-based/1-based confusion!
    #
    # defs = []
    # defs.append( {'filename': definition.module_path.encode( 'utf-8' ),
    #               'lnum': definition.line,
    #               'col': definition.column + 1,
    #               'text': definition.description.encode( 'utf-8' ) } )
    # vim.eval( 'setqflist( %s )' % repr( defs ) )
    # vim.eval( 'youcompleteme#OpenGoToList()' )
    return self.ServerResponse()


def SendCommandRequest( self, arguments, completer ):
  request = CommandRequest( self, arguments, completer )
  request.Start()
  while not request.Done():
    time.sleep( 0.1 )

  return request.Response()


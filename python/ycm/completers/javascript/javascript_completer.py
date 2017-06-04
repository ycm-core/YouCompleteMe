#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
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

from ycm.completers.completer import Completer
from ycm.server import responses
from ycm import utils
import subprocess
import requests
import logging
import json
import os

#TODO
SERVER_NOT_FOUND_MSG = ( 'Tern binary not found at {0}.' )


class JSCompleter( Completer ):
  """
  A Completer that uses the JavaScript Tern server as completion engine.
  """

  def __init__( self, user_options ):
    super( JSCompleter, self ).__init__( user_options )
    self._server = None
    self._js_port = None
    self._logger = logging.getLogger( __name__ )


  def Shutdown( self ):
    #TODO add user options
    if ( self._ServerIsRunning() ):
      self._StopServer()


  def SupportedFiletypes( self ):
    """ Just JS """
    return [ 'javascript' ]


  def ComputeCandidatesInner( self, request_data ):
    return [ responses.BuildCompletionData(
                completion[ 'name' ],
                completion[ 'type' ],
                completion[ 'doc' ] )
             for completion in self._GetCompletions( request_data )['completions'] ]


  def DefinedSubcommands( self ):
    return [ 'StartServer',
             'StopServer',
             'RestartServer',
             'ServerRunning',
             'GoToDefinition',
             'GoToDeclaration',
             'GoToDefinitionElseDeclaration' ]


  def OnFileReadyToParse( self, request_data ):
    #TODO for some reason YCM creates 2 Tern instances on startup. This means
    #that YCM creates 2 JSCompleter instances on start-up but uses only second.
    #need to investigate.
    #TODO add user options
    self._logger.info("start")
    self._logger.info(self)
    if not self._server:
      #TODO handle multiple files
      self._StartServer( request_data )


  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command = arguments[ 0 ]
    if command == 'StartServer':
      return self._StartServer( request_data )
    elif command == 'StopServer':
      #TODO
      return self._StopServer()
    elif command == 'RestartServer':
      #TODO
      if self._ServerIsRunning():
        self._StopServer()
      return self._StartServer( request_data )
    elif command == 'ServerRunning':
      #TODO
      return self._ServerIsRunning()
    elif command in [ 'GoToDefinition',
                      'GoToDeclaration',
                      'GoToDefinitionElseDeclaration' ]:
      #TODO
      return self._GoToDefinition( request_data )
    raise ValueError( self.UserCommandsHelpMessage() )


  def DebugInfo( self ):
    if self._ServerIsRunning():
      return 'Server running at: {0}\nLogfiles:\n{1}\n{2}'.format(
        self._ServerLocation(), self._filename_stdout, self._filename_stderr )
    else:
      return 'Server is not running'


  def _StartServer( self, request_data ):
    self._logger.info( 'Starting JS server' )

    self._js_port = utils.GetUnusedLocalhostPort()
    #self._js_port = 12303
    tern_path = os.path.join( os.path.dirname( __file__ ),
        "node_modules/tern/bin/tern" )

    if not os.path.isfile( tern_path ):
      raise RuntimeError( SERVER_NOT_FOUND_MSG.format( tern_path ) )

    command = ["node", tern_path, "--port", str( self._js_port ),
        "--persistent", "--no-port-file"]

    filename_format = os.path.join( utils.PathToTempDir(),
                                   'javascript_{port}__{std}.log' )

    self._filename_stdout = filename_format.format(
        port=self._js_port, std='stdout' )
    self._filename_stderr = filename_format.format(
        port=self._js_port, std='stderr' )

    with open( self._filename_stderr, 'w' ) as fstderr:
      with open( self._filename_stdout, 'w' ) as fstdout:
        self._server = subprocess.Popen( command, stdout=fstdout,
            stderr=fstderr, shell=True )


  def _StopServer( self ):
    #TODO when popen is called with Shell=True object gets the pid
    #of the parent shell, not the server. So the terminate() and kill()
    #will not work (at least on Windows)
    if self._server:
      self._logger.info("Stopping JS Server")
      self._server.kill()
      self._server = None


  def _ServerIsRunning( self ):
    #TODO see note in _StopServer
    # poll() returns None when process is running
    return self._server and not self._server.poll()


  def _ServerLocation( self ):
    return 'http://localhost:' + str( self._js_port )


  def _GetCompletions( self, request_data ):
    filepath = request_data['filepath']
    query = {"end": {"line": request_data['line_num'],
                    "ch": request_data['column_num']},
             "file": "#0",
             "type": "completions",
             "docs": True,
             "lineCharPositions": True,
             "types": True}

    files = {"text": request_data['file_data'][filepath]['contents'],
            "type": "full",
            "name": os.path.basename(filepath)}

    doc = {"files": [files], "query": query}
    completions = self._GetResponse( doc )
    return completions if completions is not None else []


  def _BuildRequest( self, request_data, chunked=False ):
    #TODO add chunked requests
    #TODO handle multiple files
    return parameters


  def _GetResponse( self, data, silent = False ):
    """ Handle communication with server """
    parameters = json.dumps(data)
    response = requests.post( self._ServerLocation(), data=parameters )
    return response.json()


  def _GoToDefinition( self, request_data ):
    pass

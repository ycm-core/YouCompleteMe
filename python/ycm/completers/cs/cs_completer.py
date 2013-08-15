#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Chiel ten Brinke <ctenbrinke@gmail.com>
#                           Strahinja Val Markovic <val@markovic.io>
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
import os
from sys import platform
import glob
from ycm.completers.threaded_completer import ThreadedCompleter
from ycm import vimsupport
import urllib2
import urllib
import urlparse
import json
import subprocess
import tempfile


SERVER_NOT_FOUND_MSG = ( 'OmniSharp server binary not found at {0}. ' +
'Did you compile it? You can do so by running ' +
'"./install.sh --omnisharp_completer".' )

class CsharpCompleter( ThreadedCompleter ):
  """
  A Completer that uses the Omnisharp server as completion engine.
  """

  def __init__( self ):
    super( CsharpCompleter, self ).__init__()
    self._omnisharp_port = int( vimsupport.GetVariableValue(
        'g:ycm_csharp_server_port' ) )

    if vimsupport.GetBoolValue( 'g:ycm_auto_start_csharp_server' ):
      self._StartServer()


  def OnVimLeave( self ):
    if ( vimsupport.GetBoolValue( 'g:ycm_auto_stop_csharp_server' ) and
         self._ServerIsRunning() ):
      self._StopServer()


  def SupportedFiletypes( self ):
    """ Just csharp """
    return [ 'cs' ]


  def ComputeCandidates( self, unused_query, unused_start_column ):
    return [ { 'word': str( completion[ 'CompletionText' ] ),
               'menu': str( completion[ 'DisplayText' ] ),
               'info': str( completion[ 'Description' ] ) }
             for completion in self._GetCompletions() ]


  def DefinedSubcommands( self ):
    return [ 'StartServer',
             'StopServer',
             'RestartServer' ]


  def OnUserCommand( self, arguments ):
    if not arguments:
      self.EchoUserCommandsHelpMessage()
      return

    command = arguments[ 0 ]
    if command == 'StartServer':
      self._StartServer()
    elif command == 'StopServer':
      self._StopServer()
    elif command == 'RestartServer':
      if self._ServerIsRunning():
        self._StopServer()
      self._StartServer()


  def DebugInfo( self ):
    if self._ServerIsRunning():
      return 'Server running at: {}\nLogfiles:\n{}\n{}'.format(
        self._PortToHost(), self._filename_stdout, self._filename_stderr )
    else:
      return 'Server is not running'


  def _StartServer( self ):
    """ Start the OmniSharp server """
    self._omnisharp_port = self._FindFreePort()
    solutionfiles, folder = _FindSolutionFiles()

    if len( solutionfiles ) == 0:
      vimsupport.PostVimMessage(
              'Error starting OmniSharp server: no solutionfile found' )
      return
    elif len( solutionfiles ) == 1:
      solutionfile = solutionfiles[ 0 ]
    else:
      choice = vimsupport.PresentDialog(
              'Which solutionfile should be loaded?',
              [ str( i ) + " " + solution for i, solution in
                enumerate( solutionfiles ) ] )
      if choice == -1:
        vimsupport.PostVimMessage( 'OmniSharp not started' )
        return
      else:
        solutionfile = solutionfiles[ choice ]

    omnisharp = os.path.join(
      os.path.abspath( os.path.dirname( __file__ ) ),
      'OmniSharpServer/OmniSharp/bin/Debug/OmniSharp.exe' )

    if not os.path.isfile( omnisharp ):
      vimsupport.PostVimMessage( SERVER_NOT_FOUND_MSG.format( omnisharp ) )
      return

    if not platform.startswith( 'win' ):
      omnisharp = 'mono ' + omnisharp

    path_to_solutionfile = os.path.join( folder, solutionfile )
    # command has to be provided as one string for some reason
    command = [ omnisharp + ' -p ' + str( self._omnisharp_port ) + ' -s ' +
                path_to_solutionfile ]

    filename_format = ( tempfile.gettempdir() +
                        '/omnisharp_{port}_{sln}_{std}.log' )

    self._filename_stdout = filename_format.format(
        port=self._omnisharp_port, sln=solutionfile, std='stdout' )
    self._filename_stderr = filename_format.format(
        port=self._omnisharp_port, sln=solutionfile, std='stderr' )

    with open( self._filename_stderr, 'w' ) as fstderr:
      with open( self._filename_stdout, 'w' ) as fstdout:
        subprocess.Popen( command, stdout=fstdout, stderr=fstderr, shell=True )

    vimsupport.PostVimMessage( 'Starting OmniSharp server' )


  def _StopServer( self ):
    """ Stop the OmniSharp server """
    self._GetResponse( '/stopserver' )
    self._omnisharp_port = int( vimsupport.GetVariableValue(
        'g:ycm_csharp_server_port' ) )
    vimsupport.PostVimMessage( 'Stopping OmniSharp server' )


  def _ServerIsRunning( self, port=None ):
    """ Check if the OmniSharp server is running """
    return self._GetResponse( '/checkalivestatus',
                              silent=True,
                              port=port ) != None


  def _FindFreePort( self ):
    """ Find port without an omnisharp instance running on it """
    port = self._omnisharp_port
    while self._ServerIsRunning( port ):
      port += 1
    return port


  def _PortToHost( self, port=None ):
    if port == None:
      port = self._omnisharp_port
    return 'http://localhost:' + str( port )


  def _GetCompletions( self ):
    """ Ask server for completions """
    line, column = vimsupport.CurrentLineAndColumn()

    parameters = {}
    parameters[ 'line' ], parameters[ 'column' ] = line + 1, column + 1
    parameters[ 'buffer' ] = '\n'.join( vim.current.buffer )
    parameters[ 'filename' ] = vim.current.buffer.name

    completions = self._GetResponse( '/autocomplete', parameters )
    return completions if completions != None else []


  def _GetResponse( self, endPoint, parameters={}, silent=False, port=None ):
    """ Handle communication with server """
    target = urlparse.urljoin( self._PortToHost( port ), endPoint )
    parameters = urllib.urlencode( parameters )
    try:
      response = urllib2.urlopen( target, parameters )
      return json.loads( response.read() )
    except Exception:
      # TODO: Add logging for this case. We can't post a Vim message because Vim
      # crashes when that's done from a no-GUI thread.
      return None


def _FindSolutionFiles():
  folder = os.path.dirname( vim.current.buffer.name )
  solutionfiles = glob.glob1( folder, '*.sln' )
  while not solutionfiles:
    lastfolder = folder
    folder = os.path.dirname( folder )
    if folder == lastfolder:
      break
    solutionfiles = glob.glob1( folder, '*.sln' )
  return solutionfiles, folder

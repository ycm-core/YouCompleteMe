#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Chiel ten Brinke <ctenbrinke@gmail.com>
#                           Google Inc.
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

import os
import glob
from ycm.completers.completer import Completer
from ycm.server import responses
from ycm import utils
import urllib2
import urllib
import urlparse
import json
import logging

SERVER_NOT_FOUND_MSG = ( 'OmniSharp server binary not found at {0}. ' +
'Did you compile it? You can do so by running ' +
'"./install.sh --omnisharp-completer".' )


class CsharpCompleter( Completer ):
  """
  A Completer that uses the Omnisharp server as completion engine.
  """

  subcommands = {
    'StartServer': (lambda self, request_data: self._StartServer( request_data )),
    'StopServer': (lambda self, request_data: self._StopServer()),
    'RestartServer': (lambda self, request_data: self._RestartServer( request_data )),
    'ReloadSolution': (lambda self, request_data: self._ReloadSolution()),
    'ServerRunning': (lambda self, request_data: self._ServerIsRunning()),
    'ServerReady': (lambda self, request_data: self._ServerIsReady()),
    'GoToDefinition': (lambda self, request_data: self._GoToDefinition( request_data )),
    'GoToDeclaration': (lambda self, request_data: self._GoToDefinition( request_data )),
    'GoToDefinitionElseDeclaration': (lambda self, request_data: self._GoToDefinition( request_data ))
  }

  def __init__( self, user_options ):
    super( CsharpCompleter, self ).__init__( user_options )
    self._omnisharp_port = None
    self._logger = logging.getLogger( __name__ )


  def Shutdown( self ):
    if ( self.user_options[ 'auto_stop_csharp_server' ] and
         self._ServerIsRunning() ):
      self._StopServer()


  def SupportedFiletypes( self ):
    """ Just csharp """
    return [ 'cs' ]


  def ComputeCandidatesInner( self, request_data ):
    return [ responses.BuildCompletionData(
                completion[ 'CompletionText' ],
                completion[ 'DisplayText' ],
                completion[ 'Description' ] )
             for completion in self._GetCompletions( request_data ) ]


  def DefinedSubcommands( self ):
    return CsharpCompleter.subcommands.keys()


  def OnFileReadyToParse( self, request_data ):
    if ( not self._omnisharp_port and
         self.user_options[ 'auto_start_csharp_server' ] ):
      self._StartServer( request_data )


  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command = arguments[ 0 ]
    if command in CsharpCompleter.subcommands:
      command_lamba = CsharpCompleter.subcommands[ command ]
      return command_lamba( self, request_data )
    else:
      raise ValueError( self.UserCommandsHelpMessage() )


  def DebugInfo( self ):
    if self._ServerIsRunning():
      return 'Server running at: {0}\nLogfiles:\n{1}\n{2}'.format(
        self._ServerLocation(), self._filename_stdout, self._filename_stderr )
    else:
      return 'Server is not running'


  def _StartServer( self, request_data ):
    """ Start the OmniSharp server """
    self._logger.info( 'startup' )

    self._omnisharp_port = utils.GetUnusedLocalhostPort()
    solution_files, folder = _FindSolutionFiles( request_data[ 'filepath' ] )

    if len( solution_files ) == 0:
      raise RuntimeError(
        'Error starting OmniSharp server: no solutionfile found' )
    elif len( solution_files ) == 1:
      solutionfile = solution_files[ 0 ]
    else:
      # multiple solutions found : if there is one whose name is the same
      # as the folder containing the file we edit, use this one
      # (e.g. if we have bla/Project.sln and we are editing
      # bla/Project/Folder/File.cs, use bla/Project.sln)
      filepath_components = _PathComponents( request_data[ 'filepath' ] )
      solutionpath = _PathComponents( folder )
      foldername = ''
      if len( filepath_components ) > len( solutionpath ):
          foldername = filepath_components[ len( solutionpath ) ]
      solution_file_candidates = [ sfile for sfile in solution_files
        if _GetFilenameWithoutExtension( sfile ) == foldername ]
      if len( solution_file_candidates ) == 1:
        solutionfile = solution_file_candidates[ 0 ]
      else:
        raise RuntimeError(
          'Found multiple solution files instead of one!\n{0}'.format(
            solution_files ) )

    omnisharp = os.path.join(
      os.path.abspath( os.path.dirname( __file__ ) ),
      'OmniSharpServer/OmniSharp/bin/Debug/OmniSharp.exe' )

    if not os.path.isfile( omnisharp ):
      raise RuntimeError( SERVER_NOT_FOUND_MSG.format( omnisharp ) )

    path_to_solutionfile = os.path.join( folder, solutionfile )
    # we need to pass the command to Popen as a string since we're passing
    # shell=True (as recommended by Python's doc)
    command = ( omnisharp + ' -p ' + str( self._omnisharp_port ) + ' -s ' +
                path_to_solutionfile )

    if not utils.OnWindows():
      command = 'mono ' + command

    filename_format = os.path.join( utils.PathToTempDir(),
                                   'omnisharp_{port}_{sln}_{std}.log' )

    self._filename_stdout = filename_format.format(
        port=self._omnisharp_port, sln=solutionfile, std='stdout' )
    self._filename_stderr = filename_format.format(
        port=self._omnisharp_port, sln=solutionfile, std='stderr' )

    with open( self._filename_stderr, 'w' ) as fstderr:
      with open( self._filename_stdout, 'w' ) as fstdout:
        # shell=True is needed for Windows so OmniSharp does not spawn
        # in a new visible window
        utils.SafePopen( command, stdout=fstdout, stderr=fstderr, shell=True )

    self._logger.info( 'Starting OmniSharp server' )


  def _StopServer( self ):
    """ Stop the OmniSharp server """
    self._GetResponse( '/stopserver' )
    self._omnisharp_port = None
    self._logger.info( 'Stopping OmniSharp server' )


  def _RestartServer ( self, request_data ):
    """ Restarts the OmniSharp server """
    if self._ServerIsRunning():
      self._StopServer()
    return self._StartServer( request_data )


  def _ReloadSolution( self ):
    """ Reloads the solutions in the OmniSharp server """
    self._logger.info( 'Reloading Solution in OmniSharp server' )
    return self._GetResponse( '/reloadsolution' )


  def _GetCompletions( self, request_data ):
    """ Ask server for completions """
    completions = self._GetResponse( '/autocomplete',
                                     self._DefaultParameters( request_data ) )
    return completions if completions != None else []


  def _GoToDefinition( self, request_data ):
    """ Jump to definition of identifier under cursor """
    definition = self._GetResponse( '/gotodefinition',
                                    self._DefaultParameters( request_data ) )
    if definition[ 'FileName' ] != None:
      return responses.BuildGoToResponse( definition[ 'FileName' ],
                                          definition[ 'Line' ],
                                          definition[ 'Column' ] )
    else:
      raise RuntimeError( 'Can\'t jump to definition' )


  def _DefaultParameters( self, request_data ):
    """ Some very common request parameters """
    parameters = {}
    parameters[ 'line' ] = request_data[ 'line_num' ] + 1
    parameters[ 'column' ] = request_data[ 'column_num' ] + 1
    filepath = request_data[ 'filepath' ]
    parameters[ 'buffer' ] = request_data[ 'file_data' ][ filepath ][
      'contents' ]
    parameters[ 'filename' ] = filepath
    return parameters


  def _ServerIsRunning( self ):
    """ Check if our OmniSharp server is running """
    try:
      return bool( self._omnisharp_port and
                  self._GetResponse( '/checkalivestatus', silent = True ) )
    except:
      return False


  def _ServerIsReady( self ):
    """ Check if our OmniSharp server is ready """
    try:
      return bool( self._omnisharp_port and
                  self._GetResponse( '/checkreadystatus', silent = True ) )
    except:
      return False


  def _ServerLocation( self ):
    return 'http://localhost:' + str( self._omnisharp_port )


  def _GetResponse( self, handler, parameters = {}, silent = False ):
    """ Handle communication with server """
    # TODO: Replace usage of urllib with Requests
    target = urlparse.urljoin( self._ServerLocation(), handler )
    parameters = urllib.urlencode( parameters )
    response = urllib2.urlopen( target, parameters )
    return json.loads( response.read() )


def _FindSolutionFiles( filepath ):
  """ Find solution files by searching upwards in the file tree """
  folder = os.path.dirname( filepath )
  solutionfiles = glob.glob1( folder, '*.sln' )
  while not solutionfiles:
    lastfolder = folder
    folder = os.path.dirname( folder )
    if folder == lastfolder:
      break
    solutionfiles = glob.glob1( folder, '*.sln' )
  return solutionfiles, folder

def _PathComponents( path ):
  path_components = []
  while True:
    path, folder = os.path.split( path )
    if folder:
      path_components.append( folder )
    else:
      if path:
        path_components.append( path )
      break
  path_components.reverse()
  return path_components

def _GetFilenameWithoutExtension( path ):
    return os.path.splitext( os.path.basename ( path ) )[ 0 ]


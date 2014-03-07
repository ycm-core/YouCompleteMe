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
from ycm import extra_conf_store
from ycm.completers.completer import Completer
from ycm.server import responses
from ycm import utils
import urllib2
import urllib
import urlparse
import json
import logging
from inspect import getfile

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

  def _PollModuleForSolutionFile( self, module, filepath):
    path_to_solutionfile=None
    preferred_name=None
    if module:
      try:
        preferred_name = module.CSharpSolutionFile( filepath )
        self._logger.info( 'extra_conf_store suggests {0} as solution file'.format(
            str( preferred_name ) ) )
        if preferred_name:
          # received a full path or the name of a solution right next to the config?
          candidates = [ preferred_name,
            os.path.join( os.path.dirname( getfile( module ) ),
                          preferred_name ),
            os.path.normpath( os.path.join( os.path.dirname( getfile( module ) ),
                          "{0}.sln".format(preferred_name) ) ) ]
          # try the assumptions
          for path in candidates:
            if os.path.isfile( path ):
              # path seems to point to a solution
              path_to_solutionfile = path
              self._logger.info(
                  'Using solution file {0} selected by extra_conf_store'.format(
                  path_to_solutionfile) )
              break
          # if no solution file found, use the filename as hint later
          preferred_name=os.path.basename(preferred_name)
      except AttributeError, e:
        # the config script might not provide solution file locations
        self._logger.error(
            'Could not retrieve solution for {0} from extra_conf_store: {1}'.format(
            filepath, str( e )) )
        preferred_name = None
    return path_to_solutionfile, preferred_name

  def _StartServer( self, request_data ):
    """ Start the OmniSharp server """
    self._logger.info( 'startup' )

    # try to load ycm_extra_conf
    # if it needs to be verified, abort here and try again later
    filepath = request_data[ 'filepath' ]
    module = extra_conf_store.ModuleForSourceFile( filepath )
    path_to_solutionfile, preferred_name = self._PollModuleForSolutionFile(module, filepath)

    self._omnisharp_port = utils.GetUnusedLocalhostPort()

    if not path_to_solutionfile:
      # no solution file provided, try to find one
      path_to_solutionfile = self._GuessSolutionFile( request_data[ 'filepath' ], preferred_name )

    if not path_to_solutionfile:
      raise RuntimeError( 'Autodetection of solution file failed.\n' )
    self._logger.info( 'Loading solution file {0}'.format( path_to_solutionfile ) )

    omnisharp = os.path.join(
      os.path.abspath( os.path.dirname( __file__ ) ),
      'OmniSharpServer/OmniSharp/bin/Debug/OmniSharp.exe' )

    if not os.path.isfile( omnisharp ):
      raise RuntimeError( SERVER_NOT_FOUND_MSG.format( omnisharp ) )

    # we need to pass the command to Popen as a string since we're passing
    # shell=True (as recommended by Python's doc)
    command = ( omnisharp + ' -p ' + str( self._omnisharp_port ) + ' -s ' +
                path_to_solutionfile )

    if not utils.OnWindows():
      command = 'mono ' + command

    filename_format = os.path.join( utils.PathToTempDir(),
                                   'omnisharp_{port}_{sln}_{std}.log' )

    solutionfile = os.path.basename( path_to_solutionfile )
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

  def _SolutionTestCheckPreferred( self, path, candidates, preferred_name ):
    """ Check if one of the candidates matches preferred_name hint """
    if preferred_name:
      check = [ c for c in candidates
          if ( preferred_name == c ) ]
      if len( check ) == 1:
        selection = os.path.join( path, check[0] )
        self._logger.info(
            'Selected solution file {0} as it matches {1} (from extra_conf_store)'.format(
            selection, preferred_name ) )
        return selection
      elif len( check ) == 2:
        # pick the one ending in sln, can misbehave if there is a file.sln.sln
        selection = os.path.join( path, "%s.sln"%preferred_name )
        self._logger.info(
            'Selected solution file {0} as it matches {1} (from extra_conf_store)'.format(
            selection, preferred_name ) )
        return selection

  def _SolutionTestCheckHeuristics( self, candidates, tokens, i ):
    """ Test if one of the candidate files stands out """
    path = os.path.join( *tokens[:i + 1] )
    selection=None
    # if there is just one file here, use that
    if len( candidates ) == 1 :
      selection = os.path.join( path, candidates[0] )
      self._logger.info(
          'Selected solution file {0} as it is the first one found'.format(
          selection ) )
    # there is more than one file, try some hints to decide
    # 1. is there a solution named just like the subdirectory with the source?
    if (not selection and i < len( tokens ) - 1 and
        "{0}.sln".format( tokens[i + 1] ) in candidates ):
      selection = os.path.join( path, "{0}.sln".format( tokens[i + 1] ) )
      self._logger.info(
          'Selected solution file {0} as it matches source subfolder'.format(
          selection ) )
    # 2. is there a solution named just like the directory containing the solution?
    if not selection and "{0}.sln".format( tokens[i] ) in candidates:
      selection = os.path.join( path, "{0}.sln".format( tokens[i] ) )
      self._logger.info(
          'Selected solution file {0} as it matches containing folder'.format(
          selection ) )
    if not selection:
      self._logger.error(
          'Could not decide between multiple solution files:\n{0}'.format(
          candidates ) )
    return selection

  def _GuessSolutionFile( self, filepath, preferred_name ):
    """ Find solution files by searching upwards in the file tree """
    tokens = _PathComponents( filepath )
    selection = None
    first_hit = True
    for i in reversed( range( len( tokens ) - 1 ) ):
      path = os.path.join( *tokens[:i + 1] )
      candidates = glob.glob1( path, "*.sln" )
      if len( candidates ) > 0:
        # if a name was provided, try hard to find something matching
        final = self._SolutionTestCheckPreferred( path, candidates, preferred_name )
        if final:
          return final
        # do the whole procedure only for the first solution file(s) you find
        if first_hit :
          selection = self._SolutionTestCheckHeuristics( candidates, tokens, i )
          # we could not decide and aren't looking for anything specific, giving up
          if not preferred_name:
            return selection
        first_hit = False
    return selection

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



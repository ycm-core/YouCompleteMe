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
import glob
from ycm.completers.threaded_completer import ThreadedCompleter
from ycm import vimsupport
import urllib2
import urllib
import urlparse
import json
import subprocess


class CsharpCompleter( ThreadedCompleter ):
  """
  A Completer that uses the Omnisharp server as completion engine.
  """

  def __init__( self ):
    super( CsharpCompleter, self ).__init__()
    self.OmniSharpPort = 2000
    self.OmniSharpHost = 'http://localhost:' + str( self.OmniSharpPort )
    #self._StartServer()

  def SupportedFiletypes( self ):
    """ Just csharp """
    return [ 'cs' ]

  def ComputeCandidates( self, unused_query, unused_start_column ):
    return [ { 'word': str( completion['CompletionText'] ),
               'menu': str( completion['DisplayText'] ),
               'info': str( completion['Description'] ) }
             for completion in self._GetCompletions() ]

  def DefinedSubcommands( self ):
    return [ 'StartServer',
             'StopServer' ]

  def OnUserCommand( self, arguments ):
    if not arguments:
      self.EchoUserCommandsHelpMessage()
      return

    command = arguments[ 0 ]
    if command == 'StartServer':
      self._StartServer()
    elif command == 'StopServer':
      self._StopServer()

  def _StartServer( self ):
    """ Start the OmniSharp server """
    if ( not self._ServerIsRunning() ):
      folder = os.path.dirname( vim.current.buffer.name )
      solutionfiles = glob.glob1( folder, '*.sln' )
      while not solutionfiles:
        lastfolder = folder
        folder = os.path.dirname( folder )
        if folder == lastfolder:
          break
        solutionfiles = glob.glob1( folder, '*.sln' )

      if len( solutionfiles ) == 0:
        vimsupport.PostVimMessage( 'Error starting OmniSharp server: no solutionfile found' )
      elif len( solutionfiles ) == 1:
        omnisharp = os.path.join( os.path.abspath( os.path.dirname( __file__ ) ),
                'OmniSharpServer/OmniSharp/bin/Debug/OmniSharp.exe' )
        solutionfile = os.path.join ( folder, solutionfiles[0] )
        command = [ omnisharp, '-p ' + str( self.OmniSharpPort ), '-s ' + solutionfile ]

        vimsupport.PostVimMessage( 'starting server... ' + ' '.join( command ) )

        # Why doesn't this work properly?
        # When starting manually in seperate console, everything works
        # Maybe due to bothering stdin/stdout redirecting?
        subprocess.Popen( command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
      else:
        vimsupport.PostVimMessage( 'Error starting OmniSharp server: multiple solutionfiles found' )

  def _StopServer( self ):
    """ Stop the OmniSharp server """
    self._GetResponse( '/stopserver' )

  def _ServerIsRunning( self ):
    """ Check if the OmniSharp server is running """
    self._StopServer() # temporal fix
    return False

  def _GetCompletions( self ):
    """ Ask server for completions """
    line, column = vimsupport.CurrentLineAndColumn()

    parameters = {}
    parameters['line'], parameters['column'] = line + 1, column + 1
    parameters['buffer'] = '\n'.join( vim.current.buffer )
    parameters['filename'] = vim.current.buffer.name

    completions = self._GetResponse( '/autocomplete', parameters ) 
    return completions if completions != None else []

  def _GetResponse( self, endPoint, parameters={} ):
    """ Handle communication with server """
    target = urlparse.urljoin( self.OmniSharpHost, endPoint )
    parameters = urllib.urlencode( parameters )
    try:
      response = urllib2.urlopen( target, parameters )
      return json.loads( response.read() )
    except Exception as e:
      vimsupport.PostVimMessage('OmniSharp : Could not connect to ' + target + ': ' + str(e))
      return None

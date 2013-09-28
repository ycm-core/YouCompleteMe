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

import sys
import os
import atexit

# We want to have the YouCompleteMe/python directory on the Python PATH because
# all the code already assumes that it's there. This is a relic from before the
# client/server architecture.
# TODO: Fix things so that this is not needed anymore when we split ycmd into a
# separate repository.
sys.path.insert( 0, os.path.join(
                        os.path.dirname( os.path.abspath( __file__ ) ),
                        '../..' ) )

import logging
import time
import json
import bottle
from bottle import run, request, response
import server_state
from ycm import user_options_store
from ycm.server.responses import BuildExceptionResponse
import argparse
import httplib

# num bytes for the request body buffer; request.json only works if the request
# size is less than this
bottle.Request.MEMFILE_MAX = 300 * 1024

SERVER_STATE = None
LOGGER = None
app = bottle.Bottle()


@app.post( '/event_notification' )
def EventNotification():
  LOGGER.info( 'Received event notification')
  request_data = request.json
  event_name = request_data[ 'event_name' ]
  LOGGER.debug( 'Event name: %s', event_name )

  event_handler = 'On' + event_name
  getattr( SERVER_STATE.GetGeneralCompleter(), event_handler )( request_data )

  filetypes = request_data[ 'filetypes' ]
  if SERVER_STATE.FiletypeCompletionUsable( filetypes ):
    getattr( SERVER_STATE.GetFiletypeCompleter( filetypes ),
              event_handler )( request_data )


@app.post( '/run_completer_command' )
def RunCompleterCommand():
  LOGGER.info( 'Received command request')
  request_data = request.json
  completer = _GetCompleterForRequestData( request_data )

  return _JsonResponse( completer.OnUserCommand(
      request_data[ 'command_arguments' ],
      request_data ) )


@app.post( '/get_completions' )
def GetCompletions():
  LOGGER.info( 'Received completion request')
  request_data = request.json
  do_filetype_completion = SERVER_STATE.ShouldUseFiletypeCompleter(
    request_data )
  LOGGER.debug( 'Using filetype completion: %s', do_filetype_completion )
  filetypes = request_data[ 'filetypes' ]
  completer = ( SERVER_STATE.GetFiletypeCompleter( filetypes ) if
                do_filetype_completion else
                SERVER_STATE.GetGeneralCompleter() )

  # This is necessary so that general_completer_store fills up
  # _current_query_completers.
  # TODO: Fix this.
  completer.ShouldUseNow( request_data )

  # TODO: This should not be async anymore, server is multi-threaded
  completer.CandidatesForQueryAsync( request_data )
  while not completer.AsyncCandidateRequestReady():
    time.sleep( 0.03 )
  return _JsonResponse( completer.CandidatesFromStoredRequest() )


@app.get( '/user_options' )
def GetUserOptions():
  LOGGER.info( 'Received user options GET request')
  return _JsonResponse( dict( SERVER_STATE.user_options ) )


@app.post( '/user_options' )
def SetUserOptions():
  LOGGER.info( 'Received user options POST request')
  _SetUserOptions( request.json )


@app.post( '/filetype_completion_available')
def FiletypeCompletionAvailable():
  LOGGER.info( 'Received filetype completion available request')
  return _JsonResponse( SERVER_STATE.FiletypeCompletionAvailable(
      request.json[ 'filetypes' ] ) )


@app.post( '/defined_subcommands')
def DefinedSubcommands():
  LOGGER.info( 'Received defined subcommands request')
  completer = _GetCompleterForRequestData( request.json )

  return _JsonResponse( completer.DefinedSubcommands() )


@app.post( '/debug_info')
def DebugInfo():
  # This can't be at the top level because of possible extra conf preload
  import ycm_core
  LOGGER.info( 'Received debug info request')

  output = []
  has_clang_support = ycm_core.HasClangSupport()
  output.append( 'Server has Clang support compiled in: {0}'.format(
    has_clang_support ) )

  if has_clang_support:
    output.append( ycm_core.ClangVersion() )

  request_data = request.json
  output.append(
      _GetCompleterForRequestData( request_data ).DebugInfo( request_data) )
  return _JsonResponse( '\n'.join( output ) )


# The type of the param is Bottle.HTTPError
@app.error( httplib.INTERNAL_SERVER_ERROR )
def ErrorHandler( httperror ):
  return _JsonResponse( BuildExceptionResponse( str( httperror.exception ),
                                                httperror.traceback ) )


def _JsonResponse( data ):
  response.set_header( 'Content-Type', 'application/json' )
  return json.dumps( data )


def _GetCompleterForRequestData( request_data ):
  completer_target = request_data.get( 'completer_target', None )

  if completer_target == 'identifier':
    return SERVER_STATE.GetGeneralCompleter().GetIdentifierCompleter()
  elif completer_target == 'filetype_default' or not completer_target:
    return SERVER_STATE.GetFiletypeCompleter( request_data[ 'filetypes' ] )
  else:
    return SERVER_STATE.GetFiletypeCompleter( [ completer_target ] )


@atexit.register
def _ServerShutdown():
  if SERVER_STATE:
    SERVER_STATE.Shutdown()


def _SetUserOptions( options ):
  global SERVER_STATE

  user_options_store.SetAll( options )
  SERVER_STATE = server_state.ServerState( options )


def SetServerStateToDefaults():
  global SERVER_STATE, LOGGER
  LOGGER = logging.getLogger( __name__ )
  user_options_store.LoadDefaults()
  SERVER_STATE = server_state.ServerState( user_options_store.GetAll() )


def Main():
  global LOGGER
  parser = argparse.ArgumentParser()
  parser.add_argument( '--host', type = str, default = 'localhost',
                       help = 'server hostname')
  parser.add_argument( '--port', type = int, default = 6666,
                       help = 'server port')
  parser.add_argument( '--log', type = str, default = 'info',
                       help = 'log level, one of '
                              '[debug|info|warning|error|critical]' )
  parser.add_argument( '--options_file', type = str, default = '',
                       help = 'file with user options, in JSON format' )
  args = parser.parse_args()

  if args.options_file:
    _SetUserOptions( json.load( open( args.options_file, 'r' ) ) )

  numeric_level = getattr( logging, args.log.upper(), None )
  if not isinstance( numeric_level, int ):
    raise ValueError( 'Invalid log level: %s' % args.log )

  logging.basicConfig( format = '%(asctime)s - %(levelname)s - %(message)s',
                       level = numeric_level )

  LOGGER = logging.getLogger( __name__ )
  run( app = app, host = args.host, port = args.port, server='cherrypy' )


if __name__ == "__main__":
  Main()


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
import threading

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
import httplib
import json
import bottle
from bottle import run, request, response
import server_state
from ycm import extra_conf_store
from ycm import user_options_store
from ycm import utils
import argparse

# num bytes for the request body buffer; request.json only works if the request
# size is less than this
bottle.Request.MEMFILE_MAX = 300 * 1024

user_options_store.LoadDefaults()
SERVER_STATE = server_state.ServerState( user_options_store.GetAll() )

LOGGER = logging.getLogger( __name__ )
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

  try:
    if hasattr( extra_conf_store, event_handler ):
      getattr( extra_conf_store, event_handler )( request_data )
  except OSError as e:
    LOGGER.exception( e )

  if event_name == 'VimLeave':
    _ScheduleServerShutdown()



@app.post( '/run_completer_command' )
def RunCompleterCommand():
  LOGGER.info( 'Received command request')
  request_data = request.json
  completer_target = request_data[ 'completer_target' ]

  if completer_target == 'identifier':
    completer = SERVER_STATE.GetGeneralCompleter()
  else:
    completer = SERVER_STATE.GetFiletypeCompleter()

  return _JsonResponse(
      completer.OnUserCommand( request_data[ 'command_arguments' ],
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


@app.route( '/user_options' )
def UserOptions():
  global SERVER_STATE

  if request.method == 'GET':
    LOGGER.info( 'Received user options GET request')
    return SERVER_STATE.user_options
  elif request.method == 'POST':
    LOGGER.info( 'Received user options POST request')
    data = request.json
    SERVER_STATE = server_state.ServerState( data )
    user_options_store.SetAll( data )
  else:
    response.status = httplib.BAD_REQUEST


@app.post( '/filetype_completion_available')
def FiletypeCompletionAvailable():
  LOGGER.info( 'Received filetype completion available request')
  return _JsonResponse( SERVER_STATE.FiletypeCompletionAvailable(
      request.json[ 'filetypes' ] ) )


def _JsonResponse( data ):
  response.set_header( 'Content-Type', 'application/json' )
  return json.dumps( data )


def _ScheduleServerShutdown():
  # The reason why we want to schedule a shutdown in the near future instead of
  # just shutting down right now is because we want the current request (the one
  # that made us want to shutdown) to complete successfully first.

  def Shutdown():
    # sys.exit() doesn't work because we're not in the main thread.
    utils.TerminateProcess( os.getpid() )

  killer_thread = threading.Timer( 2, Shutdown )
  killer_thread.start()


def Main():
  global LOGGER
  parser = argparse.ArgumentParser()
  parser.add_argument( '--host', type = str, default = 'localhost',
                       help='server hostname')
  parser.add_argument( '--port', type = int, default = 6666,
                       help='server port')
  parser.add_argument( '--log', type = str, default = 'info',
                       help='log level, one of '
                            '[debug|info|warning|error|critical]')
  args = parser.parse_args()

  numeric_level = getattr( logging, args.log.upper(), None )
  if not isinstance( numeric_level, int ):
    raise ValueError( 'Invalid log level: %s' % args.log )

  logging.basicConfig( format = '%(asctime)s - %(levelname)s - %(message)s',
                       level = numeric_level )

  LOGGER = logging.getLogger( __name__ )
  run( app = app, host = args.host, port = args.port, server='cherrypy' )


if __name__ == "__main__":
  Main()


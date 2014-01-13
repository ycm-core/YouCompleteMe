#!/usr/bin/env python
#
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

from os import path

try:
  import ycm_core
except ImportError as e:
  raise RuntimeError(
    'Error importing ycm_core. Are you sure you have placed a '
    'version 3.2+ libclang.[so|dll|dylib] in folder "{0}"? '
    'See the Installation Guide in the docs. Full error: {1}'.format(
      path.realpath( path.join( path.abspath( __file__ ), '../../..' ) ),
      str( e ) ) )

import atexit
import logging
import json
import bottle
import httplib
from bottle import request, response
import server_state
from ycm import user_options_store
from ycm.server.responses import BuildExceptionResponse
from ycm import extra_conf_store


# num bytes for the request body buffer; request.json only works if the request
# size is less than this
bottle.Request.MEMFILE_MAX = 1000 * 1024

# TODO: rename these to _lower_case
SERVER_STATE = None
LOGGER = logging.getLogger( __name__ )
app = bottle.Bottle()


@app.post( '/event_notification' )
def EventNotification():
  LOGGER.info( 'Received event notification' )
  request_data = request.json
  event_name = request_data[ 'event_name' ]
  LOGGER.debug( 'Event name: %s', event_name )

  event_handler = 'On' + event_name
  getattr( SERVER_STATE.GetGeneralCompleter(), event_handler )( request_data )

  filetypes = request_data[ 'filetypes' ]
  response_data = None
  if SERVER_STATE.FiletypeCompletionUsable( filetypes ):
    response_data = getattr( SERVER_STATE.GetFiletypeCompleter( filetypes ),
                             event_handler )( request_data )

  if response_data:
    return _JsonResponse( response_data )


@app.post( '/run_completer_command' )
def RunCompleterCommand():
  LOGGER.info( 'Received command request' )
  request_data = request.json
  completer = _GetCompleterForRequestData( request_data )

  return _JsonResponse( completer.OnUserCommand(
      request_data[ 'command_arguments' ],
      request_data ) )


@app.post( '/completions' )
def GetCompletions():
  LOGGER.info( 'Received completion request' )
  request_data = request.json
  do_filetype_completion = SERVER_STATE.ShouldUseFiletypeCompleter(
    request_data )
  LOGGER.debug( 'Using filetype completion: %s', do_filetype_completion )
  filetypes = request_data[ 'filetypes' ]
  completer = ( SERVER_STATE.GetFiletypeCompleter( filetypes ) if
                do_filetype_completion else
                SERVER_STATE.GetGeneralCompleter() )

  return _JsonResponse( completer.ComputeCandidates( request_data ) )


@app.get( '/user_options' )
def GetUserOptions():
  LOGGER.info( 'Received user options GET request' )
  return _JsonResponse( dict( SERVER_STATE.user_options ) )


@app.get( '/healthy' )
def GetHealthy():
  LOGGER.info( 'Received health request' )
  return _JsonResponse( True )


@app.post( '/user_options' )
def SetUserOptions():
  LOGGER.info( 'Received user options POST request' )
  UpdateUserOptions( request.json )


@app.post( '/semantic_completion_available' )
def FiletypeCompletionAvailable():
  LOGGER.info( 'Received filetype completion available request' )
  return _JsonResponse( SERVER_STATE.FiletypeCompletionAvailable(
      request.json[ 'filetypes' ] ) )


@app.post( '/defined_subcommands' )
def DefinedSubcommands():
  LOGGER.info( 'Received defined subcommands request' )
  completer = _GetCompleterForRequestData( request.json )

  return _JsonResponse( completer.DefinedSubcommands() )


@app.post( '/detailed_diagnostic' )
def GetDetailedDiagnostic():
  LOGGER.info( 'Received detailed diagnostic request' )
  request_data = request.json
  completer = _GetCompleterForRequestData( request_data )

  return _JsonResponse( completer.GetDetailedDiagnostic( request_data ) )


@app.post( '/load_extra_conf_file' )
def LoadExtraConfFile():
  LOGGER.info( 'Received extra conf load request' )
  request_data = request.json
  extra_conf_store.Load( request_data[ 'filepath' ], force = True )


@app.post( '/ignore_extra_conf_file' )
def IgnoreExtraConfFile():
  LOGGER.info( 'Received extra conf ignore request' )
  request_data = request.json
  extra_conf_store.Disable( request_data[ 'filepath' ] )


@app.post( '/debug_info' )
def DebugInfo():
  LOGGER.info( 'Received debug info request' )

  output = []
  has_clang_support = ycm_core.HasClangSupport()
  output.append( 'Server has Clang support compiled in: {0}'.format(
    has_clang_support ) )

  if has_clang_support:
    output.append( 'Clang version: ' + ycm_core.ClangVersion() )

  request_data = request.json
  try:
    output.append(
        _GetCompleterForRequestData( request_data ).DebugInfo( request_data) )
  except:
    pass
  return _JsonResponse( '\n'.join( output ) )


# The type of the param is Bottle.HTTPError
@app.error( httplib.INTERNAL_SERVER_ERROR )
def ErrorHandler( httperror ):
  return _JsonResponse( BuildExceptionResponse( httperror.exception,
                                                httperror.traceback ) )


def _JsonResponse( data ):
  response.set_header( 'Content-Type', 'application/json' )
  return json.dumps( data, default = _UniversalSerialize )


def _UniversalSerialize( obj ):
  serialized = obj.__dict__.copy()
  serialized[ 'TYPE' ] = type( obj ).__name__
  return serialized


def _GetCompleterForRequestData( request_data ):
  completer_target = request_data.get( 'completer_target', None )

  if completer_target == 'identifier':
    return SERVER_STATE.GetGeneralCompleter().GetIdentifierCompleter()
  elif completer_target == 'filetype_default' or not completer_target:
    return SERVER_STATE.GetFiletypeCompleter( request_data[ 'filetypes' ] )
  else:
    return SERVER_STATE.GetFiletypeCompleter( [ completer_target ] )


@atexit.register
def ServerShutdown():
  LOGGER.info( 'Server shutting down' )
  if SERVER_STATE:
    SERVER_STATE.Shutdown()
    extra_conf_store.Shutdown()


def UpdateUserOptions( options ):
  global SERVER_STATE

  if not options:
    return

  user_options_store.SetAll( options )
  SERVER_STATE = server_state.ServerState( options )


def SetServerStateToDefaults():
  global SERVER_STATE, LOGGER
  LOGGER = logging.getLogger( __name__ )
  user_options_store.LoadDefaults()
  SERVER_STATE = server_state.ServerState( user_options_store.GetAll() )
  extra_conf_store.Reset()

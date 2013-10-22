#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Strahinja Val Markovic  <val@markovic.io>
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
import vim
import subprocess
import tempfile
import json
from ycm import vimsupport
from ycm import utils
from ycm.completers.all.omni_completer import OmniCompleter
from ycm.completers.general import syntax_parse
from ycm.completers.completer_utils import FiletypeCompleterExistsForFiletype
from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm.client.command_request import SendCommandRequest
from ycm.client.completion_request import CompletionRequest
from ycm.client.omni_completion_request import OmniCompletionRequest
from ycm.client.event_notification import ( SendEventNotificationAsync,
                                            EventNotification )
from ycm.server.responses import ServerError

try:
  from UltiSnips import UltiSnips_Manager
  USE_ULTISNIPS_DATA = True
except ImportError:
  USE_ULTISNIPS_DATA = False

SERVER_CRASH_MESSAGE_STDERR_FILE = 'The ycmd server crashed with output:\n'
SERVER_CRASH_MESSAGE_SAME_STDERR = (
  'The ycmd server crashed, check console output for logs!' )


class YouCompleteMe( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    self._omnicomp = OmniCompleter( user_options )
    self._latest_completion_request = None
    self._latest_file_parse_request = None
    self._server_stdout = None
    self._server_stderr = None
    self._server_popen = None
    self._filetypes_with_keywords_loaded = set()
    self._temp_options_filename = None
    self._SetupServer()


  def _SetupServer( self ):
    server_port = utils.GetUnusedLocalhostPort()
    with tempfile.NamedTemporaryFile( delete = False ) as options_file:
      self._temp_options_filename = options_file.name
      json.dump( dict( self._user_options ), options_file )
      args = [ utils.PathToPythonInterpreter(),
               _PathToServerScript(),
               '--port={0}'.format( server_port ),
               '--options_file={0}'.format( options_file.name ),
               '--log={0}'.format( self._user_options[ 'server_log_level' ] ) ]

      BaseRequest.server_location = 'http://localhost:' + str( server_port )

      if self._user_options[ 'server_use_vim_stdout' ]:
        self._server_popen = subprocess.Popen( args )
      else:
        filename_format = os.path.join( utils.PathToTempDir(),
                                        'server_{port}_{std}.log' )

        self._server_stdout = filename_format.format( port = server_port,
                                                      std = 'stdout' )
        self._server_stderr = filename_format.format( port = server_port,
                                                      std = 'stderr' )

        with open( self._server_stderr, 'w' ) as fstderr:
          with open( self._server_stdout, 'w' ) as fstdout:
            self._server_popen = subprocess.Popen( args,
                                                   stdout = fstdout,
                                                   stderr = fstderr )
    self._NotifyUserIfServerCrashed()


  def _IsServerAlive( self ):
    returncode = self._server_popen.poll()
    # When the process hasn't finished yet, poll() returns None.
    return returncode is None


  def _NotifyUserIfServerCrashed( self ):
    if self._IsServerAlive():
      return
    if self._server_stderr:
      with open( self._server_stderr, 'r' ) as server_stderr_file:
        vimsupport.PostMultiLineNotice( SERVER_CRASH_MESSAGE_STDERR_FILE +
                                        server_stderr_file.read() )
    else:
        vimsupport.PostVimMessage( SERVER_CRASH_MESSAGE_SAME_STDERR )


  def ServerPid( self ):
    if not self._server_popen:
      return -1
    return self._server_popen.pid


  def RestartServer( self ):
    vimsupport.PostVimMessage( 'Restarting ycmd server...' )
    self.OnVimLeave()
    self._SetupServer()


  def CreateCompletionRequest( self, force_semantic = False ):
    # We have to store a reference to the newly created CompletionRequest
    # because VimScript can't store a reference to a Python object across
    # function calls... Thus we need to keep this request somewhere.
    if ( not self.NativeFiletypeCompletionAvailable() and
         self.CurrentFiletypeCompletionEnabled() and
         self._omnicomp.ShouldUseNow() ):
      self._latest_completion_request = OmniCompletionRequest( self._omnicomp )
    else:
      self._latest_completion_request = ( CompletionRequest( force_semantic )
                                          if self._IsServerAlive() else
                                          None )
    return self._latest_completion_request


  def SendCommandRequest( self, arguments, completer ):
    if self._IsServerAlive():
      return SendCommandRequest( arguments, completer )


  def GetDefinedSubcommands( self ):
    if self._IsServerAlive():
      return BaseRequest.PostDataToHandler( BuildRequestData(),
                                            'defined_subcommands' )
    else:
      return []


  def GetCurrentCompletionRequest( self ):
    return self._latest_completion_request


  def GetOmniCompleter( self ):
    return self._omnicomp


  def NativeFiletypeCompletionAvailable( self ):
    return any( [ FiletypeCompleterExistsForFiletype( x ) for x in
                  vimsupport.CurrentFiletypes() ] )


  def NativeFiletypeCompletionUsable( self ):
    return ( self.CurrentFiletypeCompletionEnabled() and
             self.NativeFiletypeCompletionAvailable() )


  def OnFileReadyToParse( self ):
    self._omnicomp.OnFileReadyToParse( None )

    if not self._IsServerAlive():
      self._NotifyUserIfServerCrashed()

    extra_data = {}
    if self._user_options[ 'collect_identifiers_from_tags_files' ]:
      extra_data[ 'tag_files' ] = _GetTagFiles()

    if self._user_options[ 'seed_identifiers_with_syntax' ]:
      self._AddSyntaxDataIfNeeded( extra_data )

    self._latest_file_parse_request = EventNotification( 'FileReadyToParse',
                                                          extra_data )
    self._latest_file_parse_request.Start()


  def OnBufferUnload( self, deleted_buffer_file ):
    if not self._IsServerAlive():
      return
    SendEventNotificationAsync( 'BufferUnload',
                                { 'unloaded_buffer': deleted_buffer_file } )


  def OnBufferVisit( self ):
    if not self._IsServerAlive():
      return
    extra_data = {}
    _AddUltiSnipsDataIfNeeded( extra_data )
    SendEventNotificationAsync( 'BufferVisit', extra_data )


  def OnInsertLeave( self ):
    if not self._IsServerAlive():
      return
    SendEventNotificationAsync( 'InsertLeave' )


  def OnVimLeave( self ):
    if self._IsServerAlive():
      self._server_popen.terminate()
    os.remove( self._temp_options_filename )

    if not self._user_options[ 'server_keep_logfiles' ]:
      if self._server_stderr:
        os.remove( self._server_stderr )
      if self._server_stdout:
        os.remove( self._server_stdout )


  def OnCurrentIdentifierFinished( self ):
    if not self._IsServerAlive():
      return
    SendEventNotificationAsync( 'CurrentIdentifierFinished' )


  def DiagnosticsForCurrentFileReady( self ):
    return bool( self._latest_file_parse_request and
                 self._latest_file_parse_request.Done() )


  def GetDiagnosticsFromStoredRequest( self ):
    if self.DiagnosticsForCurrentFileReady():
      to_return = self._latest_file_parse_request.Response()
      # We set the diagnostics request to None because we want to prevent
      # Syntastic from repeatedly refreshing the buffer with the same diags.
      # Setting this to None makes DiagnosticsForCurrentFileReady return False
      # until the next request is created.
      self._latest_file_parse_request = None
      return to_return
    return []


  def ShowDetailedDiagnostic( self ):
    if not self._IsServerAlive():
      return
    try:
      debug_info = BaseRequest.PostDataToHandler( BuildRequestData(),
                                                  'detailed_diagnostic' )
      if 'message' in debug_info:
        vimsupport.EchoText( debug_info[ 'message' ] )
    except ServerError as e:
      vimsupport.PostVimMessage( str( e ) )


  def DebugInfo( self ):
    if self._IsServerAlive():
      debug_info = BaseRequest.PostDataToHandler( BuildRequestData(),
                                                  'debug_info' )
    else:
      debug_info = 'Server crashed, no debug info from server'
    debug_info += '\nServer running at: {0}'.format(
        BaseRequest.server_location )
    debug_info += '\nServer process ID: {0}'.format( self._server_popen.pid )
    if self._server_stderr or self._server_stdout:
      debug_info += '\nServer logfiles:\n  {0}\n  {1}'.format(
        self._server_stdout,
        self._server_stderr )

    return debug_info


  def CurrentFiletypeCompletionEnabled( self ):
    filetypes = vimsupport.CurrentFiletypes()
    filetype_to_disable = self._user_options[
      'filetype_specific_completion_to_disable' ]
    return not all([ x in filetype_to_disable for x in filetypes ])


  def _AddSyntaxDataIfNeeded( self, extra_data ):
    filetype = vimsupport.CurrentFiletypes()[ 0 ]
    if filetype in self._filetypes_with_keywords_loaded:
      return

    self._filetypes_with_keywords_loaded.add( filetype )
    extra_data[ 'syntax_keywords' ] = list(
       syntax_parse.SyntaxKeywordsForCurrentBuffer() )


def _GetTagFiles():
  tag_files = vim.eval( 'tagfiles()' )
  current_working_directory = os.getcwd()
  return [ os.path.join( current_working_directory, x ) for x in tag_files ]


def _PathToServerScript():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'server/ycmd.py' )


def _AddUltiSnipsDataIfNeeded( extra_data ):
  if not USE_ULTISNIPS_DATA:
    return

  try:
    rawsnips = UltiSnips_Manager._snips( '', 1 )
  except:
    return

  # UltiSnips_Manager._snips() returns a class instance where:
  # class.trigger - name of snippet trigger word ( e.g. defn or testcase )
  # class.description - description of the snippet
  extra_data[ 'ultisnips_snippets' ] = [ { 'trigger': x.trigger,
                                           'description': x.description
                                         } for x in rawsnips ]

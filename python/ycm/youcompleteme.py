#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Google Inc.
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
import tempfile
import json
import signal
import base64
from subprocess import PIPE
from ycm import vimsupport
from ycmd import utils
from ycmd.request_wrap import RequestWrap
from ycm.diagnostic_interface import DiagnosticInterface
from ycm.omni_completer import OmniCompleter
from ycm import syntax_parse
from ycmd.completers.completer_utils import FiletypeCompleterExistsForFiletype
from ycm.client.ycmd_keepalive import YcmdKeepalive
from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm.client.command_request import SendCommandRequest
from ycm.client.completion_request import CompletionRequest
from ycm.client.omni_completion_request import OmniCompletionRequest
from ycm.client.event_notification import ( SendEventNotificationAsync,
                                            EventNotification )
from ycmd.responses import ServerError

try:
  from UltiSnips import UltiSnips_Manager
  USE_ULTISNIPS_DATA = True
except ImportError:
  USE_ULTISNIPS_DATA = False

# We need this so that Requests doesn't end up using the local HTTP proxy when
# talking to ycmd. Users should actually be setting this themselves when
# configuring a proxy server on their machine, but most don't know they need to
# or how to do it, so we do it for them.
# Relevant issues:
#  https://github.com/Valloric/YouCompleteMe/issues/641
#  https://github.com/kennethreitz/requests/issues/879
os.environ['no_proxy'] = '127.0.0.1,localhost'

# Force the Python interpreter embedded in Vim (in which we are running) to
# ignore the SIGINT signal. This helps reduce the fallout of a user pressing
# Ctrl-C in Vim.
signal.signal( signal.SIGINT, signal.SIG_IGN )

HMAC_SECRET_LENGTH = 16
NUM_YCMD_STDERR_LINES_ON_CRASH = 30
SERVER_CRASH_MESSAGE_STDERR_FILE_DELETED = (
  'The ycmd server SHUT DOWN (restart with :YcmRestartServer). '
  'Logfile was deleted; set g:ycm_server_keep_logfiles to see errors '
  'in the future.' )
SERVER_CRASH_MESSAGE_STDERR_FILE = (
  'The ycmd server SHUT DOWN (restart with :YcmRestartServer). ' +
  'Stderr (last {0} lines):\n\n'.format( NUM_YCMD_STDERR_LINES_ON_CRASH ) )
SERVER_CRASH_MESSAGE_SAME_STDERR = (
  'The ycmd server SHUT DOWN (restart with :YcmRestartServer). '
  ' check console output for logs!' )
SERVER_IDLE_SUICIDE_SECONDS = 10800  # 3 hours


class YouCompleteMe( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    self._user_notified_about_crash = False
    self._diag_interface = DiagnosticInterface( user_options )
    self._omnicomp = OmniCompleter( user_options )
    self._latest_file_parse_request = None
    self._latest_completion_request = None
    self._server_stdout = None
    self._server_stderr = None
    self._server_popen = None
    self._filetypes_with_keywords_loaded = set()
    self._ycmd_keepalive = YcmdKeepalive()
    self._SetupServer()
    self._ycmd_keepalive.Start()

  def _SetupServer( self ):
    server_port = utils.GetUnusedLocalhostPort()
    # The temp options file is deleted by ycmd during startup
    with tempfile.NamedTemporaryFile( delete = False ) as options_file:
      hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
      options_dict = dict( self._user_options )
      options_dict[ 'hmac_secret' ] = base64.b64encode( hmac_secret )
      json.dump( options_dict, options_file )
      options_file.flush()

      args = [ utils.PathToPythonInterpreter(),
               _PathToServerScript(),
               '--port={0}'.format( server_port ),
               '--options_file={0}'.format( options_file.name ),
               '--log={0}'.format( self._user_options[ 'server_log_level' ] ),
               '--idle_suicide_seconds={0}'.format(
                  SERVER_IDLE_SUICIDE_SECONDS )]

      if not self._user_options[ 'server_use_vim_stdout' ]:
        filename_format = os.path.join( utils.PathToTempDir(),
                                        'server_{port}_{std}.log' )

        self._server_stdout = filename_format.format( port = server_port,
                                                      std = 'stdout' )
        self._server_stderr = filename_format.format( port = server_port,
                                                      std = 'stderr' )
        args.append('--stdout={0}'.format( self._server_stdout ))
        args.append('--stderr={0}'.format( self._server_stderr ))

        if self._user_options[ 'server_keep_logfiles' ]:
          args.append('--keep_logfiles')

      self._server_popen = utils.SafePopen( args, stdout = PIPE, stderr = PIPE)
      BaseRequest.server_location = 'http://127.0.0.1:' + str( server_port )
      BaseRequest.hmac_secret = hmac_secret

    self._NotifyUserIfServerCrashed()

  def IsServerAlive( self ):
    returncode = self._server_popen.poll()
    # When the process hasn't finished yet, poll() returns None.
    return returncode is None


  def _NotifyUserIfServerCrashed( self ):
    if self._user_notified_about_crash or self.IsServerAlive():
      return
    self._user_notified_about_crash = True
    if self._server_stderr:
      try:
        with open( self._server_stderr, 'r' ) as server_stderr_file:
          error_output = ''.join( server_stderr_file.readlines()[
              : - NUM_YCMD_STDERR_LINES_ON_CRASH ] )
          vimsupport.PostMultiLineNotice( SERVER_CRASH_MESSAGE_STDERR_FILE +
                                          error_output )
      except IOError:
        vimsupport.PostVimMessage( SERVER_CRASH_MESSAGE_STDERR_FILE_DELETED )
    else:
        vimsupport.PostVimMessage( SERVER_CRASH_MESSAGE_SAME_STDERR )


  def ServerPid( self ):
    if not self._server_popen:
      return -1
    return self._server_popen.pid


  def _ServerCleanup( self ):
    if self.IsServerAlive():
      self._server_popen.terminate()


  def RestartServer( self ):
    vimsupport.PostVimMessage( 'Restarting ycmd server...' )
    self._user_notified_about_crash = False
    self._ServerCleanup()
    self._SetupServer()


  def CreateCompletionRequest( self, force_semantic = False ):
    request_data = BuildRequestData()
    if ( not self.NativeFiletypeCompletionAvailable() and
         self.CurrentFiletypeCompletionEnabled() ):
      wrapped_request_data = RequestWrap( request_data )
      if self._omnicomp.ShouldUseNow( wrapped_request_data ):
        self._latest_completion_request = OmniCompletionRequest(
            self._omnicomp, wrapped_request_data )
        return self._latest_completion_request

    self._AddExtraConfDataIfNeeded( request_data )
    if force_semantic:
      request_data[ 'force_semantic' ] = True
    self._latest_completion_request = CompletionRequest( request_data )
    return self._latest_completion_request


  def SendCommandRequest( self, arguments, completer ):
    if self.IsServerAlive():
      return SendCommandRequest( arguments, completer )


  def GetDefinedSubcommands( self ):
    if self.IsServerAlive():
      try:
        return BaseRequest.PostDataToHandler( BuildRequestData(),
                                             'defined_subcommands' )
      except ServerError:
        return []
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

    if not self.IsServerAlive():
      self._NotifyUserIfServerCrashed()

    extra_data = {}
    self._AddTagsFilesIfNeeded( extra_data )
    self._AddSyntaxDataIfNeeded( extra_data )
    self._AddExtraConfDataIfNeeded( extra_data )

    self._latest_file_parse_request = EventNotification( 'FileReadyToParse',
                                                          extra_data )
    self._latest_file_parse_request.Start()


  def OnBufferUnload( self, deleted_buffer_file ):
    if not self.IsServerAlive():
      return
    SendEventNotificationAsync( 'BufferUnload',
                                { 'unloaded_buffer': deleted_buffer_file } )


  def OnBufferVisit( self ):
    if not self.IsServerAlive():
      return
    extra_data = {}
    _AddUltiSnipsDataIfNeeded( extra_data )
    SendEventNotificationAsync( 'BufferVisit', extra_data )


  def OnInsertLeave( self ):
    if not self.IsServerAlive():
      return
    SendEventNotificationAsync( 'InsertLeave' )


  def OnCursorMoved( self ):
    self._diag_interface.OnCursorMoved()


  def OnVimLeave( self ):
    self._ServerCleanup()


  def OnCurrentIdentifierFinished( self ):
    if not self.IsServerAlive():
      return
    SendEventNotificationAsync( 'CurrentIdentifierFinished' )


  def DiagnosticsForCurrentFileReady( self ):
    return bool( self._latest_file_parse_request and
                 self._latest_file_parse_request.Done() )


  def GetDiagnosticsFromStoredRequest( self, qflist_format = False ):
    if self.DiagnosticsForCurrentFileReady():
      diagnostics = self._latest_file_parse_request.Response()
      # We set the diagnostics request to None because we want to prevent
      # Syntastic from repeatedly refreshing the buffer with the same diags.
      # Setting this to None makes DiagnosticsForCurrentFileReady return False
      # until the next request is created.
      self._latest_file_parse_request = None
      if qflist_format:
        return vimsupport.ConvertDiagnosticsToQfList( diagnostics )
      else:
        return diagnostics
    return []


  def UpdateDiagnosticInterface( self ):
    if not self.DiagnosticsForCurrentFileReady():
      return
    self._diag_interface.UpdateWithNewDiagnostics(
      self.GetDiagnosticsFromStoredRequest() )


  def ShowDetailedDiagnostic( self ):
    if not self.IsServerAlive():
      return
    try:
      debug_info = BaseRequest.PostDataToHandler( BuildRequestData(),
                                                  'detailed_diagnostic' )
      if 'message' in debug_info:
        vimsupport.EchoText( debug_info[ 'message' ] )
    except ServerError as e:
      vimsupport.PostVimMessage( str( e ) )


  def DebugInfo( self ):
    if self.IsServerAlive():
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
    if '*' in filetype_to_disable:
      return False
    else:
      return not all([ x in filetype_to_disable for x in filetypes ])


  def _AddSyntaxDataIfNeeded( self, extra_data ):
    if not self._user_options[ 'seed_identifiers_with_syntax' ]:
      return
    filetype = vimsupport.CurrentFiletypes()[ 0 ]
    if filetype in self._filetypes_with_keywords_loaded:
      return

    self._filetypes_with_keywords_loaded.add( filetype )
    extra_data[ 'syntax_keywords' ] = list(
       syntax_parse.SyntaxKeywordsForCurrentBuffer() )


  def _AddTagsFilesIfNeeded( self, extra_data ):
    def GetTagFiles():
      tag_files = vim.eval( 'tagfiles()' )
      current_working_directory = os.getcwd()
      return [ os.path.join( current_working_directory, x ) for x in tag_files ]

    if not self._user_options[ 'collect_identifiers_from_tags_files' ]:
      return
    extra_data[ 'tag_files' ] = GetTagFiles()


  def _AddExtraConfDataIfNeeded( self, extra_data ):
    def BuildExtraConfData( extra_conf_vim_data ):
      return dict( ( expr, vimsupport.VimExpressionToPythonType( expr ) )
                   for expr in extra_conf_vim_data )

    extra_conf_vim_data = self._user_options[ 'extra_conf_vim_data' ]
    if extra_conf_vim_data:
      extra_data[ 'extra_conf_data' ] = BuildExtraConfData(
        extra_conf_vim_data )


def _PathToServerScript():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, '../../third_party/ycmd/ycmd' )


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



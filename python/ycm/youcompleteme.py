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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from future.utils import iteritems
import os
import vim
import json
import re
import signal
import base64
from subprocess import PIPE
from tempfile import NamedTemporaryFile
from requests.exceptions import Timeout
from ycm import base, paths, vimsupport
from ycmd import utils
from ycmd import server_utils
from ycmd.request_wrap import RequestWrap
from ycmd.responses import ServerError
from ycm.diagnostic_interface import DiagnosticInterface
from ycm.omni_completer import OmniCompleter
from ycm import syntax_parse
from ycm.client.ycmd_keepalive import YcmdKeepalive
from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm.client.completer_available_request import SendCompleterAvailableRequest
from ycm.client.command_request import SendCommandRequest
from ycm.client.completion_request import ( CompletionRequest,
                                            ConvertCompletionDataToVimData )
from ycm.client.omni_completion_request import OmniCompletionRequest
from ycm.client.event_notification import ( SendEventNotificationAsync,
                                            EventNotification )
from ycm.client.shutdown_request import SendShutdownRequest


def PatchNoProxy():
  current_value = os.environ.get('no_proxy', '')
  additions = '127.0.0.1,localhost'
  os.environ['no_proxy'] = ( additions if not current_value
                             else current_value + ',' + additions )

# We need this so that Requests doesn't end up using the local HTTP proxy when
# talking to ycmd. Users should actually be setting this themselves when
# configuring a proxy server on their machine, but most don't know they need to
# or how to do it, so we do it for them.
# Relevant issues:
#  https://github.com/Valloric/YouCompleteMe/issues/641
#  https://github.com/kennethreitz/requests/issues/879
PatchNoProxy()

# Force the Python interpreter embedded in Vim (in which we are running) to
# ignore the SIGINT signal. This helps reduce the fallout of a user pressing
# Ctrl-C in Vim.
signal.signal( signal.SIGINT, signal.SIG_IGN )

HMAC_SECRET_LENGTH = 16
SERVER_SHUTDOWN_MESSAGE = (
  "The ycmd server SHUT DOWN (restart with ':YcmRestartServer')." )
STDERR_FILE_MESSAGE = (
  "Run ':YcmToggleLogs stderr' to check the logs." )
STDERR_FILE_DELETED_MESSAGE = (
  "Logfile was deleted; set 'g:ycm_server_keep_logfiles' to see errors "
  "in the future." )
CORE_UNEXPECTED_MESSAGE = (
  'Unexpected error while loading the YCM core library.' )
CORE_MISSING_MESSAGE = (
  'YCM core library not detected; you need to compile YCM before using it. '
  'Follow the instructions in the documentation.' )
CORE_PYTHON2_MESSAGE = (
  "YCM core library compiled for Python 2 but loaded in Python 3. "
  "Set the 'g:ycm_server_python_interpreter' option to a Python 2 "
  "interpreter path." )
CORE_PYTHON3_MESSAGE = (
  "YCM core library compiled for Python 3 but loaded in Python 2. "
  "Set the 'g:ycm_server_python_interpreter' option to a Python 3 "
  "interpreter path." )
CORE_OUTDATED_MESSAGE = (
  'YCM core library too old; PLEASE RECOMPILE by running the install.py '
  'script. See the documentation for more details.' )
SERVER_IDLE_SUICIDE_SECONDS = 10800  # 3 hours
DIAGNOSTIC_UI_FILETYPES = set( [ 'cpp', 'cs', 'c', 'objc', 'objcpp' ] )


class YouCompleteMe( object ):
  def __init__( self, user_options ):
    self._available_completers = {}
    self._user_options = user_options
    self._user_notified_about_crash = False
    self._diag_interface = DiagnosticInterface( user_options )
    self._omnicomp = OmniCompleter( user_options )
    self._latest_file_parse_request = None
    self._latest_file_parse_request_bufnr = 0
    self._latest_completion_request = None
    self._latest_diagnostics = []
    self._server_stdout = None
    self._server_stderr = None
    self._server_popen = None
    self._filetypes_with_keywords_loaded = set()
    self._ycmd_keepalive = YcmdKeepalive()
    self._SetupServer()
    self._ycmd_keepalive.Start()
    self._complete_done_hooks = {
      'cs': lambda self: self._OnCompleteDone_Csharp()
    }
    self._file_parse_ready_callbacks = []

  def _SetupServer( self ):
    self._available_completers = {}
    self._user_notified_about_crash = False
    server_port = utils.GetUnusedLocalhostPort()
    # The temp options file is deleted by ycmd during startup
    with NamedTemporaryFile( delete = False, mode = 'w+' ) as options_file:
      hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
      options_dict = dict( self._user_options )
      options_dict[ 'hmac_secret' ] = utils.ToUnicode(
        base64.b64encode( hmac_secret ) )
      json.dump( options_dict, options_file )
      options_file.flush()

      args = [ paths.PathToPythonInterpreter(),
               paths.PathToServerScript(),
               '--port={0}'.format( server_port ),
               '--options_file={0}'.format( options_file.name ),
               '--log={0}'.format( self._user_options[ 'server_log_level' ] ),
               '--idle_suicide_seconds={0}'.format(
                  SERVER_IDLE_SUICIDE_SECONDS ) ]

      filename_format = os.path.join( utils.PathToCreatedTempDir(),
                                      'server_{port}_{std}.log' )

      self._server_stdout = filename_format.format( port = server_port,
                                                    std = 'stdout' )
      self._server_stderr = filename_format.format( port = server_port,
                                                    std = 'stderr' )
      args.append( '--stdout={0}'.format( self._server_stdout ) )
      args.append( '--stderr={0}'.format( self._server_stderr ) )

      if self._user_options[ 'server_keep_logfiles' ]:
        args.append( '--keep_logfiles' )

      self._server_popen = utils.SafePopen( args, stdin_windows = PIPE,
                                            stdout = PIPE, stderr = PIPE )
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

    try:
      vimsupport.CheckFilename( self._server_stderr )
      stderr_message = STDERR_FILE_MESSAGE
    except RuntimeError:
      stderr_message = STDERR_FILE_DELETED_MESSAGE

    message = SERVER_SHUTDOWN_MESSAGE
    return_code = self._server_popen.poll()
    if return_code == server_utils.CORE_UNEXPECTED_STATUS:
      message += ' ' + CORE_UNEXPECTED_MESSAGE + ' ' + stderr_message
    elif return_code == server_utils.CORE_MISSING_STATUS:
      message += ' ' + CORE_MISSING_MESSAGE
    elif return_code == server_utils.CORE_PYTHON2_STATUS:
      message += ' ' + CORE_PYTHON2_MESSAGE
    elif return_code == server_utils.CORE_PYTHON3_STATUS:
      message += ' ' + CORE_PYTHON3_MESSAGE
    elif return_code == server_utils.CORE_OUTDATED_STATUS:
      message += ' ' + CORE_OUTDATED_MESSAGE
    else:
      message += ' ' + stderr_message
    vimsupport.PostVimMessage( message )


  def ServerPid( self ):
    if not self._server_popen:
      return -1
    return self._server_popen.pid


  def _ShutdownServer( self ):
    if self.IsServerAlive():
      SendShutdownRequest()


  def RestartServer( self ):
    self._CloseLogs()
    vimsupport.PostVimMessage( 'Restarting ycmd server...' )
    self._ShutdownServer()
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

    request_data[ 'working_dir' ] = os.getcwd()

    self._AddExtraConfDataIfNeeded( request_data )
    if force_semantic:
      request_data[ 'force_semantic' ] = True
    self._latest_completion_request = CompletionRequest( request_data )
    return self._latest_completion_request


  def GetCompletions( self ):
    request = self.GetCurrentCompletionRequest()
    request.Start()
    while not request.Done():
      try:
        if vimsupport.GetBoolValue( 'complete_check()' ):
          return { 'words' : [], 'refresh' : 'always' }
      except KeyboardInterrupt:
        return { 'words' : [], 'refresh' : 'always' }

    results = base.AdjustCandidateInsertionText( request.Response() )
    return { 'words' : results, 'refresh' : 'always' }


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


  def FiletypeCompleterExistsForFiletype( self, filetype ):
    try:
      return self._available_completers[ filetype ]
    except KeyError:
      pass

    if not self.IsServerAlive():
      return False

    exists_completer = SendCompleterAvailableRequest( filetype )
    if exists_completer is None:
      return False

    self._available_completers[ filetype ] = exists_completer
    return exists_completer


  def NativeFiletypeCompletionAvailable( self ):
    return any( [ self.FiletypeCompleterExistsForFiletype( x ) for x in
                  vimsupport.CurrentFiletypes() ] )


  def NativeFiletypeCompletionUsable( self ):
    return ( self.CurrentFiletypeCompletionEnabled() and
             self.NativeFiletypeCompletionAvailable() )


  def OnFileReadyToParse( self ):
    if not self.IsServerAlive():
      self._NotifyUserIfServerCrashed()
      return

    self._omnicomp.OnFileReadyToParse( None )

    extra_data = {}
    self._AddTagsFilesIfNeeded( extra_data )
    self._AddSyntaxDataIfNeeded( extra_data )
    self._AddExtraConfDataIfNeeded( extra_data )

    self._latest_file_parse_request_bufnr = vimsupport.GetCurrentBufferNumber()
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
    self._AddUltiSnipsDataIfNeeded( extra_data )
    SendEventNotificationAsync( 'BufferVisit', extra_data )


  def OnInsertLeave( self ):
    if not self.IsServerAlive():
      return
    SendEventNotificationAsync( 'InsertLeave' )


  def OnCursorMoved( self ):
    self._diag_interface.OnCursorMoved()


  def OnVimLeave( self ):
    self._ShutdownServer()


  def OnCurrentIdentifierFinished( self ):
    if not self.IsServerAlive():
      return
    SendEventNotificationAsync( 'CurrentIdentifierFinished' )


  def OnCompleteDone( self ):
    complete_done_actions = self.GetCompleteDoneHooks()
    for action in complete_done_actions:
      action(self)


  def GetCompleteDoneHooks( self ):
    filetypes = vimsupport.CurrentFiletypes()
    for key, value in iteritems( self._complete_done_hooks ):
      if key in filetypes:
        yield value


  def GetCompletionsUserMayHaveCompleted( self ):
    latest_completion_request = self.GetCurrentCompletionRequest()
    if not latest_completion_request or not latest_completion_request.Done():
      return []

    completions = latest_completion_request.RawResponse()

    result = self._FilterToMatchingCompletions( completions, True )
    result = list( result )
    if result:
      return result

    if self._HasCompletionsThatCouldBeCompletedWithMoreText( completions ):
      # Since the way that YCM works leads to CompleteDone called on every
      # character, return blank if the completion might not be done. This won't
      # match if the completion is ended with typing a non-keyword character.
      return []

    result = self._FilterToMatchingCompletions( completions, False )

    return list( result )


  def _FilterToMatchingCompletions( self, completions, full_match_only ):
    self._PatchBasedOnVimVersion()
    return self._FilterToMatchingCompletions( completions, full_match_only)


  def _HasCompletionsThatCouldBeCompletedWithMoreText( self, completions ):
    self._PatchBasedOnVimVersion()
    return self._HasCompletionsThatCouldBeCompletedWithMoreText( completions )


  def _PatchBasedOnVimVersion( self ):
    if vimsupport.VimVersionAtLeast( "7.4.774" ):
      self._HasCompletionsThatCouldBeCompletedWithMoreText = \
        self._HasCompletionsThatCouldBeCompletedWithMoreText_NewerVim
      self._FilterToMatchingCompletions = \
        self._FilterToMatchingCompletions_NewerVim
    else:
      self._FilterToMatchingCompletions = \
        self._FilterToMatchingCompletions_OlderVim
      self._HasCompletionsThatCouldBeCompletedWithMoreText = \
        self._HasCompletionsThatCouldBeCompletedWithMoreText_OlderVim


  def _FilterToMatchingCompletions_NewerVim( self,
                                             completions,
                                             full_match_only ):
    """Filter to completions matching the item Vim said was completed"""
    completed = vimsupport.GetVariableValue( 'v:completed_item' )
    for completion in completions:
      item = ConvertCompletionDataToVimData( completion )
      match_keys = ( [ "word", "abbr", "menu", "info" ] if full_match_only
                      else [ 'word' ] )

      def matcher( key ):
        return ( utils.ToUnicode( completed.get( key, "" ) ) ==
                 utils.ToUnicode( item.get( key, "" ) ) )

      if all( [ matcher( i ) for i in match_keys ] ):
        yield completion


  def _FilterToMatchingCompletions_OlderVim( self, completions,
                                             full_match_only ):
    """ Filter to completions matching the buffer text """
    if full_match_only:
      return # Only supported in 7.4.774+
    # No support for multiple line completions
    text = vimsupport.TextBeforeCursor()
    for completion in completions:
      word = completion[ "insertion_text" ]
      # Trim complete-ending character if needed
      text = re.sub( r"[^a-zA-Z0-9_]$", "", text )
      buffer_text = text[ -1 * len( word ) : ]
      if buffer_text == word:
        yield completion


  def _HasCompletionsThatCouldBeCompletedWithMoreText_NewerVim( self,
                                                                completions ):
    completed_item = vimsupport.GetVariableValue( 'v:completed_item' )
    if not completed_item:
      return False

    completed_word = utils.ToUnicode( completed_item[ 'word' ] )
    if not completed_word:
      return False

    # Sometimes CompleteDone is called after the next character is inserted.
    # If so, use inserted character to filter possible completions further.
    text = vimsupport.TextBeforeCursor()
    reject_exact_match = True
    if text and text[ -1 ] != completed_word[ -1 ]:
      reject_exact_match = False
      completed_word += text[ -1 ]

    for completion in completions:
      word = utils.ToUnicode(
          ConvertCompletionDataToVimData( completion )[ 'word' ] )
      if reject_exact_match and word == completed_word:
        continue
      if word.startswith( completed_word ):
        return True
    return False


  def _HasCompletionsThatCouldBeCompletedWithMoreText_OlderVim( self,
                                                                completions ):
    # No support for multiple line completions
    text = vimsupport.TextBeforeCursor()
    for completion in completions:
      word = utils.ToUnicode(
          ConvertCompletionDataToVimData( completion )[ 'word' ] )
      for i in range( 1, len( word ) - 1 ): # Excluding full word
        if text[ -1 * i : ] == word[ : i ]:
          return True
    return False


  def _OnCompleteDone_Csharp( self ):
    completions = self.GetCompletionsUserMayHaveCompleted()
    namespaces = [ self._GetRequiredNamespaceImport( c )
                   for c in completions ]
    namespaces = [ n for n in namespaces if n ]
    if not namespaces:
      return

    if len( namespaces ) > 1:
      choices = [ "{0} {1}".format( i + 1, n )
                  for i, n in enumerate( namespaces ) ]
      choice = vimsupport.PresentDialog( "Insert which namespace:", choices )
      if choice < 0:
        return
      namespace = namespaces[ choice ]
    else:
      namespace = namespaces[ 0 ]

    vimsupport.InsertNamespace( namespace )


  def _GetRequiredNamespaceImport( self, completion ):
    if ( "extra_data" not in completion
         or "required_namespace_import" not in completion[ "extra_data" ] ):
      return None
    return completion[ "extra_data" ][ "required_namespace_import" ]


  def GetErrorCount( self ):
    return self._diag_interface.GetErrorCount()


  def GetWarningCount( self ):
    return self._diag_interface.GetWarningCount()


  def DiagnosticUiSupportedForCurrentFiletype( self ):
    return any( [ x in DIAGNOSTIC_UI_FILETYPES
                  for x in vimsupport.CurrentFiletypes() ] )


  def ShouldDisplayDiagnostics( self ):
    return bool( self._user_options[ 'show_diagnostics_ui' ] and
                 self.DiagnosticUiSupportedForCurrentFiletype() )


  def PopulateLocationListWithLatestDiagnostics( self ):
    # Do nothing if loc list is already populated by diag_interface
    if not self._user_options[ 'always_populate_location_list' ]:
      self._diag_interface.PopulateLocationList( self._latest_diagnostics )
    return bool( self._latest_diagnostics )


  def UpdateDiagnosticInterface( self ):
    self._diag_interface.UpdateWithNewDiagnostics( self._latest_diagnostics )


  def FileParseRequestReady( self, block = False ):
    return bool( self._latest_file_parse_request and
                 ( block or self._latest_file_parse_request.Done() ) )


  def HandleFileParseRequest( self, block = False ):
    # Order is important here:
    # FileParseRequestReady has a low cost, while
    # NativeFiletypeCompletionUsable is a blocking server request
    if ( self.FileParseRequestReady( block ) and
         self.NativeFiletypeCompletionUsable() ):

      if self.ShouldDisplayDiagnostics():
        self._latest_diagnostics = self._latest_file_parse_request.Response()
        self.UpdateDiagnosticInterface()
      else:
        # YCM client has a hard-coded list of filetypes which are known
        # to support diagnostics, self.DiagnosticUiSupportedForCurrentFiletype()
        #
        # For filetypes which don't support diagnostics, we just want to check
        # the _latest_file_parse_request for any exception or UnknownExtraConf
        # response, to allow the server to raise configuration warnings, etc.
        # to the user. We ignore any other supplied data.
        self._latest_file_parse_request.Response()

      self.NotifyFileParseReady( self._latest_file_parse_request_bufnr )
      # We set the file parse request to None because we want to prevent
      # repeated issuing of the same warnings/errors/prompts. Setting this to
      # None makes FileParseRequestReady return False until the next
      # request is created.
      #
      # Note: it is the server's responsibility to determine the frequency of
      # error/warning/prompts when receiving a FileReadyToParse event, but
      # it our responsibility to ensure that we only apply the
      # warning/error/prompt received once (for each event).
      self._latest_file_parse_request = None


  def ShowDetailedDiagnostic( self ):
    if not self.IsServerAlive():
      return
    try:
      debug_info = BaseRequest.PostDataToHandler( BuildRequestData(),
                                                  'detailed_diagnostic' )
      if 'message' in debug_info:
        vimsupport.PostVimMessage( debug_info[ 'message' ],
                                   warning = False )
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


  def RegisterFileParseReadyCallback( self, callback ):
    self._file_parse_ready_callbacks.append(callback)


  def NotifyFileParseReady( self, bufnr ):
    if self._file_parse_ready_callbacks:
      for callback in self._file_parse_ready_callbacks:
        try:
          callback( bufnr )
        except:
          pass


  def GetSemanticTokens( self, bufnr, start_line, start_column,
                         end_line, end_column, timeout = 0.01 ):
    if not self.IsServerAlive():
      return []
    try:
      buffer = vim.buffers[ bufnr ]
      request_data = {
        'filepath': vimsupport.GetBufferFilepath( buffer ),
        'filetypes': vimsupport.FiletypesForBuffer( buffer ),
        'start_line': start_line,
        'start_column': start_column,
        'end_line': end_line,
        'end_column': end_column,
      }
      return BaseRequest.PostDataToHandler( request_data,
                                            'semantic_tokens',
                                            timeout )
    except ServerError as e:
      if 'Still parsing' in str( e ):
        return 'Parsing'
      return 'Error'
    except Timeout:
      return 'Timeout'


  def GetSkippedRanges( self, bufnr, timeout = 0.01 ):
    if not self.IsServerAlive():
      return []
    try:
      buffer = vim.buffers[ bufnr ]
      request_data = {
        'filepath': vimsupport.GetBufferFilepath( buffer ),
        'filetypes': vimsupport.FiletypesForBuffer( buffer ),
      }
      return BaseRequest.PostDataToHandler( request_data,
                                            'skipped_ranges',
                                            timeout )
    except ServerError as e:
      if 'Still parsing' in str( e ):
        return 'Parsing'
      return 'Error'
    except Timeout:
      return 'Timeout'


  def _OpenLogs( self, stdout = True, stderr = True ):
    # Open log files in a horizontal window with the same behavior as the
    # preview window (same height and winfixheight enabled). Automatically
    # watch for changes. Set the cursor position at the end of the file.
    options = {
      'size': vimsupport.GetIntValue( '&previewheight' ),
      'fix': True,
      'watch': True,
      'position': 'end'
    }

    if stdout:
      vimsupport.OpenFilename( self._server_stdout, options )
    if stderr:
      vimsupport.OpenFilename( self._server_stderr, options )


  def _CloseLogs( self, stdout = True, stderr = True ):
    if stdout:
      vimsupport.CloseBuffersForFilename( self._server_stdout )
    if stderr:
      vimsupport.CloseBuffersForFilename( self._server_stderr )


  def ToggleLogs( self, stdout = True, stderr = True ):
    if ( stdout and
         vimsupport.BufferIsVisibleForFilename( self._server_stdout ) or
         stderr and
         vimsupport.BufferIsVisibleForFilename( self._server_stderr ) ):
      return self._CloseLogs( stdout = stdout, stderr = stderr )

    # Close hidden logfile buffers if any to keep a clean state
    self._CloseLogs( stdout = stdout, stderr = stderr )

    try:
      self._OpenLogs( stdout = stdout, stderr = stderr )
    except RuntimeError as error:
      vimsupport.PostVimMessage( 'YouCompleteMe encountered an error when '
                                 'opening logs: {0}.'.format( error ) )


  def CurrentFiletypeCompletionEnabled( self ):
    filetypes = vimsupport.CurrentFiletypes()
    filetype_to_disable = self._user_options[
      'filetype_specific_completion_to_disable' ]
    if '*' in filetype_to_disable:
      return False
    else:
      return not any([ x in filetype_to_disable for x in filetypes ])


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
      # getcwd() throws an exception when the CWD has been deleted.
      try:
        current_working_directory = os.getcwd()
      except OSError:
        return []
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


  def _AddUltiSnipsDataIfNeeded( self, extra_data ):
    # See :h UltiSnips#SnippetsInCurrentScope.
    try:
      vim.eval( 'UltiSnips#SnippetsInCurrentScope( 1 )' )
    except vim.error:
      return

    snippets = vimsupport.GetVariableValue( 'g:current_ulti_dict_info' )
    extra_data[ 'ultisnips_snippets' ] = [
      { 'trigger': trigger,
        'description': snippet[ 'description' ] }
      for trigger, snippet in iteritems( snippets )
    ]

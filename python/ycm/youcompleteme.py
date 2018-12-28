# Copyright (C) 2011-2018 YouCompleteMe contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from future.utils import iteritems
import base64
import json
import logging
import os
import signal
import vim
from subprocess import PIPE
from tempfile import NamedTemporaryFile
from ycm import base, paths, vimsupport
from ycm.buffer import ( BufferDict,
                         DIAGNOSTIC_UI_FILETYPES,
                         DIAGNOSTIC_UI_ASYNC_FILETYPES )
from ycmd import utils
from ycmd.request_wrap import RequestWrap
from ycm.omni_completer import OmniCompleter
from ycm import syntax_parse
from ycm.client.ycmd_keepalive import YcmdKeepalive
from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm.client.completer_available_request import SendCompleterAvailableRequest
from ycm.client.command_request import SendCommandRequest
from ycm.client.completion_request import CompletionRequest
from ycm.client.debug_info_request import ( SendDebugInfoRequest,
                                            FormatDebugInfoResponse )
from ycm.client.omni_completion_request import OmniCompletionRequest
from ycm.client.event_notification import SendEventNotificationAsync
from ycm.client.shutdown_request import SendShutdownRequest
from ycm.client.messages_request import MessagesPoll


def PatchNoProxy():
  current_value = os.environ.get( 'no_proxy', '' )
  additions = '127.0.0.1,localhost'
  os.environ[ 'no_proxy' ] = ( additions if not current_value
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
EXIT_CODE_UNEXPECTED_MESSAGE = (
  "Unexpected exit code {code}. "
  "Type ':YcmToggleLogs {logfile}' to check the logs." )
CORE_UNEXPECTED_MESSAGE = (
  "Unexpected error while loading the YCM core library. "
  "Type ':YcmToggleLogs {logfile}' to check the logs." )
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
SERVER_IDLE_SUICIDE_SECONDS = 1800  # 30 minutes
CLIENT_LOGFILE_FORMAT = 'ycm_'
SERVER_LOGFILE_FORMAT = 'ycmd_{port}_{std}_'

# Flag to set a file handle inheritable by child processes on Windows. See
# https://msdn.microsoft.com/en-us/library/ms724935.aspx
HANDLE_FLAG_INHERIT = 0x00000001


class YouCompleteMe( object ):
  def __init__( self ):
    self._available_completers = {}
    self._user_options = None
    self._user_notified_about_crash = False
    self._omnicomp = None
    self._buffers = None
    self._latest_completion_request = None
    self._logger = logging.getLogger( 'ycm' )
    self._client_logfile = None
    self._server_stdout = None
    self._server_stderr = None
    self._server_popen = None
    self._filetypes_with_keywords_loaded = set()
    self._ycmd_keepalive = YcmdKeepalive()
    self._server_is_ready_with_cache = False
    self._SetUpLogging()
    self._SetUpServer()
    self._ycmd_keepalive.Start()


  def _SetUpServer( self ):
    self._available_completers = {}
    self._user_notified_about_crash = False
    self._filetypes_with_keywords_loaded = set()
    self._server_is_ready_with_cache = False
    self._message_poll_request = None

    self._user_options = base.GetUserOptions()
    self._omnicomp = OmniCompleter( self._user_options )
    self._buffers = BufferDict( self._user_options )

    self._SetLogLevel()

    hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
    options_dict = dict( self._user_options )
    options_dict[ 'hmac_secret' ] = utils.ToUnicode(
      base64.b64encode( hmac_secret ) )
    options_dict[ 'server_keep_logfiles' ] = self._user_options[
      'keep_logfiles' ]

    # The temp options file is deleted by ycmd during startup.
    with NamedTemporaryFile( delete = False, mode = 'w+' ) as options_file:
      json.dump( options_dict, options_file )

    server_port = utils.GetUnusedLocalhostPort()

    BaseRequest.server_location = 'http://127.0.0.1:' + str( server_port )
    BaseRequest.hmac_secret = hmac_secret

    try:
      python_interpreter = paths.PathToPythonInterpreter()
    except RuntimeError as error:
      error_message = (
        "Unable to start the ycmd server. {0}. "
        "Correct the error then restart the server "
        "with ':YcmRestartServer'.".format( str( error ).rstrip( '.' ) ) )
      self._logger.exception( error_message )
      vimsupport.PostVimMessage( error_message )
      return

    args = [ python_interpreter,
             paths.PathToServerScript(),
             '--port={0}'.format( server_port ),
             '--options_file={0}'.format( options_file.name ),
             '--log={0}'.format( self._user_options[ 'log_level' ] ),
             '--idle_suicide_seconds={0}'.format(
                SERVER_IDLE_SUICIDE_SECONDS ) ]

    self._server_stdout = utils.CreateLogfile(
        SERVER_LOGFILE_FORMAT.format( port = server_port, std = 'stdout' ) )
    self._server_stderr = utils.CreateLogfile(
        SERVER_LOGFILE_FORMAT.format( port = server_port, std = 'stderr' ) )
    args.append( '--stdout={0}'.format( self._server_stdout ) )
    args.append( '--stderr={0}'.format( self._server_stderr ) )

    if self._user_options[ 'keep_logfiles' ]:
      args.append( '--keep_logfiles' )

    self._server_popen = utils.SafePopen( args, stdin_windows = PIPE,
                                          stdout = PIPE, stderr = PIPE )


  def _SetUpLogging( self ):
    def FreeFileFromOtherProcesses( file_object ):
      if utils.OnWindows():
        from ctypes import windll
        import msvcrt

        file_handle = msvcrt.get_osfhandle( file_object.fileno() )
        windll.kernel32.SetHandleInformation( file_handle,
                                              HANDLE_FLAG_INHERIT,
                                              0 )

    self._client_logfile = utils.CreateLogfile( CLIENT_LOGFILE_FORMAT )

    handler = logging.FileHandler( self._client_logfile )

    # On Windows and Python prior to 3.4, file handles are inherited by child
    # processes started with at least one replaced standard stream, which is the
    # case when we start the ycmd server (we are redirecting all standard
    # outputs into a pipe). These files cannot be removed while the child
    # processes are still up. This is not desirable for a logfile because we
    # want to remove it at Vim exit without having to wait for the ycmd server
    # to be completely shut down. We need to make the logfile handle
    # non-inheritable. See https://www.python.org/dev/peps/pep-0446 for more
    # details.
    FreeFileFromOtherProcesses( handler.stream )

    formatter = logging.Formatter( '%(asctime)s - %(levelname)s - %(message)s' )
    handler.setFormatter( formatter )

    self._logger.addHandler( handler )


  def _SetLogLevel( self ):
    log_level = self._user_options[ 'log_level' ]
    numeric_level = getattr( logging, log_level.upper(), None )
    if not isinstance( numeric_level, int ):
      raise ValueError( 'Invalid log level: {0}'.format( log_level ) )
    self._logger.setLevel( numeric_level )


  def IsServerAlive( self ):
    # When the process hasn't finished yet, poll() returns None.
    return bool( self._server_popen ) and self._server_popen.poll() is None


  def CheckIfServerIsReady( self ):
    if not self._server_is_ready_with_cache and self.IsServerAlive():
      self._server_is_ready_with_cache = BaseRequest().GetDataFromHandler(
          'ready', display_message = False )
    return self._server_is_ready_with_cache


  def IsServerReady( self ):
    return self._server_is_ready_with_cache


  def NotifyUserIfServerCrashed( self ):
    if ( not self._server_popen or self._user_notified_about_crash or
         self.IsServerAlive() ):
      return
    self._user_notified_about_crash = True

    return_code = self._server_popen.poll()
    logfile = os.path.basename( self._server_stderr )
    # See https://github.com/Valloric/ycmd#exit-codes for the list of exit
    # codes.
    if return_code == 3:
      error_message = CORE_UNEXPECTED_MESSAGE.format( logfile = logfile )
    elif return_code == 4:
      error_message = CORE_MISSING_MESSAGE
    elif return_code == 5:
      error_message = CORE_PYTHON2_MESSAGE
    elif return_code == 6:
      error_message = CORE_PYTHON3_MESSAGE
    elif return_code == 7:
      error_message = CORE_OUTDATED_MESSAGE
    else:
      error_message = EXIT_CODE_UNEXPECTED_MESSAGE.format( code = return_code,
                                                           logfile = logfile )

    error_message = SERVER_SHUTDOWN_MESSAGE + ' ' + error_message
    self._logger.error( error_message )
    vimsupport.PostVimMessage( error_message )


  def ServerPid( self ):
    if not self._server_popen:
      return -1
    return self._server_popen.pid


  def _ShutdownServer( self ):
    SendShutdownRequest()


  def RestartServer( self ):
    vimsupport.PostVimMessage( 'Restarting ycmd server...' )
    self._ShutdownServer()
    self._SetUpServer()


  def SendCompletionRequest( self, force_semantic = False ):
    request_data = BuildRequestData()
    request_data[ 'force_semantic' ] = force_semantic
    if not self.NativeFiletypeCompletionUsable():
      wrapped_request_data = RequestWrap( request_data )
      if self._omnicomp.ShouldUseNow( wrapped_request_data ):
        self._latest_completion_request = OmniCompletionRequest(
            self._omnicomp, wrapped_request_data )
        self._latest_completion_request.Start()
        return

    self._AddExtraConfDataIfNeeded( request_data )
    self._latest_completion_request = CompletionRequest( request_data )
    self._latest_completion_request.Start()


  def CompletionRequestReady( self ):
    return bool( self._latest_completion_request and
                 self._latest_completion_request.Done() )


  def GetCompletionResponse( self ):
    response = self._latest_completion_request.Response()
    response[ 'completions' ] = base.AdjustCandidateInsertionText(
        response[ 'completions' ] )
    return response


  def SendCommandRequest( self,
                          arguments,
                          modifiers,
                          has_range,
                          start_line,
                          end_line ):
    final_arguments = []
    for argument in arguments:
      # The ft= option which specifies the completer when running a command is
      # ignored because it has not been working for a long time. The option is
      # still parsed to not break users that rely on it.
      if argument.startswith( 'ft=' ):
        continue
      final_arguments.append( argument )

    extra_data = {
      'options': {
        'tab_size': vimsupport.GetIntValue( 'shiftwidth()' ),
        'insert_spaces': vimsupport.GetBoolValue( '&expandtab' )
      }
    }
    if has_range:
      extra_data.update( vimsupport.BuildRange( start_line, end_line ) )
    self._AddExtraConfDataIfNeeded( extra_data )

    return SendCommandRequest( final_arguments,
                               modifiers,
                               self._user_options[ 'goto_buffer_command' ],
                               extra_data )


  def GetDefinedSubcommands( self ):
    subcommands = BaseRequest().PostDataToHandler( BuildRequestData(),
                                                   'defined_subcommands' )
    return subcommands if subcommands else []


  def GetCurrentCompletionRequest( self ):
    return self._latest_completion_request


  def GetOmniCompleter( self ):
    return self._omnicomp


  def FiletypeCompleterExistsForFiletype( self, filetype ):
    try:
      return self._available_completers[ filetype ]
    except KeyError:
      pass

    exists_completer = SendCompleterAvailableRequest( filetype )
    if exists_completer is None:
      return False

    self._available_completers[ filetype ] = exists_completer
    return exists_completer


  def NativeFiletypeCompletionAvailable( self ):
    return any( self.FiletypeCompleterExistsForFiletype( x ) for x in
                vimsupport.CurrentFiletypes() )


  def NativeFiletypeCompletionUsable( self ):
    disabled_filetypes = self._user_options[
      'filetype_specific_completion_to_disable' ]
    return ( vimsupport.CurrentFiletypesEnabled( disabled_filetypes ) and
             self.NativeFiletypeCompletionAvailable() )


  def NeedsReparse( self ):
    return self.CurrentBuffer().NeedsReparse()


  def UpdateWithNewDiagnosticsForFile( self, filepath, diagnostics ):
    bufnr = vimsupport.GetBufferNumberForFilename( filepath )
    if bufnr in self._buffers and vimsupport.BufferIsVisible( bufnr ):
      # Note: We only update location lists, etc. for visible buffers, because
      # otherwise we default to using the current location list and the results
      # are that non-visible buffer errors clobber visible ones.
      self._buffers[ bufnr ].UpdateWithNewDiagnostics( diagnostics )
    else:
      # The project contains errors in file "filepath", but that file is not
      # open in any buffer. This happens for Language Server Protocol-based
      # completers, as they return diagnostics for the entire "project"
      # asynchronously (rather than per-file in the response to the parse
      # request).
      #
      # There are a number of possible approaches for
      # this, but for now we simply ignore them. Other options include:
      # - Use the QuickFix list to report project errors?
      # - Use a special buffer for project errors
      # - Put them in the location list of whatever the "current" buffer is
      # - Store them in case the buffer is opened later
      # - add a :YcmProjectDiags command
      # - Add them to errror/warning _counts_ but not any actual location list
      #   or other
      # - etc.
      #
      # However, none of those options are great, and lead to their own
      # complexities. So for now, we just ignore these diagnostics for files not
      # open in any buffer.
      pass


  def OnPeriodicTick( self ):
    if not self.IsServerAlive():
      # Server has died. We'll reset when the server is started again.
      return False
    elif not self.IsServerReady():
      # Try again in a jiffy
      return True

    if not self._message_poll_request:
      self._message_poll_request = MessagesPoll()

    if not self._message_poll_request.Poll( self ):
      # Don't poll again until some event which might change the server's mind
      # about whether to provide messages for the current buffer (e.g. buffer
      # visit, file ready to parse, etc.)
      self._message_poll_request = None
      return False

    # Poll again in a jiffy
    return True


  def OnFileReadyToParse( self ):
    if not self.IsServerAlive():
      self.NotifyUserIfServerCrashed()
      return

    if not self.IsServerReady():
      return

    extra_data = {}
    self._AddTagsFilesIfNeeded( extra_data )
    self._AddSyntaxDataIfNeeded( extra_data )
    self._AddExtraConfDataIfNeeded( extra_data )

    self.CurrentBuffer().SendParseRequest( extra_data )


  def OnBufferUnload( self, deleted_buffer_number ):
    SendEventNotificationAsync( 'BufferUnload', deleted_buffer_number )


  def UpdateMatches( self ):
    self.CurrentBuffer().UpdateMatches()


  def OnBufferVisit( self ):
    extra_data = {}
    self._AddUltiSnipsDataIfNeeded( extra_data )
    SendEventNotificationAsync( 'BufferVisit', extra_data = extra_data )


  def CurrentBuffer( self ):
    return self._buffers[ vimsupport.GetCurrentBufferNumber() ]


  def OnInsertLeave( self ):
    SendEventNotificationAsync( 'InsertLeave' )


  def OnCursorMoved( self ):
    self.CurrentBuffer().OnCursorMoved()


  def _CleanLogfile( self ):
    logging.shutdown()
    if not self._user_options[ 'keep_logfiles' ]:
      if self._client_logfile:
        utils.RemoveIfExists( self._client_logfile )


  def OnVimLeave( self ):
    self._ShutdownServer()
    self._CleanLogfile()


  def OnCurrentIdentifierFinished( self ):
    SendEventNotificationAsync( 'CurrentIdentifierFinished' )


  def OnCompleteDone( self ):
    completion_request = self.GetCurrentCompletionRequest()
    if completion_request:
      completion_request.OnCompleteDone()


  def GetErrorCount( self ):
    return self.CurrentBuffer().GetErrorCount()


  def GetWarningCount( self ):
    return self.CurrentBuffer().GetWarningCount()


  def DiagnosticUiSupportedForCurrentFiletype( self ):
    return any( x in DIAGNOSTIC_UI_FILETYPES or
                x in DIAGNOSTIC_UI_ASYNC_FILETYPES
                for x in vimsupport.CurrentFiletypes() )


  def ShouldDisplayDiagnostics( self ):
    return bool( self._user_options[ 'show_diagnostics_ui' ] and
                 self.DiagnosticUiSupportedForCurrentFiletype() )


  def _PopulateLocationListWithLatestDiagnostics( self ):
    return self.CurrentBuffer().PopulateLocationList()


  def FileParseRequestReady( self ):
    # Return True if server is not ready yet, to stop repeating check timer.
    return ( not self.IsServerReady() or
             self.CurrentBuffer().FileParseRequestReady() )


  def HandleFileParseRequest( self, block = False ):
    if not self.IsServerReady():
      return

    current_buffer = self.CurrentBuffer()
    # Order is important here:
    # FileParseRequestReady has a low cost, while
    # NativeFiletypeCompletionUsable is a blocking server request
    if ( not current_buffer.IsResponseHandled() and
         current_buffer.FileParseRequestReady( block ) and
         self.NativeFiletypeCompletionUsable() ):

      if self.ShouldDisplayDiagnostics():
        # Forcefuly update the location list, etc. from the parse request when
        # doing something like :YcmDiags
        current_buffer.UpdateDiagnostics( block is True )
      else:
        # YCM client has a hard-coded list of filetypes which are known
        # to support diagnostics, self.DiagnosticUiSupportedForCurrentFiletype()
        #
        # For filetypes which don't support diagnostics, we just want to check
        # the _latest_file_parse_request for any exception or UnknownExtraConf
        # response, to allow the server to raise configuration warnings, etc.
        # to the user. We ignore any other supplied data.
        current_buffer.GetResponse()

      # We set the file parse request as handled because we want to prevent
      # repeated issuing of the same warnings/errors/prompts. Setting this
      # makes IsRequestHandled return True until the next request is created.
      #
      # Note: it is the server's responsibility to determine the frequency of
      # error/warning/prompts when receiving a FileReadyToParse event, but
      # it is our responsibility to ensure that we only apply the
      # warning/error/prompt received once (for each event).
      current_buffer.MarkResponseHandled()


  def ShouldResendFileParseRequest( self ):
    return self.CurrentBuffer().ShouldResendParseRequest()


  def DebugInfo( self ):
    debug_info = ''
    if self._client_logfile:
      debug_info += 'Client logfile: {0}\n'.format( self._client_logfile )
    extra_data = {}
    self._AddExtraConfDataIfNeeded( extra_data )
    debug_info += FormatDebugInfoResponse( SendDebugInfoRequest( extra_data ) )
    debug_info += 'Server running at: {0}\n'.format(
      BaseRequest.server_location )
    if self._server_popen:
      debug_info += 'Server process ID: {0}\n'.format( self._server_popen.pid )
    if self._server_stdout and self._server_stderr:
      debug_info += ( 'Server logfiles:\n'
                      '  {0}\n'
                      '  {1}'.format( self._server_stdout,
                                      self._server_stderr ) )
    return debug_info


  def GetLogfiles( self ):
    logfiles_list = [ self._client_logfile,
                      self._server_stdout,
                      self._server_stderr ]

    extra_data = {}
    self._AddExtraConfDataIfNeeded( extra_data )
    debug_info = SendDebugInfoRequest( extra_data )
    if debug_info:
      completer = debug_info[ 'completer' ]
      if completer:
        for server in completer[ 'servers' ]:
          logfiles_list.extend( server[ 'logfiles' ] )

    logfiles = {}
    for logfile in logfiles_list:
      logfiles[ os.path.basename( logfile ) ] = logfile
    return logfiles


  def _OpenLogfile( self, logfile ):
    # Open log files in a horizontal window with the same behavior as the
    # preview window (same height and winfixheight enabled). Automatically
    # watch for changes. Set the cursor position at the end of the file.
    options = {
      'size': vimsupport.GetIntValue( '&previewheight' ),
      'fix': True,
      'focus': False,
      'watch': True,
      'position': 'end'
    }

    vimsupport.OpenFilename( logfile, options )


  def _CloseLogfile( self, logfile ):
    vimsupport.CloseBuffersForFilename( logfile )


  def ToggleLogs( self, *filenames ):
    logfiles = self.GetLogfiles()
    if not filenames:
      sorted_logfiles = sorted( list( logfiles ) )
      try:
        logfile_index = vimsupport.SelectFromList(
          'Which logfile do you wish to open (or close if already open)?',
          sorted_logfiles )
      except RuntimeError as e:
        vimsupport.PostVimMessage( str( e ) )
        return

      logfile = logfiles[ sorted_logfiles[ logfile_index ] ]
      if not vimsupport.BufferIsVisibleForFilename( logfile ):
        self._OpenLogfile( logfile )
      else:
        self._CloseLogfile( logfile )
      return

    for filename in set( filenames ):
      if filename not in logfiles:
        continue

      logfile = logfiles[ filename ]

      if not vimsupport.BufferIsVisibleForFilename( logfile ):
        self._OpenLogfile( logfile )
        continue

      self._CloseLogfile( logfile )


  def ShowDetailedDiagnostic( self ):
    detailed_diagnostic = BaseRequest().PostDataToHandler(
        BuildRequestData(), 'detailed_diagnostic' )

    if detailed_diagnostic and 'message' in detailed_diagnostic:
      vimsupport.PostVimMessage( detailed_diagnostic[ 'message' ],
                                 warning = False )


  def ForceCompileAndDiagnostics( self ):
    if not self.NativeFiletypeCompletionUsable():
      vimsupport.PostVimMessage(
          'Native filetype completion not supported for current file, '
          'cannot force recompilation.', warning = False )
      return False
    vimsupport.PostVimMessage(
        'Forcing compilation, this will block Vim until done.',
        warning = False )
    self.OnFileReadyToParse()
    self.HandleFileParseRequest( block = True )
    vimsupport.PostVimMessage( 'Diagnostics refreshed', warning = False )
    return True


  def ShowDiagnostics( self ):
    if not self.ForceCompileAndDiagnostics():
      return

    if not self._PopulateLocationListWithLatestDiagnostics():
      vimsupport.PostVimMessage( 'No warnings or errors detected.',
                                 warning = False )
      return

    if self._user_options[ 'open_loclist_on_ycm_diags' ]:
      vimsupport.OpenLocationList( focus = True )


  def _AddSyntaxDataIfNeeded( self, extra_data ):
    if not self._user_options[ 'seed_identifiers_with_syntax' ]:
      return
    filetype = vimsupport.CurrentFiletypes()[ 0 ]
    if filetype in self._filetypes_with_keywords_loaded:
      return

    if self.IsServerReady():
      self._filetypes_with_keywords_loaded.add( filetype )
    extra_data[ 'syntax_keywords' ] = list(
       syntax_parse.SyntaxKeywordsForCurrentBuffer() )


  def _AddTagsFilesIfNeeded( self, extra_data ):
    def GetTagFiles():
      tag_files = vim.eval( 'tagfiles()' )
      return [ os.path.join( utils.GetCurrentDirectory(), tag_file )
               for tag_file in tag_files ]

    if not self._user_options[ 'collect_identifiers_from_tags_files' ]:
      return
    extra_data[ 'tag_files' ] = GetTagFiles()


  def _AddExtraConfDataIfNeeded( self, extra_data ):
    def BuildExtraConfData( extra_conf_vim_data ):
      extra_conf_data = {}
      for expr in extra_conf_vim_data:
        try:
          extra_conf_data[ expr ] = vimsupport.VimExpressionToPythonType( expr )
        except vim.error:
          message = (
            "Error evaluating '{expr}' in the 'g:ycm_extra_conf_vim_data' "
            "option.".format( expr = expr ) )
          vimsupport.PostVimMessage( message, truncate = True )
          self._logger.exception( message )
      return extra_conf_data

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

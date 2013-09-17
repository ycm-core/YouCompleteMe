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

import imp
import os
import time
import vim
import ycm_core
import logging
import tempfile
from ycm import vimsupport
from ycm import base
from ycm import extra_conf_store
from ycm.completers.all.omni_completer import OmniCompleter
from ycm.completers.general.general_completer_store import GeneralCompleterStore


# TODO: Put the Request classes in separate files
class BaseRequest( object ):
  def __init__( self ):
    pass


  def Start( self ):
    pass


  def Done( self ):
    return True


  def Response( self ):
    return {}


class CompletionRequest( BaseRequest ):
  def __init__( self, ycm_state ):
    super( CompletionRequest, self ).__init__()

    self._completion_start_column = base.CompletionStartColumn()
    self._ycm_state = ycm_state
    self._request_data = _BuildRequestData( self._completion_start_column )
    self._do_filetype_completion = self._ycm_state.ShouldUseFiletypeCompleter(
      self._request_data )
    self._completer = ( self._ycm_state.GetFiletypeCompleter() if
                        self._do_filetype_completion else
                        self._ycm_state.GetGeneralCompleter() )


  def ShouldComplete( self ):
    return ( self._do_filetype_completion or
             self._ycm_state.ShouldUseGeneralCompleter( self._request_data ) )


  def CompletionStartColumn( self ):
    return self._completion_start_column


  def Start( self, query ):
    self._request_data[ 'query' ] = query
    self._completer.CandidatesForQueryAsync( self._request_data )

  def Done( self ):
    return self._completer.AsyncCandidateRequestReady()


  def Results( self ):
    try:
      return [ _ConvertCompletionDataToVimData( x )
              for x in self._completer.CandidatesFromStoredRequest() ]
    except Exception as e:
      vimsupport.PostVimMessage( str( e ) )
      return []



class CommandRequest( BaseRequest ):
  class ServerResponse( object ):
    def __init__( self ):
      pass

    def Valid( self ):
      return True

  def __init__( self, ycm_state, arguments, completer_target = None ):
    super( CommandRequest, self ).__init__()

    if not completer_target:
      completer_target = 'filetpe_default'

    if completer_target == 'omni':
      self._completer = ycm_state.GetOmniCompleter()
    elif completer_target == 'identifier':
      self._completer = ycm_state.GetGeneralCompleter()
    else:
      self._completer = ycm_state.GetFiletypeCompleter()
    self._arguments = arguments


  def Start( self ):
    self._completer.OnUserCommand( self._arguments,
                                   _BuildRequestData() )


  def Response( self ):
    # TODO: Call vimsupport.JumpToLocation if the user called a GoTo command...
    # we may want to have specific subclasses of CommandRequest so that a
    # GoToRequest knows it needs to jump after the data comes back.
    #
    # Also need to run the following on GoTo data:
    # CAREFUL about line/column number 0-based/1-based confusion!
    #
    # defs = []
    # defs.append( {'filename': definition.module_path.encode( 'utf-8' ),
    #               'lnum': definition.line,
    #               'col': definition.column + 1,
    #               'text': definition.description.encode( 'utf-8' ) } )
    # vim.eval( 'setqflist( %s )' % repr( defs ) )
    # vim.eval( 'youcompleteme#OpenGoToList()' )
    return self.ServerResponse()


class EventNotification( BaseRequest ):
  def __init__( self, event_name, ycm_state, extra_data = None ):
    super( EventNotification, self ).__init__()

    self._ycm_state = ycm_state
    self._event_name = event_name
    self._request_data = _BuildRequestData()
    if extra_data:
      self._request_data.update( extra_data )


  def Start( self ):
    event_handler = 'On' + self._event_name
    getattr( self._ycm_state.GetGeneralCompleter(),
             event_handler )( self._request_data )

    if self._ycm_state.FiletypeCompletionUsable():
      getattr( self._ycm_state.GetFiletypeCompleter(),
               event_handler )( self._request_data )

    if hasattr( extra_conf_store, event_handler ):
      getattr( extra_conf_store, event_handler )( self._request_data )



def SendEventNotificationAsync( event_name, ycm_state, extra_data = None ):
  event = EventNotification( event_name, ycm_state, extra_data )
  event.Start()


class YouCompleteMe( object ):
  def __init__( self, user_options ):
    # TODO: This should go into the server
    # TODO: Use more logging like we do in cs_completer
    self._logfile = tempfile.NamedTemporaryFile()
    logging.basicConfig( format='%(asctime)s - %(levelname)s - %(message)s',
                         filename=self._logfile.name,
                         level=logging.DEBUG )

    self._user_options = user_options
    self._gencomp = GeneralCompleterStore( user_options )
    self._omnicomp = OmniCompleter( user_options )
    self._filetype_completers = {}
    self._current_completion_request = None


  def CreateCompletionRequest( self ):
    # We have to store a reference to the newly created CompletionRequest
    # because VimScript can't store a reference to a Python object across
    # function calls... Thus we need to keep this request somewhere.
    self._current_completion_request = CompletionRequest( self )
    return self._current_completion_request


  def SendCommandRequest( self, arguments, completer ):
    # TODO: This should be inside a method in a command_request module
    request = CommandRequest( self, arguments, completer )
    request.Start()
    while not request.Done():
      time.sleep( 0.1 )

    return request.Response()


  def GetCurrentCompletionRequest( self ):
    return self._current_completion_request


  def GetGeneralCompleter( self ):
    return self._gencomp


  def GetOmniCompleter( self ):
    return self._omnicomp


  def GetFiletypeCompleter( self ):
    filetypes = vimsupport.CurrentFiletypes()

    completers = [ self.GetFiletypeCompleterForFiletype( filetype )
                   for filetype in filetypes ]

    if not completers:
      return None

    # Try to find a native completer first
    for completer in completers:
      if completer and completer is not self._omnicomp:
        return completer

    # Return the omni completer for the first filetype
    return completers[ 0 ]


  def GetFiletypeCompleterForFiletype( self, filetype ):
    try:
      return self._filetype_completers[ filetype ]
    except KeyError:
      pass

    module_path = _PathToFiletypeCompleterPluginLoader( filetype )

    completer = None
    supported_filetypes = [ filetype ]
    if os.path.exists( module_path ):
      module = imp.load_source( filetype, module_path )
      completer = module.GetCompleter( self._user_options )
      if completer:
        supported_filetypes.extend( completer.SupportedFiletypes() )
    else:
      completer = self._omnicomp

    for supported_filetype in supported_filetypes:
      self._filetype_completers[ supported_filetype ] = completer
    return completer


  def ShouldUseGeneralCompleter( self, request_data ):
    return self._gencomp.ShouldUseNow( request_data )


  def ShouldUseFiletypeCompleter( self, request_data ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().ShouldUseNow( request_data )
    return False


  def NativeFiletypeCompletionAvailable( self ):
    completer = self.GetFiletypeCompleter()
    return bool( completer ) and completer is not self._omnicomp


  def FiletypeCompletionAvailable( self ):
    return bool( self.GetFiletypeCompleter() )


  def NativeFiletypeCompletionUsable( self ):
    return ( self.CurrentFiletypeCompletionEnabled() and
             self.NativeFiletypeCompletionAvailable() )


  def FiletypeCompletionUsable( self ):
    return ( self.CurrentFiletypeCompletionEnabled() and
             self.FiletypeCompletionAvailable() )


  def OnFileReadyToParse( self ):
    extra_data = {}
    if self._user_options[ 'collect_identifiers_from_tags_files' ]:
      extra_data[ 'tag_files' ] = _GetTagFiles()

    # TODO: make this work again
    # if self._user_options[ 'seed_identifiers_with_syntax' ]:

    SendEventNotificationAsync( 'FileReadyToParse', self, extra_data )


  def OnBufferUnload( self, deleted_buffer_file ):
    SendEventNotificationAsync( 'BufferUnload',
                                self,
                                { 'unloaded_buffer': deleted_buffer_file } )


  def OnBufferVisit( self ):
    SendEventNotificationAsync( 'BufferVisit', self )


  def OnInsertLeave( self ):
    SendEventNotificationAsync( 'InsertLeave', self )


  def OnVimLeave( self ):
    SendEventNotificationAsync( 'VimLeave', self )


  def OnCurrentIdentifierFinished( self ):
    SendEventNotificationAsync( 'CurrentIdentifierFinished', self )


  def DiagnosticsForCurrentFileReady( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().DiagnosticsForCurrentFileReady()
    return False


  def GetDiagnosticsForCurrentFile( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().GetDiagnosticsForCurrentFile()
    return []


  def GetDetailedDiagnostic( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().GetDetailedDiagnostic()


  def GettingCompletions( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().GettingCompletions()
    return False


  def DebugInfo( self ):
    completers = set( self._filetype_completers.values() )
    completers.add( self._gencomp )
    output = []
    for completer in completers:
      if not completer:
        continue
      debug = completer.DebugInfo()
      if debug:
        output.append( debug )

    has_clang_support = ycm_core.HasClangSupport()
    output.append( 'Has Clang support compiled in: {0}'.format(
      has_clang_support ) )

    if has_clang_support:
      output.append( ycm_core.ClangVersion() )

    return '\n'.join( output )


  def CurrentFiletypeCompletionEnabled( self ):
    filetypes = vimsupport.CurrentFiletypes()
    filetype_to_disable = self._user_options[
      'filetype_specific_completion_to_disable' ]
    return not all([ x in filetype_to_disable for x in filetypes ])


def _PathToCompletersFolder():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'completers' )


def _PathToFiletypeCompleterPluginLoader( filetype ):
  return os.path.join( _PathToCompletersFolder(), filetype, 'hook.py' )


def _BuildRequestData( start_column = None, query = None ):
  line, column = vimsupport.CurrentLineAndColumn()
  request_data = {
    'filetypes': vimsupport.CurrentFiletypes(),
    'line_num': line,
    'column_num': column,
    'start_column': start_column,
    'line_value': vim.current.line,
    'filepath': vim.current.buffer.name,
    'file_data': vimsupport.GetUnsavedAndCurrentBufferData()
  }

  if query:
    request_data[ 'query' ] = query

  return request_data

def _ConvertCompletionDataToVimData( completion_data ):
  # see :h complete-items for a description of the dictionary fields
  vim_data = {
    'word' : completion_data[ 'insertion_text' ],
    'dup'  : 1,
  }

  if 'menu_text' in completion_data:
    vim_data[ 'abbr' ] = completion_data[ 'menu_text' ]
  if 'extra_menu_info' in completion_data:
    vim_data[ 'menu' ] = completion_data[ 'extra_menu_info' ]
  if 'kind' in completion_data:
    vim_data[ 'kind' ] = completion_data[ 'kind' ]
  if 'detailed_info' in completion_data:
    vim_data[ 'info' ] = completion_data[ 'detailed_info' ]

  return vim_data

def _GetTagFiles():
  tag_files = vim.eval( 'tagfiles()' )
  current_working_directory = os.getcwd()
  return [ os.path.join( current_working_directory, x ) for x in tag_files ]

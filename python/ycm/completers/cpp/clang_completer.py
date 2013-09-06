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

from collections import defaultdict
import ycm_core
import logging
from ycm import server_responses
from ycm import extra_conf_store
from ycm.completers.completer import Completer
from ycm.completers.cpp.flags import Flags

CLANG_FILETYPES = set( [ 'c', 'cpp', 'objc', 'objcpp' ] )
MIN_LINES_IN_FILE_TO_PARSE = 5
PARSING_FILE_MESSAGE = 'Still parsing file, no completions yet.'
NO_COMPILE_FLAGS_MESSAGE = 'Still no compile flags, no completions yet.'
NO_COMPLETIONS_MESSAGE = 'No completions found; errors in the file?'
INVALID_FILE_MESSAGE = 'File is invalid.'
FILE_TOO_SHORT_MESSAGE = (
  'File is less than {} lines long; not compiling.'.format(
    MIN_LINES_IN_FILE_TO_PARSE ) )
NO_DIAGNOSTIC_MESSAGE = 'No diagnostic for current line!'


class ClangCompleter( Completer ):
  def __init__( self, user_options ):
    super( ClangCompleter, self ).__init__( user_options )
    self.max_diagnostics_to_display = user_options[
      'max_diagnostics_to_display' ]
    self.completer = ycm_core.ClangCompleter()
    self.completer.EnableThreading()
    self.last_prepared_diagnostics = []
    self.parse_future = None
    self.flags = Flags()
    self.diagnostic_store = None
    self._logger = logging.getLogger( __name__ )

    # We set this flag when a compilation request comes in while one is already
    # in progress. We use this to trigger the pending request after the previous
    # one completes (from GetDiagnosticsForCurrentFile because that's the only
    # method that knows when the compilation has finished).
    self.extra_parse_desired = False


  def SupportedFiletypes( self ):
    return CLANG_FILETYPES


  def GetUnsavedFilesVector( self, request_data ):
    files = ycm_core.UnsavedFileVec()
    for filename, file_data in request_data[ 'file_data' ].iteritems():
      if not ClangAvailableForFiletypes( file_data[ 'filetypes' ] ):
        continue
      contents = file_data[ 'contents' ]
      if not contents or not filename:
        continue

      unsaved_file = ycm_core.UnsavedFile()
      unsaved_file.contents_ = contents
      unsaved_file.length_ = len( contents )
      unsaved_file.filename_ = filename

      files.append( unsaved_file )
    return files


  def CandidatesForQueryAsync( self, request_data ):
    filename = request_data[ 'filepath' ]

    if not filename:
      return

    if self.completer.UpdatingTranslationUnit( filename ):
      self.completions_future = None
      self._logger.info( PARSING_FILE_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        PARSING_FILE_MESSAGE )

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      self.completions_future = None
      self._logger.info( NO_COMPILE_FLAGS_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        NO_COMPILE_FLAGS_MESSAGE )

    # TODO: sanitize query, probably in C++ code

    files = ycm_core.UnsavedFileVec()
    query = request_data[ 'query' ]
    if not query:
      files = self.GetUnsavedFilesVector( request_data )

    line = request_data[ 'line_num' ] + 1
    column = request_data[ 'start_column' ] + 1
    self.completions_future = (
      self.completer.CandidatesForQueryAndLocationInFileAsync(
        query,
        filename,
        line,
        column,
        files,
        flags ) )


  def CandidatesFromStoredRequest( self ):
    if not self.completions_future:
      return []
    results = [ ConvertCompletionData( x ) for x in
                self.completions_future.GetResults() ]
    if not results:
      self._logger.warning( NO_COMPLETIONS_MESSAGE )
      raise RuntimeError( NO_COMPLETIONS_MESSAGE )
    return results


  def DefinedSubcommands( self ):
    return [ 'GoToDefinition',
             'GoToDeclaration',
             'GoToDefinitionElseDeclaration',
             'ClearCompilationFlagCache']


  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command = arguments[ 0 ]
    if command == 'GoToDefinition':
      self._GoToDefinition( request_data )
    elif command == 'GoToDeclaration':
      self._GoToDeclaration( request_data )
    elif command == 'GoToDefinitionElseDeclaration':
      self._GoToDefinitionElseDeclaration( request_data )
    elif command == 'ClearCompilationFlagCache':
      self._ClearCompilationFlagCache( request_data )


  def _LocationForGoTo( self, goto_function, request_data ):
    filename = request_data[ 'filepath' ]
    if not filename:
      self._logger.warning( INVALID_FILE_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        INVALID_FILE_MESSAGE )

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      self._logger.info( NO_COMPILE_FLAGS_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        NO_COMPILE_FLAGS_MESSAGE )

    files = self.GetUnsavedFilesVector()
    line = request_data[ 'line_num' ] + 1
    column = request_data[ 'start_column' ] + 1
    return getattr( self.completer, goto_function )(
        filename,
        line,
        column,
        files,
        flags )


  def _GoToDefinition( self, request_data ):
    location = self._LocationForGoTo( 'GetDefinitionLocation' )
    if not location or not location.IsValid():
      raise RuntimeError( 'Can\'t jump to definition.' )

    return server_responses.BuildGoToResponse( location.filename_,
                                               location.line_number_,
                                               location.column_number_ )


  def _GoToDeclaration( self, request_data ):
    location = self._LocationForGoTo( 'GetDeclarationLocation' )
    if not location or not location.IsValid():
      raise RuntimeError( 'Can\'t jump to declaration.' )

    return server_responses.BuildGoToResponse( location.filename_,
                                               location.line_number_,
                                               location.column_number_ )


  def _GoToDefinitionElseDeclaration( self, request_data ):
    location = self._LocationForGoTo( 'GetDefinitionLocation' )
    if not location or not location.IsValid():
      location = self._LocationForGoTo( 'GetDeclarationLocation' )
    if not location or not location.IsValid():
      raise RuntimeError( 'Can\'t jump to definition or declaration.' )

    return server_responses.BuildGoToResponse( location.filename_,
                                               location.line_number_,
                                               location.column_number_ )



  def _ClearCompilationFlagCache( self ):
    self.flags.Clear()



  def OnFileReadyToParse( self, request_data ):
    filename = request_data[ 'filepath' ]
    contents = request_data[ 'file_data' ][ filename ][ 'contents' ]
    if contents.count( '\n' ) < MIN_LINES_IN_FILE_TO_PARSE:
      self.parse_future = None
      self._logger.warning( FILE_TOO_SHORT_MESSAGE )
      raise ValueError( FILE_TOO_SHORT_MESSAGE )

    if not filename:
      self._logger.warning( INVALID_FILE_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        INVALID_FILE_MESSAGE )

    if self.completer.UpdatingTranslationUnit( filename ):
      self.extra_parse_desired = True
      return

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      self.parse_future = None
      self._logger.info( NO_COMPILE_FLAGS_MESSAGE )
      return server_responses.BuildDisplayMessageResponse(
        NO_COMPILE_FLAGS_MESSAGE )

    self.parse_future = self.completer.UpdateTranslationUnitAsync(
      filename,
      self.GetUnsavedFilesVector( request_data ),
      flags )

    self.extra_parse_desired = False


  def OnBufferUnload( self, deleted_buffer_file ):
    self.completer.DeleteCachesForFileAsync( deleted_buffer_file )


  def DiagnosticsForCurrentFileReady( self ):
    if not self.parse_future:
      return False

    return self.parse_future.ResultsReady()


  def GettingCompletions( self, request_data ):
    return self.completer.UpdatingTranslationUnit( request_data[ 'filepath' ] )


  def GetDiagnosticsForCurrentFile( self, request_data ):
    filename = request_data[ 'filepath' ]
    if self.DiagnosticsForCurrentFileReady():
      diagnostics = self.completer.DiagnosticsForFile( filename )
      self.diagnostic_store = DiagnosticsToDiagStructure( diagnostics )
      self.last_prepared_diagnostics = [
        server_responses.BuildDiagnosticData( x ) for x in
        diagnostics[ : self.max_diagnostics_to_display ] ]
      self.parse_future = None

      if self.extra_parse_desired:
        self.OnFileReadyToParse()

    return self.last_prepared_diagnostics


  def GetDetailedDiagnostic( self, request_data ):
    current_line = request_data[ 'line_num' ] + 1
    current_column = request_data[ 'column_num' ] + 1
    current_file = request_data[ 'filepath' ]

    if not self.diagnostic_store:
      return server_responses.BuildDisplayMessageResponse(
        NO_DIAGNOSTIC_MESSAGE )

    diagnostics = self.diagnostic_store[ current_file ][ current_line ]
    if not diagnostics:
      return server_responses.BuildDisplayMessageResponse(
        NO_DIAGNOSTIC_MESSAGE )

    closest_diagnostic = None
    distance_to_closest_diagnostic = 999

    for diagnostic in diagnostics:
      distance = abs( current_column - diagnostic.column_number_ )
      if distance < distance_to_closest_diagnostic:
        distance_to_closest_diagnostic = distance
        closest_diagnostic = diagnostic

    return server_responses.BuildDisplayMessageResponse(
      closest_diagnostic.long_formatted_text_ )


  def ShouldUseNow( self, request_data ):
    # We don't want to use the Completer API cache, we use one in the C++ code.
    return self.ShouldUseNowInner( request_data )


  def DebugInfo( self, request_data ):
    filename = request_data[ 'filepath' ]
    if not filename:
      return ''
    flags = self.flags.FlagsForFile( filename ) or []
    source = extra_conf_store.ModuleFileForSourceFile( filename )
    return server_responses.BuildDisplayMessageResponse(
      'Flags for {0} loaded from {1}:\n{2}'.format( filename,
                                                    source,
                                                    list( flags ) ) )


# TODO: make these functions module-local
# def CompletionDataToDict( completion_data ):
#   # see :h complete-items for a description of the dictionary fields
#   return {
#     'word' : completion_data.TextToInsertInBuffer(),
#     'abbr' : completion_data.MainCompletionText(),
#     'menu' : completion_data.ExtraMenuInfo(),
#     'kind' : completion_data.kind_,
#     'info' : completion_data.DetailedInfoForPreviewWindow(),
#     'dup'  : 1,
#   }


# def DiagnosticToDict( diagnostic ):
#   # see :h getqflist for a description of the dictionary fields
#   return {
#     # TODO: wrap the bufnr generation into a function
#     'bufnr' : int( vim.eval( "bufnr('{0}', 1)".format(
#       diagnostic.filename_ ) ) ),
#     'lnum'  : diagnostic.line_number_,
#     'col'   : diagnostic.column_number_,
#     'text'  : diagnostic.text_,
#     'type'  : diagnostic.kind_,
#     'valid' : 1
#   }


def ConvertCompletionData( completion_data ):
  return server_responses.BuildCompletionData(
    insertion_text = completion_data.TextToInsertInBuffer(),
    menu_text = completion_data.MainCompletionText(),
    extra_menu_info = completion_data.ExtraMenuInfo(),
    kind = completion_data.kind_,
    detailed_info = completion_data.DetailedInfoForPreviewWindow() )


def DiagnosticsToDiagStructure( diagnostics ):
  structure = defaultdict(lambda : defaultdict(list))
  for diagnostic in diagnostics:
    structure[ diagnostic.filename_ ][ diagnostic.line_number_ ].append(
        diagnostic )
  return structure


def ClangAvailableForFiletypes( filetypes ):
  return any( [ filetype in CLANG_FILETYPES for filetype in filetypes ] )


def InCFamilyFile( filetypes ):
  return ClangAvailableForFiletypes( filetypes )

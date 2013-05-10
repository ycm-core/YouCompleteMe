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

from completers.completer import Completer
from collections import defaultdict
import vim
import vimsupport
import ycm_core
import extra_conf_store
from flags import Flags

CLANG_FILETYPES = set( [ 'c', 'cpp', 'objc', 'objcpp' ] )
MAX_DIAGNOSTICS_TO_DISPLAY = int( vimsupport.GetVariableValue(
  "g:ycm_max_diagnostics_to_display" ) )


class ClangCompleter( Completer ):
  def __init__( self ):
    super( ClangCompleter, self ).__init__()
    self.completer = ycm_core.ClangCompleter()
    self.completer.EnableThreading()
    self.contents_holder = []
    self.filename_holder = []
    self.last_prepared_diagnostics = []
    self.parse_future = None
    self.flags = Flags()
    self.diagnostic_store = None


  def SupportedFiletypes( self ):
    return CLANG_FILETYPES


  def GetUnsavedFilesVector( self ):
    # CAREFUL HERE! For UnsavedFile filename and contents we are referring
    # directly to Python-allocated and -managed memory since we are accepting
    # pointers to data members of python objects. We need to ensure that those
    # objects outlive our UnsavedFile objects. This is why we need the
    # contents_holder and filename_holder lists, to make sure the string objects
    # are still around when we call CandidatesForQueryAndLocationInFile.  We do
    # this to avoid an extra copy of the entire file contents.

    files = ycm_core.UnsavedFileVec()
    self.contents_holder = []
    self.filename_holder = []
    for buffer in vimsupport.GetUnsavedBuffers():
      if not ClangAvailableForBuffer( buffer ):
        continue
      contents = '\n'.join( buffer )
      name = buffer.name
      if not contents or not name:
        continue
      self.contents_holder.append( contents )
      self.filename_holder.append( name )

      unsaved_file = ycm_core.UnsavedFile()
      unsaved_file.contents_ = self.contents_holder[ -1 ]
      unsaved_file.length_ = len( self.contents_holder[ -1 ] )
      unsaved_file.filename_ = self.filename_holder[ -1 ]

      files.append( unsaved_file )

    return files


  def CandidatesForQueryAsync( self, query, start_column ):
    filename = vim.current.buffer.name

    if not filename:
      return

    if self.completer.UpdatingTranslationUnit( filename ):
      vimsupport.PostVimMessage( 'Still parsing file, no completions yet.' )
      self.completions_future = None
      return

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      vimsupport.PostVimMessage( 'Still no compile flags, no completions yet.' )
      self.completions_future = None
      return

    # TODO: sanitize query, probably in C++ code

    files = ycm_core.UnsavedFileVec()
    if not query:
      files = self.GetUnsavedFilesVector()

    line, _ = vim.current.window.cursor
    column = start_column + 1
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
    results = [ CompletionDataToDict( x ) for x in
                self.completions_future.GetResults() ]
    if not results:
      vimsupport.PostVimMessage( 'No completions found; errors in the file?' )
    return results


  def DefinedSubcommands( self ):
    return [ "GoToDefinition",
             "GoToDeclaration",
             "GoToDefinitionElseDeclaration" ]


  def OnUserCommand( self, arguments ):
    if not arguments:
      self.EchoUserCommandsHelpMessage()
      return

    command = arguments[ 0 ]
    if command == 'GoToDefinition':
      self._GoToDefinition()
    elif command == 'GoToDeclaration':
      self._GoToDeclaration()
    elif command == 'GoToDefinitionElseDeclaration':
      self._GoToDefinitionElseDeclaration()


  def _LocationForGoTo( self, goto_function ):
    filename = vim.current.buffer.name
    if not filename:
      return None

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      vimsupport.PostVimMessage( 'Still no compile flags, can\'t compile.' )
      return None

    files = self.GetUnsavedFilesVector()
    line, column = vimsupport.CurrentLineAndColumn()
    # Making the line & column 1-based instead of 0-based
    line += 1
    column += 1
    return getattr( self.completer, goto_function )(
        filename,
        line,
        column,
        files,
        flags )


  def _GoToDefinition( self ):
    location = self._LocationForGoTo( 'GetDefinitionLocation' )
    if not location or not location.IsValid():
      vimsupport.PostVimMessage( 'Can\'t jump to definition.' )
      return

    vimsupport.JumpToLocation( location.filename_,
                               location.line_number_,
                               location.column_number_ )


  def _GoToDeclaration( self ):
    location = self._LocationForGoTo( 'GetDeclarationLocation' )
    if not location or not location.IsValid():
      vimsupport.PostVimMessage( 'Can\'t jump to declaration.' )
      return

    vimsupport.JumpToLocation( location.filename_,
                               location.line_number_,
                               location.column_number_ )


  def _GoToDefinitionElseDeclaration( self ):
    location = self._LocationForGoTo( 'GetDefinitionLocation' )
    if not location or not location.IsValid():
      location = self._LocationForGoTo( 'GetDeclarationLocation' )
    if not location or not location.IsValid():
      vimsupport.PostVimMessage( 'Can\'t jump to definition or declaration.' )
      return

    vimsupport.JumpToLocation( location.filename_,
                               location.line_number_,
                               location.column_number_ )


  def OnFileReadyToParse( self ):
    if vimsupport.NumLinesInBuffer( vim.current.buffer ) < 5:
      self.parse_future = None
      return

    filename = vim.current.buffer.name
    if not filename:
      return

    if self.completer.UpdatingTranslationUnit( filename ):
      return

    flags = self.flags.FlagsForFile( filename )
    if not flags:
      self.parse_future = None
      return

    self.parse_future = self.completer.UpdateTranslationUnitAsync(
      filename,
      self.GetUnsavedFilesVector(),
      flags )


  def OnBufferDelete( self, deleted_buffer_file ):
    self.completer.DeleteCachesForFileAsync( deleted_buffer_file )


  def DiagnosticsForCurrentFileReady( self ):
    if not self.parse_future:
      return False

    return self.parse_future.ResultsReady()


  def GettingCompletions( self ):
    return self.completer.UpdatingTranslationUnit( vim.current.buffer.name )


  def GetDiagnosticsForCurrentFile( self ):
    if self.DiagnosticsForCurrentFileReady():
      diagnostics = self.completer.DiagnosticsForFile( vim.current.buffer.name )
      self.diagnostic_store = DiagnosticsToDiagStructure( diagnostics )
      self.last_prepared_diagnostics = [ DiagnosticToDict( x ) for x in
          diagnostics[ : MAX_DIAGNOSTICS_TO_DISPLAY ] ]
      self.parse_future = None
    return self.last_prepared_diagnostics


  def ShowDetailedDiagnostic( self ):
    current_line, current_column = vimsupport.CurrentLineAndColumn()

    # CurrentLineAndColumn() numbers are 0-based, clang numbers are 1-based
    current_line += 1
    current_column += 1

    current_file = vim.current.buffer.name

    if not self.diagnostic_store:
      vimsupport.PostVimMessage( "No diagnostic for current line!" )
      return

    diagnostics = self.diagnostic_store[ current_file ][ current_line ]
    if not diagnostics:
      vimsupport.PostVimMessage( "No diagnostic for current line!" )
      return

    closest_diagnostic = None
    distance_to_closest_diagnostic = 999

    for diagnostic in diagnostics:
      distance = abs( current_column - diagnostic.column_number_ )
      if distance < distance_to_closest_diagnostic:
        distance_to_closest_diagnostic = distance
        closest_diagnostic = diagnostic

    vimsupport.EchoText( closest_diagnostic.long_formatted_text_ )


  def ShouldUseNow( self, start_column ):
    # We don't want to use the Completer API cache, we use one in the C++ code.
    return self.ShouldUseNowInner( start_column )


  def DebugInfo( self ):
    filename = vim.current.buffer.name
    if not filename:
      return ''
    flags = self.flags.FlagsForFile( filename ) or []
    source = extra_conf_store.ModuleFileForSourceFile( filename )
    return 'Flags for {0} loaded from {1}:\n{2}'.format( filename,
                                                         source,
                                                         list( flags ) )


# TODO: make these functions module-local
def CompletionDataToDict( completion_data ):
  # see :h complete-items for a description of the dictionary fields
  return {
    'word' : completion_data.TextToInsertInBuffer(),
    'abbr' : completion_data.MainCompletionText(),
    'menu' : completion_data.ExtraMenuInfo(),
    'kind' : completion_data.kind_,
    'info' : completion_data.DetailedInfoForPreviewWindow(),
    'dup'  : 1,
  }


def DiagnosticToDict( diagnostic ):
  # see :h getqflist for a description of the dictionary fields
  return {
    # TODO: wrap the bufnr generation into a function
    'bufnr' : int( vim.eval( "bufnr('{0}', 1)".format(
      diagnostic.filename_ ) ) ),
    'lnum'  : diagnostic.line_number_,
    'col'   : diagnostic.column_number_,
    'text'  : diagnostic.text_,
    'type'  : diagnostic.kind_,
    'valid' : 1
  }


def DiagnosticsToDiagStructure( diagnostics ):
  structure = defaultdict(lambda : defaultdict(list))
  for diagnostic in diagnostics:
    structure[ diagnostic.filename_ ][ diagnostic.line_number_ ].append(
        diagnostic )
  return structure


def ClangAvailableForBuffer( buffer_object ):
  filetypes = vimsupport.FiletypesForBuffer( buffer_object )
  return any( [ filetype in CLANG_FILETYPES for filetype in filetypes ] )


def InCFamilyFile():
  return any( [ filetype in CLANG_FILETYPES for filetype in
                vimsupport.CurrentFiletypes() ] )


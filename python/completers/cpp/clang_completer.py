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
import vim
import vimsupport
import ycm_core
from flags import Flags

CLANG_FILETYPES = set( [ 'c', 'cpp', 'objc', 'objcpp' ] )


class ClangCompleter( Completer ):
  def __init__( self ):
    self.completer = ycm_core.ClangCompleter()
    self.completer.EnableThreading()
    self.contents_holder = []
    self.filename_holder = []
    self.last_diagnostics = []
    self.possibly_new_diagnostics = False
    self.flags = Flags()


  def SupportedFiletypes( self ):
    return CLANG_FILETYPES


  def GetUnsavedFilesVector( self ):
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


  def CandidatesForQueryAsync( self, query ):
    if self.completer.UpdatingTranslationUnit():
      vimsupport.PostVimMessage( 'Still parsing file, no completions yet.' )
      self.future = None
      return

    # TODO: sanitize query

    # CAREFUL HERE! For UnsavedFile filename and contents we are referring
    # directly to Python-allocated and -managed memory since we are accepting
    # pointers to data members of python objects. We need to ensure that those
    # objects outlive our UnsavedFile objects. This is why we need the
    # contents_holder and filename_holder lists, to make sure the string objects
    # are still around when we call CandidatesForQueryAndLocationInFile.  We do
    # this to avoid an extra copy of the entire file contents.

    files = ycm_core.UnsavedFileVec()
    if not query:
      files = self.GetUnsavedFilesVector()

    line, _ = vim.current.window.cursor
    column = int( vim.eval( "s:completion_start_column" ) ) + 1
    current_buffer = vim.current.buffer
    self.future = self.completer.CandidatesForQueryAndLocationInFileAsync(
      query,
      current_buffer.name,
      line,
      column,
      files,
      self.flags.FlagsForFile( current_buffer.name ) )


  def CandidatesFromStoredRequest( self ):
    if not self.future:
      return []
    results = [ CompletionDataToDict( x ) for x in self.future.GetResults() ]
    if not results:
      vimsupport.PostVimMessage( 'No completions found; errors in the file?' )
    return results


  def OnFileReadyToParse( self ):
    if vimsupport.NumLinesInBuffer( vim.current.buffer ) < 5:
      return

    self.possibly_new_diagnostics = True

    filename = vim.current.buffer.name
    self.completer.UpdateTranslationUnitAsync(
      filename,
      self.GetUnsavedFilesVector(),
      self.flags.FlagsForFile( filename ) )


  def DiagnosticsForCurrentFileReady( self ):
    return ( self.possibly_new_diagnostics and not
             self.completer.UpdatingTranslationUnit() )


  def GetDiagnosticsForCurrentFile( self ):
    if self.DiagnosticsForCurrentFileReady():
      self.last_diagnostics = [ DiagnosticToDict( x ) for x in
                                self.completer.DiagnosticsForFile(
                                  vim.current.buffer.name ) ]
      self.possibly_new_diagnostics = False
    return self.last_diagnostics


  def ShouldUseNow( self, start_column ):
    return ShouldUseClang( start_column )




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


def ClangAvailableForBuffer( buffer_object ):
  filetype = vim.eval( 'getbufvar({0}, "&ft")'.format( buffer_object.number ) )
  return filetype in CLANG_FILETYPES


def ShouldUseClang( start_column ):
  line = vim.current.line
  previous_char_index = start_column - 1
  if ( not len( line ) or
       previous_char_index < 0 or
       previous_char_index >= len( line ) ):
    return False

  if line[ previous_char_index ] == '.':
    return True

  if previous_char_index - 1 < 0:
    return False

  two_previous_chars = line[ previous_char_index - 1 : start_column ]
  if ( two_previous_chars == '->' or two_previous_chars == '::' ):
    return True

  return False

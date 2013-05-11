#!/usr/bin/env python
#
# Copyright (C) 2013  Stanislav Golovanov <stgolovanov@gmail.com>
#                     Strahinja Val Markovic  <val@markovic.io>
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
from completers.all.identifier_completer import IdentifierCompleter
from filename_completer import FilenameCompleter

try:
  from ultisnips_completer import UltiSnipsCompleter
  USE_ULTISNIPS_COMPLETER = True
except ImportError:
  USE_ULTISNIPS_COMPLETER = False



class GeneralCompleterStore( Completer ):
  """
  Holds a list of completers that can be used in all filetypes.

  It overrides all Competer API methods so that specific calls to
  GeneralCompleterStore are passed to all general completers.
  """

  def __init__( self ):
    super( GeneralCompleterStore, self ).__init__()
    self._identifier_completer = IdentifierCompleter()
    self._filename_completer = FilenameCompleter()
    self._ultisnips_completer = ( UltiSnipsCompleter()
                                  if USE_ULTISNIPS_COMPLETER else None )
    self._non_filename_completers = filter( lambda x: x,
                                            [ self._ultisnips_completer,
                                              self._identifier_completer ] )
    self._all_completers = filter( lambda x: x,
                                   [ self._identifier_completer,
                                     self._filename_completer,
                                     self._ultisnips_completer ] )
    self._current_query_completers = []


  def SupportedFiletypes( self ):
    return set()


  def ShouldUseNow( self, start_column ):
    self._current_query_completers = []

    if self._filename_completer.ShouldUseNow( start_column ):
      self._current_query_completers = [ self._filename_completer ]
      return True

    should_use_now = False

    for completer in self._non_filename_completers:
      should_use_this_completer = completer.ShouldUseNow( start_column )
      should_use_now = should_use_now or should_use_this_completer

      if should_use_this_completer:
        self._current_query_completers.append( completer )

    return should_use_now


  def CandidatesForQueryAsync( self, query, start_column ):
    for completer in self._current_query_completers:
      completer.CandidatesForQueryAsync( query, start_column )


  def AsyncCandidateRequestReady( self ):
    return all( x.AsyncCandidateRequestReady() for x in
                self._current_query_completers )


  def CandidatesFromStoredRequest( self ):
    candidates = []
    for completer in self._current_query_completers:
      candidates += completer.CandidatesFromStoredRequest()

    return candidates


  def OnFileReadyToParse( self ):
    for completer in self._all_completers:
      completer.OnFileReadyToParse()


  def OnCursorMovedInsertMode( self ):
    for completer in self._all_completers:
      completer.OnCursorMovedInsertMode()


  def OnCursorMovedNormalMode( self ):
    for completer in self._all_completers:
      completer.OnCursorMovedNormalMode()


  def OnBufferVisit( self ):
    for completer in self._all_completers:
      completer.OnBufferVisit()


  def OnBufferUnload( self, deleted_buffer_file ):
    for completer in self._all_completers:
      completer.OnBufferUnload( deleted_buffer_file )


  def OnCursorHold( self ):
    for completer in self._all_completers:
      completer.OnCursorHold()


  def OnInsertLeave( self ):
    for completer in self._all_completers:
      completer.OnInsertLeave()


  def OnCurrentIdentifierFinished( self ):
    for completer in self._all_completers:
      completer.OnCurrentIdentifierFinished()


  def GettingCompletions( self ):
    for completer in self._all_completers:
      completer.GettingCompletions()

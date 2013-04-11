#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
#
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

from completers.completer import Completer, CompletionsCache
import vimsupport
import ycm_core
import vim
import os
import re


class FilenameCompleter( Completer ):
  """
  General completer that provides filename and filepath completions.

  It maintains a cache of completions which is invalidated on each '/' symbol.
  """
  def __init__(self):
    super( FilenameCompleter, self ).__init__()
    self._candidates = []
    self.query = None
    self.ShouldUse = False

    # TODO look into vim-style path globbing, NCC has a nice implementation
    self.pat = re.compile( """(?:[A-z]+:/|[/~]|\./|\.+/)+ # 1 or more 'D:/'-like token or '/' or '~' or './' or '../'
                             (?:[ /a-zA-Z0-9()$+_~.\x80-\xff-\[\]]| # any alphanumeric symbal and space literal
                             [^\x20-\x7E]| # skip any special symbols
                             \\.)* # backslash and 1 char after it. + matches 1 or more of whole group
                           """, re.X )


  def SupportedFiletypes( self ):
    # magic token meaning all filetypes
    return set( [ 'ycm_all' ] )


  def ShouldUseNowInner( self, start_column ):
    token = vim.current.line[ start_column - 1 ]
    if token  == '/' or self.ShouldUse:
      self.ShouldUse = True
      return True
    else:
      return False


  def CandidatesForQueryAsync( self, query, start_column ):
    self.completion_start_column = start_column

    if query and self.completions_cache and self.completions_cache.CacheValid(
      start_column ):
      self.completions_cache.filtered_completions = self._generate_results(
          self.completions_cache.raw_completions, query )
    else:
      self.completions_cache = None
      self.CandidatesForQueryAsyncInner( query, start_column )


  def CandidatesForQueryAsyncInner( self, query, start_column ):
    self._candidates = []
    self.query = query
    self.finished = False
    self.line = str( vim.current.line.strip() )
    self.SetCandidates()


  def AsyncCandidateRequestReadyInner( self ):
    return self.finished


  def OnInsertLeave( self ):
    # TODO this a hackish way to keep results when typing 2-3rd char after slash
    # because identifier completer will kick in and replace results for 1 char.
    # Need to do something better
    self.ShouldUse = False


  def CandidatesFromStoredRequest( self ):
    if self.completions_cache:
      return self.completions_cache.filtered_completions
    else:
      self.completions_cache = CompletionsCache()
      self.completions_cache.raw_completions = self.CandidatesFromStoredRequestInner()
      self.completions_cache.line, _ = vimsupport.CurrentLineAndColumn()
      self.completions_cache.column = self.completion_start_column
      return self._generate_results( self.completions_cache.raw_completions, self.query )

  def CandidatesFromStoredRequestInner( self ):
    return self._candidates


  def SetCandidates( self ):
    path = self.pat.search( self.line )
    self.working_dir = os.path.expanduser( path.group() ) if path else ''

    try:
      self._candidates = os.listdir( self.working_dir )
    except:
      self._candidates = []

    self.finished = True


  def _generate_results( self, completions, query ):
    try:
      matches = ycm_core.FilterAndSortCandidates( completions, '', query ) \
              if query else completions
    except IndexError, error:
      # Vim python is not thread safe, so this sometimes causes vim crashes.
      # Disabling for now.
      #vimsupport.PostVimMessage( 'Filtering failed, probably non-ASCII symbols. '
                                 #'Returning empty list. '
                                 #'Full error: {0}'.format( str(error) ) )
      matches = []

    return [ {'word': path,
            'dup': 1,
            'menu': '[Dir]' if os.path.isdir( self.working_dir + '/' + path ) else '[File]'
             } for path in matches ]

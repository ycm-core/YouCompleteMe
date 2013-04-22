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

from completers.completer import GeneralCompleter, CompletionsCache
import vimsupport
import ycm_core
import vim
import os
import re


class FilenameCompleter( GeneralCompleter ):
  """
  General completer that provides filename and filepath completions.

  It maintains a cache of completions which is invalidated on each '/' symbol.
  """
  def __init__(self):
    super( FilenameCompleter, self ).__init__()
    self._candidates = []
    self._query = None
    self._should_use = False

    # TODO look into vim-style path globbing, NCC has a nice implementation
    self._path_regex = re.compile( """(?:[A-z]+:/|[/~]|\./|\.+/)+ # 1 or more 'D:/'-like token or '/' or '~' or './' or '../'
                             (?:[ /a-zA-Z0-9()$+_~.\x80-\xff-\[\]]| # any alphanumeric symbal and space literal
                             [^\x20-\x7E]| # skip any special symbols
                             \\.)* # backslash and 1 char after it. + matches 1 or more of whole group
                           """, re.X )


  def ShouldUseNowInner( self, start_column ):
    token = vim.current.line[ start_column - 1 ]
    if token  == '/' or self._should_use:
      self._should_use = True
      return True
    else:
      return False


  def CandidatesForQueryAsyncInner( self, query, start_column ):
    self._candidates = []
    self._query = query
    self._completions_ready = False
    self.line = str( vim.current.line.strip() )
    self.SetCandidates()


  def AsyncCandidateRequestReadyInner( self ):
    return self._completions_ready


  def OnInsertLeave( self ):
    # TODO this a hackish way to keep results when typing 2-3rd char after slash
    # because identifier completer will kick in and replace results for 1 char.
    # Need to do something better
    self._should_use = False


  def CandidatesFromStoredRequestInner( self ):
    return self._candidates


  def SetCandidates( self ):
    path = self._path_regex.search( self.line )
    self._working_dir = os.path.expanduser( path.group() ) if path else ''

    try:
      paths = os.listdir( self._working_dir )
    except:
      paths = []

    self._candidates = [ {'word': path,
                        'dup': 1,
                        'menu': '[Dir]' if os.path.isdir( self._working_dir + \
                                                         '/' + path ) else '[File]'
                        } for path in paths ]

    self._completions_ready = True

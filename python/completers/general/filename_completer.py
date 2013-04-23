#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
#                    Strahinja Val Markovic  <val@markovic.io>
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

from completers.threaded_completer import ThreadedCompleter
import vim
import vimsupport
import os
import re

USE_WORKING_DIR = vimsupport.GetBoolValue(
  'g:ycm_filepath_completion_use_working_dir' )

class FilenameCompleter( ThreadedCompleter ):
  """
  General completer that provides filename and filepath completions.
  """

  def __init__(self):
    super( FilenameCompleter, self ).__init__()

    self._path_regex = re.compile("""
      # 1 or more 'D:/'-like token or '/' or '~' or './' or '../'
      (?:[A-z]+:/|[/~]|\./|\.+/)+

      # any alphanumeric symbal and space literal
      (?:[ /a-zA-Z0-9()$+_~.\x80-\xff-\[\]]|

      # skip any special symbols
      [^\x20-\x7E]|

      # backslash and 1 char after it. + matches 1 or more of whole group
      \\.)*$
      """, re.X )


  def ShouldUseNowInner( self, start_column ):
    return vim.current.line[ start_column - 1 ] == '/'


  def SupportedFiletypes( self ):
    return []


  def ComputeCandidates( self, unused_query, start_column ):
    def GenerateCandidateForPath( path, path_dir ):
      is_dir = os.path.isdir( os.path.join( path_dir, path ) )
      return { 'word': path,
               'dup': 1,
               'menu': '[Dir]' if is_dir else '[File]' }

    line = vim.current.line[ :start_column ]
    match = self._path_regex.search( line )
    path_dir = os.path.expanduser( match.group() ) if match else ''

    if not USE_WORKING_DIR and not path_dir.startswith( '/' ):
      path_dir = os.path.join( os.path.dirname( vim.current.buffer.name ),
                               path_dir )

    try:
      paths = os.listdir( path_dir )
    except:
      paths = []

    return [ GenerateCandidateForPath( path, path_dir ) for path in paths ]

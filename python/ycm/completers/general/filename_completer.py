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

import vim
import os
import re

from ycm import vimsupport
from ycm.completers.threaded_completer import ThreadedCompleter
from ycm.completers.cpp.clang_completer import InCFamilyFile
from ycm.completers.cpp.flags import Flags

USE_WORKING_DIR = vimsupport.GetBoolValue(
  'g:ycm_filepath_completion_use_working_dir' )


class FilenameCompleter( ThreadedCompleter ):
  """
  General completer that provides filename and filepath completions.
  """

  def __init__( self ):
    super( FilenameCompleter, self ).__init__()
    self._flags = Flags()

    self._path_regex = re.compile( """
      # 1 or more 'D:/'-like token or '/' or '~' or './' or '../'
      (?:[A-z]+:/|[/~]|\./|\.+/)+

      # any alphanumeric symbal and space literal
      (?:[ /a-zA-Z0-9()$+_~.\x80-\xff-\[\]]|

      # skip any special symbols
      [^\x20-\x7E]|

      # backslash and 1 char after it. + matches 1 or more of whole group
      \\.)*$
      """, re.X )

    include_regex_common = '^\s*#(?:include|import)\s*(?:"|<)'
    self._include_start_regex = re.compile( include_regex_common + '$' )
    self._include_regex = re.compile( include_regex_common )


  def AtIncludeStatementStart( self, start_column ):
    return ( InCFamilyFile() and
             self._include_start_regex.match(
               vim.current.line[ :start_column ] ) )


  def ShouldUseNowInner( self, start_column ):
    return ( start_column and ( vim.current.line[ start_column - 1 ] == '/' or
             self.AtIncludeStatementStart( start_column ) ) )


  def SupportedFiletypes( self ):
    return []


  def ComputeCandidates( self, unused_query, start_column ):
    line = vim.current.line[ :start_column ]

    if InCFamilyFile():
      include_match = self._include_regex.search( line )
      if include_match:
        path_dir = line[ include_match.end(): ]
        # We do what GCC does for <> versus "":
        # http://gcc.gnu.org/onlinedocs/cpp/Include-Syntax.html
        include_current_file_dir = '<' not in include_match.group()
        return _GenerateCandidatesForPaths(
          self.GetPathsIncludeCase( path_dir, include_current_file_dir ) )

    path_match = self._path_regex.search( line )
    path_dir = os.path.expanduser( path_match.group() ) if path_match else ''

    return _GenerateCandidatesForPaths( _GetPathsStandardCase( path_dir ) )


  def GetPathsIncludeCase( self, path_dir, include_current_file_dir ):
    paths = []
    include_paths = self._flags.UserIncludePaths( vim.current.buffer.name )

    if include_current_file_dir:
      include_paths.append( os.path.dirname( vim.current.buffer.name ) )

    for include_path in include_paths:
      try:
        relative_paths = os.listdir( os.path.join( include_path, path_dir ) )
      except:
        relative_paths = []

      paths.extend( os.path.join( include_path, path_dir, relative_path ) for
                    relative_path in relative_paths  )

    return sorted( set( paths ) )


def _GetPathsStandardCase( path_dir ):
  if not USE_WORKING_DIR and not path_dir.startswith( '/' ):
    path_dir = os.path.join( os.path.dirname( vim.current.buffer.name ),
                             path_dir )

  try:
    relative_paths = os.listdir( path_dir )
  except:
    relative_paths = []

  return ( os.path.join( path_dir, relative_path )
           for relative_path in relative_paths )


def _GenerateCandidatesForPaths( absolute_paths ):
  seen_basenames = set()
  completion_dicts = []

  for absolute_path in absolute_paths:
    basename = os.path.basename( absolute_path )
    if basename in seen_basenames:
      continue
    seen_basenames.add( basename )

    is_dir = os.path.isdir( absolute_path )
    completion_dicts.append( { 'word': basename,
                               'dup': 1,
                               'menu': '[Dir]' if is_dir else '[File]' } )

  return completion_dicts

#!/usr/bin/env python
#
# Copyright (C) 2013 Stanislav Golovanov <stgolovanov@gmail.com>
#                    Google Inc.
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

import os
import re
from collections import defaultdict

from ycm.completers.completer import Completer
from ycm.completers.cpp.clang_completer import InCFamilyFile
from ycm.completers.cpp.flags import Flags
from ycm.utils import ToUtf8IfNeeded
from ycm.server import responses

EXTRA_INFO_MAP = { 1 : '[File]', 2 : '[Dir]', 3 : '[File&Dir]' }

class FilenameCompleter( Completer ):
  """
  General completer that provides filename and filepath completions.
  """

  def __init__( self, user_options ):
    super( FilenameCompleter, self ).__init__( user_options )
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


  def AtIncludeStatementStart( self, request_data ):
    start_column = request_data[ 'start_column' ]
    current_line = request_data[ 'line_value' ]
    filepath = ToUtf8IfNeeded( request_data[ 'filepath' ] )
    filetypes = request_data[ 'file_data' ][ filepath ][ 'filetypes' ]
    return ( InCFamilyFile( filetypes ) and
             self._include_start_regex.match(
               current_line[ :start_column ] ) )


  def ShouldUseNowInner( self, request_data ):
    start_column = request_data[ 'start_column' ]
    current_line = request_data[ 'line_value' ]
    return ( start_column and ( current_line[ start_column - 1 ] == '/' or
             self.AtIncludeStatementStart( request_data ) ) )


  def SupportedFiletypes( self ):
    return []


  def ComputeCandidatesInner( self, request_data ):
    current_line = request_data[ 'line_value' ]
    start_column = request_data[ 'start_column' ]
    filepath = ToUtf8IfNeeded( request_data[ 'filepath' ] )
    filetypes = request_data[ 'file_data' ][ filepath ][ 'filetypes' ]
    line = current_line[ :start_column ]

    if InCFamilyFile( filetypes ):
      include_match = self._include_regex.search( line )
      if include_match:
        path_dir = line[ include_match.end(): ]
        # We do what GCC does for <> versus "":
        # http://gcc.gnu.org/onlinedocs/cpp/Include-Syntax.html
        include_current_file_dir = '<' not in include_match.group()
        return _GenerateCandidatesForPaths(
          self.GetPathsIncludeCase( path_dir,
                                    include_current_file_dir,
                                    filepath ) )

    path_match = self._path_regex.search( line )
    path_dir = os.path.expanduser( path_match.group() ) if path_match else ''

    return _GenerateCandidatesForPaths(
      _GetPathsStandardCase(
        path_dir,
        self.user_options[ 'filepath_completion_use_working_dir' ],
        filepath ) )


  def GetPathsIncludeCase( self, path_dir, include_current_file_dir, filepath ):
    paths = []
    include_paths = self._flags.UserIncludePaths( filepath )

    if include_current_file_dir:
      include_paths.append( os.path.dirname( filepath ) )

    for include_path in include_paths:
      try:
        relative_paths = os.listdir( os.path.join( include_path, path_dir ) )
      except:
        relative_paths = []

      paths.extend( os.path.join( include_path, path_dir, relative_path ) for
                    relative_path in relative_paths  )

    return sorted( set( paths ) )


def _GetPathsStandardCase( path_dir, use_working_dir, filepath ):
  if not use_working_dir and not path_dir.startswith( '/' ):
    path_dir = os.path.join( os.path.dirname( filepath ),
                             path_dir )

  try:
    relative_paths = os.listdir( path_dir )
  except:
    relative_paths = []

  return ( os.path.join( path_dir, relative_path )
           for relative_path in relative_paths )


def _GenerateCandidatesForPaths( absolute_paths ):
  extra_info = defaultdict(int)
  basenames = []
  for absolute_path in absolute_paths:
    basename = os.path.basename( absolute_path )
    if extra_info[ basename ] == 0:
      basenames.append( basename )
    is_dir = os.path.isdir( absolute_path )
    extra_info[ basename ] |= ( 2 if is_dir else 1 )

  completion_dicts = []
  # Keep original ordering
  for basename in basenames:
    completion_dicts.append(
      responses.BuildCompletionData( basename,
                                     EXTRA_INFO_MAP[ extra_info[ basename ] ] ) )

  return completion_dicts

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

import ycm_core
import os
from ycm import extra_conf_store
from ycm.utils import ToUtf8IfNeeded

NO_EXTRA_CONF_FILENAME_MESSAGE = ( 'No {0} file detected, so no compile flags '
  'are available. Thus no semantic support for C/C++/ObjC/ObjC++. Go READ THE '
  'DOCS *NOW*, DON\'T file a bug report.' ).format(
    extra_conf_store.YCM_EXTRA_CONF_FILENAME )


class Flags( object ):
  """Keeps track of the flags necessary to compile a file.
  The flags are loaded from user-created python files (hereafter referred to as
  'modules') that contain a method FlagsForFile( filename )."""

  def __init__( self ):
    # It's caches all the way down...
    self.flags_for_file = {}
    self.special_clang_flags = _SpecialClangIncludes()
    self.no_extra_conf_file_warning_posted = False


  def FlagsForFile( self, filename, add_special_clang_flags = True ):
    try:
      return self.flags_for_file[ filename ]
    except KeyError:
      module = extra_conf_store.ModuleForSourceFile( filename )
      if not module:
        if not self.no_extra_conf_file_warning_posted:
          self.no_extra_conf_file_warning_posted = True
          raise RuntimeError( NO_EXTRA_CONF_FILENAME_MESSAGE )
        return None

      results = module.FlagsForFile( filename )

      if not results.get( 'flags_ready', True ):
        return None

      flags = list( results[ 'flags' ] )
      if add_special_clang_flags:
        flags += self.special_clang_flags
      sanitized_flags = PrepareFlagsForClang( flags, filename )

      if results[ 'do_cache' ]:
        self.flags_for_file[ filename ] = sanitized_flags
      return sanitized_flags


  def UserIncludePaths( self, filename ):
    flags = self.FlagsForFile( filename, False )
    if not flags:
      return []

    include_paths = []
    path_flags = [ '-isystem', '-I', '-iquote' ]

    next_flag_is_include_path = False
    for flag in flags:
      if next_flag_is_include_path:
        next_flag_is_include_path = False
        include_paths.append( flag )

      for path_flag in path_flags:
        if flag == path_flag:
          next_flag_is_include_path = True
          break

        if flag.startswith( path_flag ):
          path = flag[ len( path_flag ): ]
          include_paths.append( path )
    return [ x for x in include_paths if x ]


  def Clear( self ):
    self.flags_for_file.clear()


def PrepareFlagsForClang( flags, filename ):
  flags = _RemoveUnusedFlags( flags, filename )
  flags = _SanitizeFlags( flags )
  return flags


def _SanitizeFlags( flags ):
  """Drops unsafe flags. Currently these are only -arch flags; they tend to
  crash libclang."""

  sanitized_flags = []
  saw_arch = False
  for i, flag in enumerate( flags ):
    if flag == '-arch':
      saw_arch = True
      continue
    elif flag.startswith( '-arch' ):
      continue
    elif saw_arch:
      saw_arch = False
      continue

    sanitized_flags.append( flag )

  vector = ycm_core.StringVec()
  for flag in sanitized_flags:
    vector.append( ToUtf8IfNeeded( flag ) )
  return vector


def _RemoveUnusedFlags( flags, filename ):
  """Given an iterable object that produces strings (flags for Clang), removes
  the '-c' and '-o' options that Clang does not like to see when it's producing
  completions for a file. Also removes the first flag in the list if it does not
  start with a '-' (it's highly likely to be the compiler name/path)."""

  new_flags = []

  # When flags come from the compile_commands.json file, the first flag is
  # usually the path to the compiler that should be invoked. We want to strip
  # that.
  if not flags[ 0 ].startswith( '-' ):
    flags = flags[ 1: ]

  skip = False
  for flag in flags:
    if skip:
      skip = False
      continue

    if flag == '-c':
      continue

    if flag == '-o':
      skip = True;
      continue

    if flag == filename or os.path.realpath( flag ) == filename:
      continue

    new_flags.append( flag )
  return new_flags


def _SpecialClangIncludes():
  libclang_dir = os.path.dirname( ycm_core.__file__ )
  path_to_includes = os.path.join( libclang_dir, 'clang_includes' )
  return [ '-I', path_to_includes ]



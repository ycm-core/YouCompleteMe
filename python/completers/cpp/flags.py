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
import vimsupport
import extra_conf_store

NO_EXTRA_CONF_FILENAME_MESSAGE = ('No {0} file detected, so no compile flags '
  'are available. Thus no semantic support for C/C++/ObjC/ObjC++. See the '
  'docs for details.').format( extra_conf_store.YCM_EXTRA_CONF_FILENAME )

class Flags( object ):
  """Keeps track of the flags necessary to compile a file.
  The flags are loaded from user-created python files (hereafter referred to as
  'modules') that contain a method FlagsForFile( filename )."""

  def __init__( self ):
    # It's caches all the way down...
    self.flags_for_file = {}
    self.special_clang_flags = _SpecialClangIncludes()
    self.no_extra_conf_file_warning_posted = False


  def FlagsForFile( self, filename ):
    try:
      return self.flags_for_file[ filename ]
    except KeyError:
      module = extra_conf_store.ModuleForSourceFile( filename )
      if not module:
        if not self.no_extra_conf_file_warning_posted:
          vimsupport.PostVimMessage( NO_EXTRA_CONF_FILENAME_MESSAGE )
          self.no_extra_conf_file_warning_posted = True
        return None

      results = module.FlagsForFile( filename )

      if not results.get( 'flags_ready', True ):
        return None

      results[ 'flags' ] += self.special_clang_flags
      sanitized_flags = _SanitizeFlags( results[ 'flags' ] )

      if results[ 'do_cache' ]:
        self.flags_for_file[ filename ] = sanitized_flags
      return sanitized_flags


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
    vector.append( flag )
  return vector


def _SpecialClangIncludes():
  libclang_dir = os.path.dirname( ycm_core.__file__ )
  path_to_includes = os.path.join( libclang_dir, 'clang_includes' )
  return [ '-I', path_to_includes ]



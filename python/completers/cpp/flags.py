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

import imp
import os
import ycm_core
import random
import string
import sys
import vimsupport

YCM_EXTRA_CONF_FILENAME = '.ycm_extra_conf.py'
NO_OPTIONS_FILENAME_MESSAGE = ('No {0} file detected, so no compile flags '
  'are available. Thus no semantic support for C/C++/ObjC/ObjC++.').format(
    YCM_EXTRA_CONF_FILENAME )
GLOBAL_YCM_EXTRA_CONF_FILE = vimsupport.GetVariableValue(
  "g:ycm_global_ycm_extra_conf" )

class Flags( object ):
  def __init__( self ):
    # It's caches all the way down...
    self.flags_for_file = {}
    self.flags_module_for_file = {}
    self.flags_module_for_flags_module_file = {}
    self.special_clang_flags = _SpecialClangIncludes()


  def FlagsForFile( self, filename ):
    try:
      return self.flags_for_file[ filename ]
    except KeyError:
      flags_module = self._FlagsModuleForFile( filename )
      if not flags_module:
        vimsupport.PostVimMessage( NO_OPTIONS_FILENAME_MESSAGE )
        return None

      results = flags_module.FlagsForFile( filename )

      if not results.get( 'flags_ready', True ):
        return None

      results[ 'flags' ] += self.special_clang_flags
      sanitized_flags = _SanitizeFlags( results[ 'flags' ] )

      if results[ 'do_cache' ]:
        self.flags_for_file[ filename ] = sanitized_flags
      return sanitized_flags


  def _FlagsModuleForFile( self, filename ):
    try:
      return self.flags_module_for_file[ filename ]
    except KeyError:
      flags_module_file = _FlagsModuleSourceFileForFile( filename )
      if not flags_module_file:
        return None

      try:
        flags_module = self.flags_module_for_flags_module_file[
          flags_module_file ]
      except KeyError:
        sys.path.append( _DirectoryOfThisScript() )
        flags_module = imp.load_source( _RandomName(), flags_module_file )
        del sys.path[ -1 ]

        self.flags_module_for_flags_module_file[
          flags_module_file ] = flags_module

      self.flags_module_for_file[ filename ] = flags_module
      return flags_module



def _FlagsModuleSourceFileForFile( filename ):
  """For a given filename, finds its nearest YCM_EXTRA_CONF_FILENAME file that
  will compute the flags necessary to compile the file. Returns None if no
  YCM_EXTRA_CONF_FILENAME file could be found. Uses the global ycm_extra_conf
  file if one is set."""

  if ( GLOBAL_YCM_EXTRA_CONF_FILE and
       os.path.exists( GLOBAL_YCM_EXTRA_CONF_FILE ) ):
    return GLOBAL_YCM_EXTRA_CONF_FILE

  parent_folder = os.path.dirname( filename )
  old_parent_folder = ''

  while True:
    current_file = os.path.join( parent_folder, YCM_EXTRA_CONF_FILENAME )
    if os.path.exists( current_file ):
      return current_file

    old_parent_folder = parent_folder
    parent_folder = os.path.dirname( parent_folder )

    if parent_folder == old_parent_folder:
      return None


def _RandomName():
  """Generates a random module name."""
  return ''.join( random.choice( string.ascii_lowercase ) for x in range( 15 ) )


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


def _DirectoryOfThisScript():
  return os.path.dirname( os.path.abspath( __file__ ) )

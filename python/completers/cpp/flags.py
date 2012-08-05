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

CLANG_OPTIONS_FILENAME = '.ycm_clang_options.py'

class Flags( object ):
  def __init__( self ):
    # It's caches all the way down...
    self.flags_for_file = {}
    self.flags_module_for_file = {}
    self.flags_module_for_flags_module_file = {}


  def FlagsForFile( self, filename ):
    try:
      return self.flags_for_file[ filename ]
    except KeyError:
      flags_module = self.FlagsModuleForFile( filename )
      if not flags_module:
        return ycm_core.StringVec()

      results = flags_module.FlagsForFile( filename )
      sanitized_flags = _SanitizeFlags( results[ 'flags' ] )

      if results[ 'do_cache' ]:
        self.flags_for_file[ filename ] = sanitized_flags
      return sanitized_flags


  def FlagsModuleForFile( self, filename ):
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
        flags_module = imp.load_source( _RandomName(), flags_module_file )
        self.flags_module_for_flags_module_file[
          flags_module_file ] = flags_module

      self.flags_module_for_file[ filename ] = flags_module
      return flags_module


def _FlagsModuleSourceFileForFile( filename ):
  """For a given filename, finds its nearest CLANG_OPTIONS_FILENAME file that
  will compute the flags necessary to compile the file. Returns None if no
  CLANG_OPTIONS_FILENAME file could be found."""

  parent_folder = os.path.dirname( filename )
  old_parent_folder = ''

  while True:
    current_file = os.path.join( parent_folder, CLANG_OPTIONS_FILENAME )
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

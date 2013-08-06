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

# NOTE: This module is used as a Singleton

import os
import imp
import random
import string
import sys
import vim
from ycm import vimsupport
from fnmatch import fnmatch

# Constants
YCM_EXTRA_CONF_FILENAME = '.ycm_extra_conf.py'
CONFIRM_CONF_FILE_MESSAGE = ('Found {0}. Load? \n\n(Question can be turned '
                             'off with options, see YCM docs)')
GLOBAL_YCM_EXTRA_CONF_FILE = os.path.expanduser(
    vimsupport.GetVariableValue( "g:ycm_global_ycm_extra_conf" )
)

# Singleton variables
_module_for_module_file = {}
_module_file_for_source_file = {}


def ModuleForSourceFile( filename ):
  return _Load( ModuleFileForSourceFile( filename ) )


def ModuleFileForSourceFile( filename ):
  """This will try all files returned by _ExtraConfModuleSourceFilesForFile in
  order and return the filename of the first module that was allowed to load.
  If no module was found or allowed to load, None is returned."""

  if not filename in _module_file_for_source_file:
    for module_file in _ExtraConfModuleSourceFilesForFile( filename ):
      if _Load( module_file ):
        _module_file_for_source_file[ filename ] = module_file
        break

  return _module_file_for_source_file.setdefault( filename )


def CallExtraConfYcmCorePreloadIfExists():
  _CallExtraConfMethod( 'YcmCorePreload' )


def CallExtraConfVimCloseIfExists():
  _CallExtraConfMethod( 'VimClose' )


def _CallExtraConfMethod( function_name ):
  vim_current_working_directory = vim.eval( 'getcwd()' )
  path_to_dummy = os.path.join( vim_current_working_directory, 'DUMMY_FILE' )
  module = ModuleForSourceFile( path_to_dummy )
  if not module or not hasattr( module, function_name ):
    return
  getattr( module, function_name )()


def _Disable( module_file ):
  """Disables the loading of a module for the current session."""
  _module_for_module_file[ module_file ] = None


def _ShouldLoad( module_file ):
  """Checks if a module is safe to be loaded. By default this will try to
  decide using a white-/blacklist and ask the user for confirmation as a
  fallback."""

  if ( module_file == GLOBAL_YCM_EXTRA_CONF_FILE or
        not vimsupport.GetBoolValue( 'g:ycm_confirm_extra_conf' ) ):
    return True

  globlist = vimsupport.GetVariableValue( 'g:ycm_extra_conf_globlist' )
  for glob in globlist:
    is_blacklisted = glob[0] == '!'
    if _MatchesGlobPattern( module_file, glob.lstrip('!') ):
      return not is_blacklisted

  return vimsupport.Confirm( CONFIRM_CONF_FILE_MESSAGE.format( module_file ) )


def _Load( module_file, force = False ):
  """Load and return the module contained in a file.
  Using force = True the module will be loaded regardless
  of the criteria in _ShouldLoad.
  This will return None if the module was not allowed to be loaded."""

  if not module_file:
    return None

  if not force:
    if module_file in _module_for_module_file:
      return _module_for_module_file[ module_file ]

    if not _ShouldLoad( module_file ):
      return _Disable( module_file )

  # This has to be here because a long time ago, the ycm_extra_conf.py files
  # used to import clang_helpers.py from the cpp folder. This is not needed
  # anymore, but there are a lot of old ycm_extra_conf.py files that we don't
  # want to break.
  sys.path.insert( 0, _PathToCppCompleterFolder() )
  module = imp.load_source( _RandomName(), module_file )
  del sys.path[ 0 ]

  _module_for_module_file[ module_file ] = module
  return module


def _MatchesGlobPattern( filename, glob ):
  """Returns true if a filename matches a given pattern. A '~' in glob will be
  expanded to the home directory and checking will be performed using absolute
  paths. See the documentation of fnmatch for the supported patterns."""

  abspath = os.path.abspath( filename )
  return fnmatch( abspath, os.path.abspath( os.path.expanduser( glob ) ) )


def _ExtraConfModuleSourceFilesForFile( filename ):
  """For a given filename, search all parent folders for YCM_EXTRA_CONF_FILENAME
  files that will compute the flags necessary to compile the file.
  If GLOBAL_YCM_EXTRA_CONF_FILE exists it is returned as a fallback."""

  for folder in _PathsToAllParentFolders( filename ):
    candidate = os.path.join( folder, YCM_EXTRA_CONF_FILENAME )
    if os.path.exists( candidate ):
      yield candidate
  if ( GLOBAL_YCM_EXTRA_CONF_FILE
       and os.path.exists( GLOBAL_YCM_EXTRA_CONF_FILE ) ):
    yield GLOBAL_YCM_EXTRA_CONF_FILE


def _PathsToAllParentFolders( filename ):
  """Build a list of all parent folders of a file.
  The neares files will be returned first.
  Example: _PathsToAllParentFolders( '/home/user/projects/test.c' )
    [ '/home/user/projects', '/home/user', '/home', '/' ]"""

  parent_folders = os.path.abspath(
    os.path.dirname( filename ) ).split( os.path.sep )
  if not parent_folders[0]:
    parent_folders[0] = os.path.sep
  parent_folders = [ os.path.join( *parent_folders[:i + 1] )
                     for i in xrange( len( parent_folders ) ) ]
  return reversed( parent_folders )


def _PathToCppCompleterFolder():
  """Returns the path to the 'cpp' completer folder. This is necessary
  because ycm_extra_conf files need it on the path."""
  return os.path.join( _DirectoryOfThisScript(), 'completers', 'cpp' )


def _DirectoryOfThisScript():
  return os.path.dirname( os.path.abspath( __file__ ) )


def _RandomName():
  """Generates a random module name."""
  return ''.join( random.choice( string.ascii_lowercase ) for x in range( 15 ) )

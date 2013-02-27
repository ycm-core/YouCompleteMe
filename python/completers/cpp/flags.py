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
from fnmatch import fnmatch

YCM_EXTRA_CONF_FILENAME = '.ycm_extra_conf.py'
NO_EXTRA_CONF_FILENAME_MESSAGE = ('No {0} file detected, so no compile flags '
  'are available. Thus no semantic support for C/C++/ObjC/ObjC++. See the '
  'docs for details.').format( YCM_EXTRA_CONF_FILENAME )
CONFIRM_CONF_FILE_MESSAGE = 'Found {0}. Load?'
GLOBLIST_WRONG_TYPE_FOR_VARIABLE = '{0} needs to be a list of strings.'
GLOBAL_YCM_EXTRA_CONF_FILE = os.path.expanduser(
    vimsupport.GetVariableValue( "g:ycm_global_ycm_extra_conf" )
)

class Flags( object ):
  """Keeps track of the flags necessary to compile a file.
  The flags are loaded from user-created python files (hereafter referred to as
  'modules') that contain a method FlagsForFile( filename )."""

  def __init__( self ):
    # It's caches all the way down...
    self.flags_for_file = {}
    self.module_for_file = {}
    self.modules = FlagsModules()
    self.special_clang_flags = _SpecialClangIncludes()
    self.no_extra_conf_file_warning_posted = False

  def ModuleForFile( self, filename ):
    """This will try all files returned by _FlagsModuleSourceFilesForFile in
    order and return the filename of the first module that was allowed to load.
    If no module was found or allowed to load, None is returned."""

    if not self.module_for_file.has_key( filename ):
      for flags_module_file in _FlagsModuleSourceFilesForFile( filename ):
        if self.modules.Load( flags_module_file ):
          self.module_for_file[ filename ] = flags_module_file
          break

    return self.module_for_file.setdefault( filename )

  def FlagsForFile( self, filename ):
    try:
      return self.flags_for_file[ filename ]
    except KeyError:
      module_file = self.ModuleForFile( filename )
      if not module_file:
        if not self.no_extra_conf_file_warning_posted:
          vimsupport.PostVimMessage( NO_EXTRA_CONF_FILENAME_MESSAGE )
          self.no_extra_conf_file_warning_posted = True
        return None

      results = self.modules[ module_file ].FlagsForFile( filename )

      if not results.get( 'flags_ready', True ):
        return None

      results[ 'flags' ] += self.special_clang_flags
      sanitized_flags = _SanitizeFlags( results[ 'flags' ] )

      if results[ 'do_cache' ]:
        self.flags_for_file[ filename ] = sanitized_flags
      return sanitized_flags

  def ReloadModule( self, module_file ):
    """Reloads a module file cleaning the flags cache for all files
    associated with that module. Returns False if reloading failed
    (for example due to the model not being loaded in the first place)."""

    module_file = os.path.abspath(module_file)
    if self.modules.Reload( module_file ):
      for filename, module in self.module_for_file.iteritems():
        if module == module_file:
          del self.flags_for_file[ filename ]
      return True
    return False


class FlagsModules( object ):
  """Keeps track of modules.
  Modules are loaded on-demand and cached in self.modules for quick access."""

  def __init__( self ):
    self.modules = {}

  def Disable( self, module_file ):
    """Disables the loading of a module for the current session."""
    self.modules[ module_file ] = None

  @staticmethod
  def ShouldLoad( module_file ):
    """Checks if a module is safe to be loaded.
    By default this will ask the user for confirmation."""

    if module_file == GLOBAL_YCM_EXTRA_CONF_FILE:
      return True

    glob = CheckGlobList( 'g:ycm_extra_conf_globlist', module_file )
    if glob < 0:
      return False
    elif glob > 0:
      return True
    elif ( vimsupport.GetBoolValue( 'g:ycm_confirm_extra_conf' ) and
           not vimsupport.Confirm(
             CONFIRM_CONF_FILE_MESSAGE.format( module_file ) ) ):
      return False
    return True

  def Load( self, module_file, force = False ):
    """Load and return the module contained in a file.
    Using force = True the module will be loaded regardless
    of the criteria in ShouldLoad.
    This will return None if the module was not allowed to be loaded."""

    if not force:
      if self.modules.has_key( module_file ):
        return self.modules[ module_file ]

      if not self.ShouldLoad( module_file ):
        return self.Disable( module_file )

    sys.path.insert( 0, _DirectoryOfThisScript() )
    module = imp.load_source( _RandomName(), module_file )
    del sys.path[ 0 ]

    self.modules[ module_file ] = module
    return module

  def Reload( self, module_file ):
    """Reloads the given module. If it has not been loaded yet does nothing.
    Note that the module will not be subject to the loading criteria again."""

    if self.modules.get( module_file ):
      return self.Load( module_file, force = True )

  def __getitem__( self, key ):
    return self.Load( key )


def _FlagsModuleSourceFilesForFile( filename ):
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


def CheckGlobList( variable, filename ):
  abspath = os.path.abspath( filename )
  if vimsupport.GetVariableType( variable ) != 'List':
    if getattr(CheckGlobList, "no_type_warning_posted", True):
      vimsupport.PostVimMessage(
        GLOBLIST_WRONG_TYPE_FOR_VARIABLE.format( variable ) )
      CheckGlobList.no_type_warning_posted = False
    return 0

  globlist = vimsupport.GetVariableValue( variable )
  for glob in globlist:
    blacklist = glob[0] == '!'
    glob = glob.lstrip('!')
    if fnmatch( abspath, os.path.abspath( os.path.expanduser( glob ) ) ):
      return -1 if blacklist else 1
  return 0

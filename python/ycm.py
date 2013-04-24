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
import sys
import vimsupport
import vim
import ycm_utils as utils

try:
  import ycm_core
except ImportError as e:
  vimsupport.PostVimMessage(
    'Error importing ycm_core. Are you sure you have placed a version 3.2+ '
    'libclang.[so|dll|dylib] in folder "{0}"? See the Installation Guide in '
    'the docs. Full error: {1}'.format(
      os.path.dirname( os.path.abspath( __file__ ) ), str( e ) ) )


from completers.all.omni_completer import OmniCompleter
from completers.general.general_completer_store import GeneralCompleterStore

FILETYPE_SPECIFIC_COMPLETION_TO_DISABLE = vim.eval(
  'g:ycm_filetype_specific_completion_to_disable' )


class YouCompleteMe( object ):
  def __init__( self ):
    self.gencomp = GeneralCompleterStore()
    self.omnicomp = OmniCompleter()
    self.filetype_completers = {}


  def GetGeneralCompleter( self ):
    return self.gencomp


  def GetOmniCompleter( self ):
    return self.omnicomp


  def GetFiletypeCompleter( self ):
    filetypes = vimsupport.CurrentFiletypes()

    completers = [self.GetFiletypeCompleterForFiletype( filetype )
        for filetype in filetypes ]

    if not completers:
      return None

    # Try to find a native completer first
    for completer in completers:
      if completer and completer is not self.omnicomp:
        return completer

    # Return the omni completer for the first filetype
    return completers[0]


  def GetFiletypeCompleterForFiletype( self, filetype ):
    try:
      return self.filetype_completers[ filetype ]
    except KeyError:
      pass

    module_path = _PathToFiletypeCompleterPluginLoader( filetype )

    completer = None
    supported_filetypes = [ filetype ]
    if os.path.exists( module_path ):

      sys.path.insert( 0, os.path.dirname( module_path ) )
      module = imp.load_source( filetype, module_path )
      del sys.path[ 0 ]

      completer = module.GetCompleter()
      if completer:
        supported_filetypes.extend( completer.SupportedFiletypes() )
    else:
      completer = self.omnicomp

    for supported_filetype in supported_filetypes:
      self.filetype_completers[ supported_filetype ] = completer
    return completer


  def ShouldUseGeneralCompleter( self, start_column ):
    return self.gencomp.ShouldUseNow( start_column )


  def ShouldUseFiletypeCompleter( self, start_column ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().ShouldUseNow(
        start_column )
    return False


  def NativeFiletypeCompletionAvailable( self ):
    completer = self.GetFiletypeCompleter()
    return bool( completer ) and completer is not self.omnicomp


  def FiletypeCompletionAvailable( self ):
    return bool( self.GetFiletypeCompleter() )


  def NativeFiletypeCompletionUsable( self ):
    return ( _CurrentFiletypeCompletionEnabled() and
             self.NativeFiletypeCompletionAvailable() )


  def FiletypeCompletionUsable( self ):
    return ( _CurrentFiletypeCompletionEnabled() and
             self.FiletypeCompletionAvailable() )


  def OnFileReadyToParse( self ):
    self.gencomp.OnFileReadyToParse()

    if self.FiletypeCompletionUsable():
      self.GetFiletypeCompleter().OnFileReadyToParse()


  def OnBufferDelete( self, deleted_buffer_file ):
    self.gencomp.OnBufferDelete( deleted_buffer_file )

    if self.FiletypeCompletionUsable():
      self.GetFiletypeCompleter().OnBufferDelete( deleted_buffer_file )


  def OnBufferVisit( self ):
    self.gencomp.OnBufferVisit()

    if self.FiletypeCompletionUsable():
      self.GetFiletypeCompleter().OnBufferVisit()


  def OnInsertLeave( self ):
    self.gencomp.OnInsertLeave()

    if self.FiletypeCompletionUsable():
      self.GetFiletypeCompleter().OnInsertLeave()


  def DiagnosticsForCurrentFileReady( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().DiagnosticsForCurrentFileReady()
    return False


  def GetDiagnosticsForCurrentFile( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().GetDiagnosticsForCurrentFile()
    return []


  def ShowDetailedDiagnostic( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().ShowDetailedDiagnostic()


  def GettingCompletions( self ):
    if self.FiletypeCompletionUsable():
      return self.GetFiletypeCompleter().GettingCompletions()
    return False


  def OnCurrentIdentifierFinished( self ):
    self.gencomp.OnCurrentIdentifierFinished()

    if self.FiletypeCompletionUsable():
      self.GetFiletypeCompleter().OnCurrentIdentifierFinished()


  def DebugInfo( self ):
    completers = set( self.filetype_completers.values() )
    completers.add( self.gencomp )
    output = []
    for completer in completers:
      if not completer:
        continue
      debug = completer.DebugInfo()
      if debug:
        output.append( debug )

    has_clang_support = ycm_core.HasClangSupport()
    output.append( 'Has Clang support compiled in: {0}'.format(
      has_clang_support ) )

    if has_clang_support:
      output.append( ycm_core.ClangVersion() )

    return '\n'.join( output )


def _CurrentFiletypeCompletionEnabled():
  filetypes = vimsupport.CurrentFiletypes()
  return not all([ x in FILETYPE_SPECIFIC_COMPLETION_TO_DISABLE
                   for x in filetypes ])


def _PathToCompletersFolder():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, 'completers' )


def _PathToFiletypeCompleterPluginLoader( filetype ):
  return os.path.join( _PathToCompletersFolder(), filetype, 'hook.py' )


def CompletionStartColumn():
  """Returns the 0-based index where the completion string should start. So if
  the user enters:
    foo.bar^
  with the cursor being at the location of the caret, then the starting column
  would be the index of the letter 'b'.
  """

  line = vim.current.line
  start_column = vimsupport.CurrentColumn()

  while start_column > 0 and utils.IsIdentifierChar( line[ start_column - 1 ] ):
    start_column -= 1
  return start_column


def CurrentIdentifierFinished():
  current_column = vimsupport.CurrentColumn()
  previous_char_index = current_column - 1
  if previous_char_index < 0:
    return True
  line = vim.current.line
  try:
    previous_char = line[ previous_char_index ]
  except IndexError:
    return False

  if utils.IsIdentifierChar( previous_char ):
    return False

  if ( not utils.IsIdentifierChar( previous_char ) and
       previous_char_index > 0 and
       utils.IsIdentifierChar( line[ previous_char_index - 1 ] ) ):
    return True
  else:
    return line[ : current_column ].isspace()


COMPATIBLE_WITH_CORE_VERSION = 3

def CompatibleWithYcmCore():
  try:
    current_core_version = ycm_core.YcmCoreVersion()
  except AttributeError:
    return False

  return current_core_version == COMPATIBLE_WITH_CORE_VERSION


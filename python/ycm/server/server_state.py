#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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
from ycm import extra_conf_store
from ycm.completers.general.general_completer_store import GeneralCompleterStore


class ServerState( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    self._filetype_completers = {}
    self._gencomp = GeneralCompleterStore( self._user_options )
    extra_conf_store.CallExtraConfYcmCorePreloadIfExists()


  @property
  def user_options( self ):
    return self._user_options


  def Shutdown( self ):
    for completer in self._filetype_completers.itervalues():
      completer.Shutdown()

    self._gencomp.Shutdown()
    extra_conf_store.Shutdown()



  def _GetFiletypeCompleterForFiletype( self, filetype ):
    try:
      return self._filetype_completers[ filetype ]
    except KeyError:
      pass

    module_path = _PathToFiletypeCompleterPluginLoader( filetype )

    completer = None
    supported_filetypes = [ filetype ]
    if os.path.exists( module_path ):
      module = imp.load_source( filetype, module_path )
      completer = module.GetCompleter( self._user_options )
      if completer:
        supported_filetypes.extend( completer.SupportedFiletypes() )

    for supported_filetype in supported_filetypes:
      self._filetype_completers[ supported_filetype ] = completer
    return completer


  def GetFiletypeCompleter( self, current_filetypes ):
    completers = [ self._GetFiletypeCompleterForFiletype( filetype )
                   for filetype in current_filetypes ]

    for completer in completers:
      if completer:
        return completer

    return None


  def FiletypeCompletionAvailable( self, filetypes ):
    return bool( self.GetFiletypeCompleter( filetypes ) )


  def FiletypeCompletionUsable( self, filetypes ):
    return ( self.CurrentFiletypeCompletionEnabled( filetypes ) and
             self.FiletypeCompletionAvailable( filetypes ) )


  def ShouldUseGeneralCompleter( self, request_data ):
    return self._gencomp.ShouldUseNow( request_data )


  def ShouldUseFiletypeCompleter( self, request_data ):
    filetypes = request_data[ 'filetypes' ]
    if self.FiletypeCompletionUsable( filetypes ):
      return self.GetFiletypeCompleter( filetypes ).ShouldUseNow( request_data )
    return False


  def GetGeneralCompleter( self ):
    return self._gencomp


  def CurrentFiletypeCompletionEnabled( self, current_filetypes ):
    filetype_to_disable = self._user_options[
        'filetype_specific_completion_to_disable' ]
    return not all([ x in filetype_to_disable for x in current_filetypes ])



def _PathToCompletersFolder():
  dir_of_current_script = os.path.dirname( os.path.abspath( __file__ ) )
  return os.path.join( dir_of_current_script, '..', 'completers' )


def _PathToFiletypeCompleterPluginLoader( filetype ):
  return os.path.join( _PathToCompletersFolder(), filetype, 'hook.py' )



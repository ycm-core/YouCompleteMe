#!/usr/bin/env python
#
# Copyright (C) 2013  Google Inc.
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
from ycm.utils import ForceSemanticCompletion
from ycm.completers.general.general_completer_store import GeneralCompleterStore
from ycm.completers.completer_utils import PathToFiletypeCompleterPluginLoader


class ServerState( object ):
  def __init__( self, user_options ):
    self._user_options = user_options
    self._filetype_completers = {}
    self._gencomp = GeneralCompleterStore( self._user_options )


  @property
  def user_options( self ):
    return self._user_options


  def Shutdown( self ):
    for completer in self._filetype_completers.itervalues():
      if completer:
        completer.Shutdown()

    self._gencomp.Shutdown()


  def _GetFiletypeCompleterForFiletype( self, filetype ):
    try:
      return self._filetype_completers[ filetype ]
    except KeyError:
      pass

    module_path = PathToFiletypeCompleterPluginLoader( filetype )
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

    raise ValueError( 'No semantic completer exists for filetypes: {0}'.format(
        current_filetypes ) )


  def FiletypeCompletionAvailable( self, filetypes ):
    try:
      self.GetFiletypeCompleter( filetypes )
      return True
    except:
      return False


  def FiletypeCompletionUsable( self, filetypes ):
    return ( self.CurrentFiletypeCompletionEnabled( filetypes ) and
             self.FiletypeCompletionAvailable( filetypes ) )


  def ShouldUseGeneralCompleter( self, request_data ):
    return self._gencomp.ShouldUseNow( request_data )


  def ShouldUseFiletypeCompleter( self, request_data ):
    filetypes = request_data[ 'filetypes' ]
    if self.FiletypeCompletionUsable( filetypes ):
      return ( ForceSemanticCompletion( request_data ) or
               self.GetFiletypeCompleter( filetypes ).ShouldUseNow(
                 request_data ) )
    return False


  def GetGeneralCompleter( self ):
    return self._gencomp


  def CurrentFiletypeCompletionEnabled( self, current_filetypes ):
    filetype_to_disable = self._user_options[
        'filetype_specific_completion_to_disable' ]
    return not all([ x in filetype_to_disable for x in current_filetypes ])


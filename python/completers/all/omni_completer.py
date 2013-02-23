#!/usr/bin/env python
#
# Copyright (C) 2011, 2012, 2013  Strahinja Val Markovic  <val@markovic.io>
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

import vim
import vimsupport
from completers.completer import Completer

class OmniCompleter( Completer ):
  def __init__( self ):
    super( OmniCompleter, self ).__init__()
    self.omnifunc = None
    self.stored_candidates = None


  def SupportedFiletypes( self ):
    return []


  def ShouldUseNowInner( self, start_column ):
    if not self.omnifunc:
      return False
    return super( OmniCompleter, self ).ShouldUseNowInner( start_column )


  def CandidatesForQueryAsyncInner( self, query ):
    if not self.omnifunc:
      self.stored_candidates = None
      return

    return_value = vim.eval( self.omnifunc + '(1,"")' )
    if return_value < 0:
      self.stored_candidates = None
      return

    omnifunc_call = [ self.omnifunc,
                      "(0,'",
                      vimsupport.EscapeForVim( query ),
                      "')" ]

    items = vim.eval( ''.join( omnifunc_call ) )
    if hasattr( items, 'words' ):
      items = item.words
    self.stored_candidates = filter( bool, items )


  def AsyncCandidateRequestReadyInner( self ):
    return True


  def OnFileReadyToParse( self ):
    self.omnifunc = vim.eval( '&omnifunc' )


  def CandidatesFromStoredRequestInner( self ):
    return self.stored_candidates


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
from ycm import vimsupport
from ycm.completers.completer import Completer

OMNIFUNC_RETURNED_BAD_VALUE = 'Omnifunc returned bad value to YCM!'
OMNIFUNC_NOT_LIST = ( 'Omnifunc did not return a list or a dict with a "words" '
                     ' list when expected.' )

class OmniCompleter( Completer ):
  def __init__( self, user_options ):
    super( OmniCompleter, self ).__init__( user_options )
    self.omnifunc = None
    self.stored_candidates = None


  def SupportedFiletypes( self ):
    return []


  def ShouldUseCache( self ):
    return bool( self.user_options[ 'cache_omnifunc' ] )


  def ShouldUseNow( self, start_column, current_line ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ShouldUseNow( start_column,
                                                        current_line )
    return self.ShouldUseNowInner( start_column, current_line )


  def ShouldUseNowInner( self, start_column, current_line ):
    if not self.omnifunc:
      return False
    return super( OmniCompleter, self ).ShouldUseNowInner( start_column,
                                                           current_line )


  def CandidatesForQueryAsync( self, query, unused_start_column ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).CandidatesForQueryAsync(
          query, unused_start_column )
    else:
      return self.CandidatesForQueryAsyncInner( query, unused_start_column )


  def CandidatesForQueryAsyncInner( self, query, unused_start_column ):
    if not self.omnifunc:
      self.stored_candidates = None
      return

    try:
      return_value = int( vim.eval( self.omnifunc + '(1,"")' ) )
      if return_value < 0:
        self.stored_candidates = None
        return

      omnifunc_call = [ self.omnifunc,
                        "(0,'",
                        vimsupport.EscapeForVim( query ),
                        "')" ]

      items = vim.eval( ''.join( omnifunc_call ) )

      if 'words' in items:
        items = items['words']
      if not hasattr( items, '__iter__' ):
        raise TypeError( OMNIFUNC_NOT_LIST )

      self.stored_candidates = filter( bool, items )
    except (TypeError, ValueError) as error:
      vimsupport.PostVimMessage(
        OMNIFUNC_RETURNED_BAD_VALUE + ' ' + str( error ) )
      self.stored_candidates = None
      return



  def AsyncCandidateRequestReadyInner( self ):
    return True


  def OnFileReadyToParse( self ):
    self.omnifunc = vim.eval( '&omnifunc' )


  def CandidatesFromStoredRequest( self ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).CandidatesFromStoredRequest()
    else:
      return self.CandidatesFromStoredRequestInner()


  def CandidatesFromStoredRequestInner( self ):
    return self.stored_candidates if self.stored_candidates else []


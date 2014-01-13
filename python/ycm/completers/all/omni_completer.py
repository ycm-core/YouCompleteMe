#!/usr/bin/env python
#
# Copyright (C) 2011, 2012, 2013  Google Inc.
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
from ycm import base
from ycm.completers.completer import Completer
from ycm.client.base_request import BuildRequestData

OMNIFUNC_RETURNED_BAD_VALUE = 'Omnifunc returned bad value to YCM!'
OMNIFUNC_NOT_LIST = ( 'Omnifunc did not return a list or a dict with a "words" '
                     ' list when expected.' )

class OmniCompleter( Completer ):
  def __init__( self, user_options ):
    super( OmniCompleter, self ).__init__( user_options )
    self._omnifunc = None


  def SupportedFiletypes( self ):
    return []


  def ShouldUseCache( self ):
    return bool( self.user_options[ 'cache_omnifunc' ] )


  # We let the caller call this without passing in request_data. This is useful
  # for figuring out should we even be preparing the "real" request_data in
  # omni_completion_request. The real request_data is much bigger and takes
  # longer to prepare, and we want to avoid creating it twice.
  def ShouldUseNow( self, request_data = None ):
    if not self._omnifunc:
      return False

    if not request_data:
      request_data = _BuildRequestDataSubstitute()

    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ShouldUseNow( request_data )
    return self.ShouldUseNowInner( request_data )


  def ShouldUseNowInner( self, request_data ):
    if not self._omnifunc:
      return False
    return super( OmniCompleter, self ).ShouldUseNowInner( request_data )


  def ComputeCandidates( self, request_data ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ComputeCandidates(
        request_data )
    else:
      if self.ShouldUseNowInner( request_data ):
        return self.ComputeCandidatesInner( request_data )
      return []


  def ComputeCandidatesInner( self, request_data ):
    if not self._omnifunc:
      return []

    try:
      return_value = int( vim.eval( self._omnifunc + '(1,"")' ) )
      if return_value < 0:
        return []

      omnifunc_call = [ self._omnifunc,
                        "(0,'",
                        vimsupport.EscapeForVim( request_data[ 'query' ] ),
                        "')" ]

      items = vim.eval( ''.join( omnifunc_call ) )

      if 'words' in items:
        items = items[ 'words' ]
      if not hasattr( items, '__iter__' ):
        raise TypeError( OMNIFUNC_NOT_LIST )

      return filter( bool, items )
    except ( TypeError, ValueError, vim.error ) as error:
      vimsupport.PostVimMessage(
        OMNIFUNC_RETURNED_BAD_VALUE + ' ' + str( error ) )
      return []


  def OnFileReadyToParse( self, request_data ):
    self._omnifunc = vim.eval( '&omnifunc' )


def _BuildRequestDataSubstitute():
  data = BuildRequestData( include_buffer_data = False )
  data[ 'start_column' ] = base.CompletionStartColumn()
  return data



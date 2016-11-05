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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import vim
from ycm import vimsupport
from ycmd import utils
from ycmd.completers.completer import Completer
from ycm.client.base_request import BaseRequest, HandleServerException

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


  def ShouldUseNow( self, request_data ):
    if not self._omnifunc:
      return False

    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ShouldUseNow( request_data )
    return self.ShouldUseNowInner( request_data )


  def ShouldUseNowInner( self, request_data ):
    if not self._omnifunc:
      return False
    return super( OmniCompleter, self ).ShouldUseNowInner( request_data )


  def ComputeCandidates( self, request_data ):
    if self.ShouldUseCache():
      return super( OmniCompleter, self ).ComputeCandidates( request_data )
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
        # FIXME: Technically, if the return is -1 we should raise an error
        return []

      omnifunc_call = [ self._omnifunc,
                        "(0,'",
                        vimsupport.EscapeForVim( request_data[ 'query' ] ),
                        "')" ]

      items = vim.eval( ''.join( omnifunc_call ) )

      if isinstance( items, dict ) and 'words' in items:
        items = items[ 'words' ]

      if not hasattr( items, '__iter__' ):
        raise TypeError( OMNIFUNC_NOT_LIST )

      return list( filter( bool, items ) )

    except ( TypeError, ValueError, vim.error ) as error:
      vimsupport.PostVimMessage(
        OMNIFUNC_RETURNED_BAD_VALUE + ' ' + str( error ) )
      return []


  def OnFileReadyToParse( self, request_data ):
    self._omnifunc = utils.ToUnicode( vim.eval( '&omnifunc' ) )


  def FilterAndSortCandidatesInner( self, candidates, sort_property, query ):
    request_data = {
      'candidates': candidates,
      'sort_property': sort_property,
      'query': query
    }

    with HandleServerException():
      return BaseRequest.PostDataToHandler( request_data,
                                            'filter_and_sort_candidates' )
    return candidates

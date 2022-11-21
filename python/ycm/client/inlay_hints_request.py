# Copyright (C) 2022, YouCompleteMe Contributors
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


import logging
from ycm.client.base_request import ( BaseRequest, DisplayServerException,
                                      MakeServerException )

_logger = logging.getLogger( __name__ )


# FIXME: This is copy/pasta from SemanticTokensRequest - abstract a
# SimpleAsyncRequest base that does all of this generically
class InlayHintsRequest( BaseRequest ):
  def __init__( self, request_data ):
    super().__init__()
    self.request_data = request_data
    self._response_future = None


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'inlay_hints' )

  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Reset( self ):
    self._response_future = None

  def Response( self ):
    if not self._response_future:
      return []

    response = self.HandleFuture( self._response_future,
                                  truncate_message = True )

    if not response:
      return []

    # Vim may not be able to convert the 'errors' entry to its internal format
    # so we remove it from the response.
    errors = response.pop( 'errors', [] )
    for e in errors:
      exception = MakeServerException( e )
      _logger.error( exception )
      DisplayServerException( exception, truncate_message = True )

    return response.get( 'inlay_hints' ) or []

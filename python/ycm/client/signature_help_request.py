# Copyright (C) 2019 YouCompleteMe contributors
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


class SigHelpAvailableByFileType( dict ):
  def __missing__( self, filetype ):
    request = SignatureHelpAvailableRequest( filetype )
    self[ filetype ] = request
    return request


class SignatureHelpRequest( BaseRequest ):
  def __init__( self, request_data ):
    super( SignatureHelpRequest, self ).__init__()
    self.request_data = request_data
    self._response_future = None


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'signature_help' )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Reset( self ):
    self._response_future = None


  def Response( self ):
    if not self._response_future:
      return {}

    response = self.HandleFuture( self._response_future,
                                  truncate_message = True )
    if not response:
      return {}

    # Vim may not be able to convert the 'errors' entry to its internal format
    # so we remove it from the response.
    errors = response.pop( 'errors', [] )
    for e in errors:
      exception = MakeServerException( e )
      _logger.error( exception )
      DisplayServerException( exception, truncate_message = True )

    return response.get( 'signature_help' ) or {}


class SignatureHelpAvailableRequest( BaseRequest ):
  def __init__( self, filetype ):
    super( SignatureHelpAvailableRequest, self ).__init__()
    self._response_future = None
    self.Start( filetype )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def Response( self ):
    if not self._response_future:
      return None

    response = self.HandleFuture( self._response_future,
                                  truncate_message = True )

    if not response:
      return None

    return response[ 'available' ]


  def Start( self, filetype ):
    self._response_future = self.GetDataFromHandlerAsync(
      'signature_help_available',
      payload = { 'subserver': filetype } )

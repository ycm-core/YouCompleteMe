# Copyright (C) 2020 YouCompleteMe contributors
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

from ycm.client.base_request import ( BaseRequest,
                                      DisplayServerException,
                                      MakeServerException )
from ycm.client.completion_request import ( CompletionRequest,
                                            ConvertCompletionDataToVimData )

import logging
import json
_logger = logging.getLogger( __name__ )


class ResolveCompletionRequest( BaseRequest ):
  def __init__( self,
                completion_request: CompletionRequest,
                request_data ):
    super().__init__()
    self.request_data = request_data
    self.completion_request = completion_request

  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'resolve_completion' )

  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def OnCompleteDone( self ):
    # This is required to be compatible with the "CompletionRequest" API. We're
    # not really a CompletionRequest, but we are mutually exclusive with
    # completion requests, so we implement this API by delegating to the
    # original completion request, which contains all of the code for actually
    # handling things like automatic imports etc.
    self.completion_request.OnCompleteDone()


  def Response( self ):
    response = self.HandleFuture( self._response_future,
                                  truncate_message = True,
                                  display_message = True )

    if not response or not response[ 'completion' ]:
      return { 'completion': [] }

    # Vim may not be able to convert the 'errors' entry to its internal format
    # so we remove it from the response.
    errors = response.pop( 'errors', [] )
    for e in errors:
      exception = MakeServerException( e )
      _logger.error( exception )
      DisplayServerException( exception, truncate_message = True )

    response[ 'completion' ] = ConvertCompletionDataToVimData(
        response[ 'completion' ] )
    return response


def ResolveCompletionItem( completion_request, item ):
  if not completion_request.Done():
    return None
  try:
    completion_extra_data = json.loads( item[ 'user_data' ] )
  except KeyError:
    return None
  except ( TypeError, json.JSONDecodeError ):
    # Can happen with the omni completer
    return None

  request_data = completion_request.request_data
  try:
    # Note: We mutate the request_data inside the original completion request
    # and pass it into the new request object. this is just a big efficiency
    # saving. The request_data for a Done() request is almost certainly no
    # longer needed.
    request_data[ 'resolve' ] = completion_extra_data[ 'resolve' ]
  except KeyError:
    return None

  resolve_request = ResolveCompletionRequest( completion_request, request_data )
  resolve_request.Start()
  return resolve_request

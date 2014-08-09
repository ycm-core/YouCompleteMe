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

from ycm import vimsupport
from ycmd.utils import ToUtf8IfNeeded
from ycm.client.base_request import BaseRequest, JsonFromFuture

TIMEOUT_SECONDS = 0.5

class CompletionRequest( BaseRequest ):
  def __init__( self, request_data ):
    super( CompletionRequest, self ).__init__()
    self.request_data = request_data


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'completions',
                                                         TIMEOUT_SECONDS,
                                                         request = self )


  def Done( self ):
    return self._response_future.done()


  def Response( self ):
    if not self._response_future:
      return []
    try:
      return _ConvertCompletionResponseToVimDatas(
          JsonFromFuture( self._response_future ) )
    except Exception as e:
      vimsupport.PostVimMessage( str( e ) )
    return []


def _ConvertCompletionDataToVimData( completion_data ):
  # see :h complete-items for a description of the dictionary fields
  vim_data = {
    'word' : ToUtf8IfNeeded( completion_data[ 'insertion_text' ] ),
    'dup'  : 1,
  }

  if 'menu_text' in completion_data:
    vim_data[ 'abbr' ] = ToUtf8IfNeeded( completion_data[ 'menu_text' ] )
  if 'extra_menu_info' in completion_data:
    vim_data[ 'menu' ] = ToUtf8IfNeeded( completion_data[ 'extra_menu_info' ] )
  if 'kind' in completion_data:
    vim_data[ 'kind' ] = ToUtf8IfNeeded(
        completion_data[ 'kind' ] )[ 0 ].lower()
  if 'detailed_info' in completion_data:
    vim_data[ 'info' ] = ToUtf8IfNeeded( completion_data[ 'detailed_info' ] )

  return vim_data


def _ConvertCompletionResponseToVimDatas( response_data ):
  return [ _ConvertCompletionDataToVimData( x )
           for x in response_data[ 'completions' ] ]

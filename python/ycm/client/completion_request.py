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

from ycm import base
from ycm import vimsupport
from ycm.utils import ToUtf8IfNeeded
from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                      JsonFromFuture )

TIMEOUT_SECONDS = 0.5

class CompletionRequest( BaseRequest ):
  def __init__( self, extra_data = None ):
    super( CompletionRequest, self ).__init__()

    self._completion_start_column = base.CompletionStartColumn()

    # This field is also used by the omni_completion_request subclass
    self.request_data = BuildRequestData( self._completion_start_column )
    if extra_data:
      self.request_data.update( extra_data )


  def CompletionStartColumn( self ):
    return self._completion_start_column


  def Start( self, query ):
    self.request_data[ 'query' ] = query
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'completions',
                                                         TIMEOUT_SECONDS )


  def Done( self ):
    return self._response_future.done()


  def Response( self ):
    if not self._response_future:
      return []
    try:
      return [ _ConvertCompletionDataToVimData( x )
               for x in JsonFromFuture( self._response_future ) ]
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
    vim_data[ 'kind' ] = ToUtf8IfNeeded( completion_data[ 'kind' ] )
  if 'detailed_info' in completion_data:
    vim_data[ 'info' ] = ToUtf8IfNeeded( completion_data[ 'detailed_info' ] )

  return vim_data

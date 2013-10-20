#!/usr/bin/env python
#
# Copyright (C) 2013  Strahinja Val Markovic  <val@markovic.io>
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
from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                      JsonFromFuture )

TIMEOUT_SECONDS = 0.5

class CmdlineCompletionRequest( BaseRequest ):
  def __init__( self ):
    super( CmdlineCompletionRequest, self ).__init__()

    self._completion_start_column = base.CmdlineCompletionStartColumn()

    self.request_data = BuildRequestData( self._completion_start_column )
    self.request_data[ 'line_value' ] = vimsupport.CurrentCmdline()
    self.request_data[ 'column_num' ] = vimsupport.CurrentCmdlineColumn()


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
      return [ completion_data[ 'insertion_text' ]
               for completion_data in JsonFromFuture( self._response_future ) ]
    except Exception as e:
      vimsupport.PostVimMessage( str( e ) )
    return []


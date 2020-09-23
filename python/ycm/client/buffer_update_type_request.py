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

from ycm.client.base_request import BaseRequest


class BufferUpdateTypeByFileType( dict ):
  def __missing__( self, filetype ):
    request = BufferUpdateTypeRequest( filetype )
    self[ filetype ] = request
    return request


class BufferUpdateTypeRequest( BaseRequest ):
  def __init__( self, filetype ):
    super().__init__()
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

    return response[ 'update_type' ]


  def Start( self, filetype ):
    self._response_future = self.GetDataFromHandlerAsync(
      'buffer_update_type',
      payload = { 'subserver': filetype } )

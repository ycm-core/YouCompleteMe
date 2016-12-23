# Copyright (C) 2016 YouCompleteMe contributors
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

from ycm.client.base_request import ( BaseRequest, BuildRequestData,
                                      HandleServerException )


class DebugInfoRequest( BaseRequest ):
  def __init__( self ):
    super( DebugInfoRequest, self ).__init__()
    self._response = None


  def Start( self ):
    request_data = BuildRequestData()
    with HandleServerException( display = False ):
      self._response = self.PostDataToHandler( request_data, 'debug_info' )


  def Response( self ):
    if not self._response:
      return 'Server errored, no debug info from server'
    return self._response


def SendDebugInfoRequest():
  request = DebugInfoRequest()
  # This is a blocking call.
  request.Start()
  return request.Response()

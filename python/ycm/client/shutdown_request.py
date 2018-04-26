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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycm.client.base_request import BaseRequest

TIMEOUT_SECONDS = 0.1


class ShutdownRequest( BaseRequest ):
  def __init__( self ):
    super( ShutdownRequest, self ).__init__()


  def Start( self ):
    self.PostDataToHandler( {},
                            'shutdown',
                            TIMEOUT_SECONDS,
                            display_message = False )


def SendShutdownRequest():
  request = ShutdownRequest()
  # This is a blocking call.
  request.Start()

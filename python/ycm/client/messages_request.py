# Copyright (C) 2017 YouCompleteMe contributors
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

from ycm.client.base_request import BaseRequest, BuildRequestData
from ycm.vimsupport import PostVimMessage

import logging

_logger = logging.getLogger( __name__ )

# Looooong poll
TIMEOUT_SECONDS = 60


class MessagesPoll( BaseRequest ):
  def __init__( self ):
    super( MessagesPoll, self ).__init__()
    self._request_data = BuildRequestData()
    self._response_future = None


  def _SendRequest( self ):
    self._response_future = self.PostDataToHandlerAsync(
      self._request_data,
      'receive_messages',
      timeout = TIMEOUT_SECONDS )
    return


  def Poll( self, diagnostics_handler ):
    """This should be called regularly to check for new messages in this buffer.
    Returns True if Poll should be called again in a while. Returns False when
    the completer or server indicated that further polling should not be done
    for the requested file."""

    if self._response_future is None:
      # First poll
      self._SendRequest()
      return True

    if not self._response_future.done():
      # Nothing yet...
      return True

    response = self.HandleFuture( self._response_future,
                                  display_message = False )
    if response is None:
      # Server returned an exception.
      return False

    poll_again = _HandlePollResponse( response, diagnostics_handler )
    if poll_again:
      self._SendRequest()
      return True

    return False


def _HandlePollResponse( response, diagnostics_handler ):
  if isinstance( response, list ):
    for notification in response:
      if 'message' in notification:
        PostVimMessage( notification[ 'message' ],
                        warning = False,
                        truncate = True )
      elif 'diagnostics' in notification:
        diagnostics_handler.UpdateWithNewDiagnosticsForFile(
          notification[ 'filepath' ],
          notification[ 'diagnostics' ] )
  elif response is False:
    # Don't keep polling for this file
    return False
  # else any truthy response means "nothing to see here; poll again in a
  # while"

  # Start the next poll (only if the last poll didn't raise an exception)
  return True

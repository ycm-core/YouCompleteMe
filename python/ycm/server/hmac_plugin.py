#!/usr/bin/env python
#
# Copyright (C) 2014  Google Inc.
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
import httplib
from bottle import request, response, abort
from ycm import utils

_HMAC_HEADER = 'x-ycm-hmac'

# This class implements the Bottle plugin API:
# http://bottlepy.org/docs/dev/plugindev.html
#
# We want to ensure that every request coming in has a valid HMAC set in the
# x-ycm-hmac header and that every response coming out sets such a valid header.
# This is to prevent security issues with possible remote code execution.
class HmacPlugin( object ):
  name = 'hmac'
  api = 2


  def __init__( self, hmac_secret ):
    self._hmac_secret = hmac_secret
    self._logger = logging.getLogger( __name__ )


  def __call__( self, callback ):
    def wrapper( *args, **kwargs ):
      body = request.body.read()
      if not RequestAuthenticated( body, self._hmac_secret ):
        self._logger.info( 'Dropping request with bad HMAC.' )
        abort( httplib.UNAUTHORIZED, 'Unauthorized, received bad HMAC.')
        return
      body = callback( *args, **kwargs )
      SetHmacHeader( body, self._hmac_secret )
      return body
    return wrapper


def RequestAuthenticated( body, hmac_secret ):
  return utils.ContentHexHmacValid( body,
                                    request.headers[ _HMAC_HEADER ],
                                    hmac_secret )

def SetHmacHeader( body, hmac_secret ):
  response.headers[ _HMAC_HEADER ] = utils.CreateHexHmac( body, hmac_secret )

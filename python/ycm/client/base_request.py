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

import vim
import json
import requests
from ycm import vimsupport

HEADERS = {'content-type': 'application/json'}

class ServerError( Exception ):
  def __init__( self, message ):
    super( ServerError, self ).__init__( message )


class BaseRequest( object ):
  def __init__( self ):
    pass


  def Start( self ):
    pass


  def Done( self ):
    return True


  def Response( self ):
    return {}


  @staticmethod
  def PostDataToHandler( data, handler ):
    response = requests.post( _BuildUri( handler ),
                              data = json.dumps( data ),
                              headers = HEADERS )
    if response.status_code == requests.codes.server_error:
      raise ServerError( response.json()[ 'message' ] )

    # We let Requests handle the other status types, we only handle the 500
    # error code.
    response.raise_for_status()

    if response.text:
      return response.json()
    return None

  server_location = 'http://localhost:6666'


def BuildRequestData( start_column = None, query = None ):
  line, column = vimsupport.CurrentLineAndColumn()
  request_data = {
    'filetypes': vimsupport.CurrentFiletypes(),
    'line_num': line,
    'column_num': column,
    'start_column': start_column,
    'line_value': vim.current.line,
    'filepath': vim.current.buffer.name,
    'file_data': vimsupport.GetUnsavedAndCurrentBufferData()
  }

  if query:
    request_data[ 'query' ] = query

  return request_data


def _BuildUri( handler ):
  return ''.join( [ BaseRequest.server_location, '/', handler ] )



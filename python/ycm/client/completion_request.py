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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from ycmd.utils import ToUnicode
from ycm.client.base_request import ( BaseRequest, JsonFromFuture,
                                      HandleServerException,
                                      MakeServerException )

TIMEOUT_SECONDS = 0.5


class CompletionRequest( BaseRequest ):
  def __init__( self, request_data ):
    super( CompletionRequest, self ).__init__()
    self.request_data = request_data
    self._response_future = None


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'completions',
                                                         TIMEOUT_SECONDS )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def RawResponse( self ):
    if not self._response_future:
      return []
    with HandleServerException( truncate = True ):
      response = JsonFromFuture( self._response_future )

      errors = response[ 'errors' ] if 'errors' in response else []
      for e in errors:
        with HandleServerException( truncate = True ):
          raise MakeServerException( e )

      return response[ 'completions' ]
    return []


  def Response( self ):
    return _ConvertCompletionDatasToVimDatas( self.RawResponse() )


def ConvertCompletionDataToVimData( completion_data ):
  # see :h complete-items for a description of the dictionary fields
  vim_data = {
    'word'  : '',
    'dup'   : 1,
    'empty' : 1,
  }

  if ( 'extra_data' in completion_data and
       'doc_string' in completion_data[ 'extra_data' ] ):
    doc_string = completion_data[ 'extra_data' ][ 'doc_string' ]
  else:
    doc_string = ""

  if 'insertion_text' in completion_data:
    vim_data[ 'word' ] = completion_data[ 'insertion_text' ]
  if 'menu_text' in completion_data:
    vim_data[ 'abbr' ] = completion_data[ 'menu_text' ]
  if 'extra_menu_info' in completion_data:
    vim_data[ 'menu' ] = completion_data[ 'extra_menu_info' ]
  if 'kind' in completion_data:
    kind = ToUnicode( completion_data[ 'kind' ] )
    if kind:
      vim_data[ 'kind' ] = kind[ 0 ].lower()
  if 'detailed_info' in completion_data:
    vim_data[ 'info' ] = completion_data[ 'detailed_info' ]
    if doc_string:
      vim_data[ 'info' ] += '\n' + doc_string
  elif doc_string:
    vim_data[ 'info' ] = doc_string

  return vim_data


def _ConvertCompletionDatasToVimDatas( response_data ):
  return [ ConvertCompletionDataToVimData( x )
           for x in response_data ]

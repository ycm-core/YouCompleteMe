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

from ycm.client.completion_request import CompletionRequest


class OmniCompletionRequest( CompletionRequest ):
  def __init__( self, omni_completer, request_data ):
    super( OmniCompletionRequest, self ).__init__( request_data )
    self._omni_completer = omni_completer


  def Start( self ):
    self._results = self._omni_completer.ComputeCandidates( self.request_data )


  def Done( self ):
    return True


  def RawResponse( self ):
    return _ConvertVimDatasToCompletionDatas( self._results )


  def Response( self ):
    return self._results


def ConvertVimDataToCompletionData( vim_data ):
  # see :h complete-items for a description of the dictionary fields
  completion_data = {}

  if 'word' in vim_data:
    completion_data[ 'insertion_text' ] = vim_data[ 'word' ]
  if 'abbr' in vim_data:
    completion_data[ 'menu_text' ] = vim_data[ 'abbr' ]
  if 'menu' in vim_data:
    completion_data[ 'extra_menu_info' ] = vim_data[ 'menu' ]
  if 'kind' in vim_data:
    completion_data[ 'kind' ] = [ vim_data[ 'kind' ] ]
  if 'info' in vim_data:
    completion_data[ 'detailed_info' ] = vim_data[ 'info' ]

  return completion_data


def _ConvertVimDatasToCompletionDatas( response_data ):
  return [ ConvertVimDataToCompletionData( x )
           for x in response_data ]

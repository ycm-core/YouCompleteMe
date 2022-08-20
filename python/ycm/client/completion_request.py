# Copyright (C) 2013-2019 YouCompleteMe contributors
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

import json
import logging
from ycmd.utils import ToUnicode
from ycm.client.base_request import ( BaseRequest,
                                      DisplayServerException,
                                      MakeServerException )
from ycm import vimsupport, base
from ycm.vimsupport import NO_COMPLETIONS

_logger = logging.getLogger( __name__ )


class CompletionRequest( BaseRequest ):
  def __init__( self, request_data ):
    super().__init__()
    self.request_data = request_data
    self._response_future = None


  def Start( self ):
    self._response_future = self.PostDataToHandlerAsync( self.request_data,
                                                         'completions' )


  def Done( self ):
    return bool( self._response_future ) and self._response_future.done()


  def _RawResponse( self ):
    if not self._response_future:
      return NO_COMPLETIONS

    response = self.HandleFuture( self._response_future,
                                  truncate_message = True )
    if not response:
      return NO_COMPLETIONS

    # Vim may not be able to convert the 'errors' entry to its internal format
    # so we remove it from the response.
    errors = response.pop( 'errors', [] )
    for e in errors:
      exception = MakeServerException( e )
      _logger.error( exception )
      DisplayServerException( exception, truncate_message = True )

    response[ 'line' ] = self.request_data[ 'line_num' ]
    response[ 'column' ] = self.request_data[ 'column_num' ]
    return response


  def Response( self ):
    response = self._RawResponse()
    response[ 'completions' ] = _ConvertCompletionDatasToVimDatas(
        response[ 'completions' ] )
    # FIXME: Do we really need to do this AdjustCandidateInsertionText ? I feel
    # like Vim should do that for us
    response[ 'completions' ] = base.AdjustCandidateInsertionText(
        response[ 'completions' ] )
    return response


  def OnCompleteDone( self ):
    if not self.Done():
      return

    if 'cs' in vimsupport.CurrentFiletypes():
      self._OnCompleteDone_Csharp()
    else:
      extra_data = self._GetCompletionExtraData()
      if not extra_data:
        return

      self._OnCompleteDone_FixIt( extra_data )

      snippet = extra_data.get( 'snippet' )
      if snippet:
        self._OnCompleteDone_Snippet( snippet )


  def _GetCompletionExtraData( self ):
    completed_item = vimsupport.GetVariableValue( 'v:completed_item' )

    if not completed_item:
      return None

    if 'user_data' not in completed_item:
      return None

    return json.loads( completed_item[ 'user_data' ] )


  def _OnCompleteDone_Csharp( self ):
    extra_data = self._GetCompletionExtraData()
    namespace = extra_data.get( 'required_namespace_import' )
    if not namespace:
      return
    vimsupport.InsertNamespace( namespace )


  def _OnCompleteDone_FixIt( self, completion_extra_data ):
    fixits = completion_extra_data.get( 'fixits', [] )

    for fixit in fixits:
      cursor_position = 'end' if fixit.get( 'is_completion', False ) else None
      vimsupport.ReplaceChunks( fixit[ 'chunks' ],
                                silent = True,
                                cursor_position = cursor_position )


  def _OnCompleteDone_Snippet( self, snippet ):
    vimsupport.ExpandSnippet( snippet[ 'snippet' ],
                              snippet[ 'trigger_string' ] )


def _GetCompletionInfoField( completion_data ):
  info = completion_data.get( 'detailed_info', '' )

  if 'extra_data' in completion_data:
    docstring = completion_data[ 'extra_data' ].get( 'doc_string', '' )
    if docstring:
      if info:
        info += '\n' + docstring
      else:
        info = docstring

  # This field may contain null characters e.g. \x00 in Python docstrings. Vim
  # cannot evaluate such characters so they are removed.
  return info.replace( '\x00', '' )


def ConvertCompletionDataToVimData( completion_data ):
  # See :h complete-items for a description of the dictionary fields.
  extra_menu_info = completion_data.get( 'extra_menu_info', '' )
  preview_info = _GetCompletionInfoField( completion_data )

  # When we are using a popup for the preview_info, it needs to fit on the
  # screen alongside the extra_menu_info. Let's use some heuristics.  If the
  # length of the extra_menu_info is more than, say, 1/3 of screen, truncate it
  # and stick it in the preview_info.
  if vimsupport.UsingPreviewPopup():
    max_width = max( int( vimsupport.DisplayWidth() / 3 ), 3 )
    extra_menu_info_width = vimsupport.DisplayWidthOfString( extra_menu_info )
    if extra_menu_info_width > max_width:
      if not preview_info.startswith( extra_menu_info ):
        preview_info = extra_menu_info + '\n\n' + preview_info
      extra_menu_info = extra_menu_info[ : ( max_width - 3 ) ] + '...'

  pfx = ''
  extra_data = completion_data.get( 'extra_data', {} )

  if 'snippet' in extra_data:
    pfx += '*'
  if 'fixits' in extra_data:
    pfx += '+'

  if 'menu_text' in completion_data:
    abbr = pfx + completion_data[ 'menu_text' ]
  elif pfx:
    abbr = pfx + completion_data[ 'insertion_text' ]
  else:
    abbr = ''

  return {
    'word'     : completion_data[ 'insertion_text' ],
    'abbr'     : abbr,
    'menu'     : extra_menu_info,
    'info'     : preview_info,
    'kind'     : ToUnicode( completion_data.get( 'kind', '' ) )[ :1 ].lower(),
    # Disable Vim filtering.
    'equal'    : 1,
    'dup'      : 1,
    'empty'    : 1,
    # We store the completion item extra_data as a string in the completion
    # user_data. This allows us to identify the _exact_ item that was completed
    # in the CompleteDone handler, by inspecting this item from v:completed_item
    #
    # We convert to string because completion user data items must be strings.
    # Note: Since 8.2.0084 we don't need to use json.dumps() here.
    'user_data': json.dumps( extra_data )
  }


def _ConvertCompletionDatasToVimDatas( response_data ):
  return [ ConvertCompletionDataToVimData( x ) for x in response_data ]
